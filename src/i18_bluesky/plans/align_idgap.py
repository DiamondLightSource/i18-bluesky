import asyncio
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import bluesky.plan_stubs as bps
import mendeleev as pt
import numpy as np
from bluesky.devices.monochromator import DCM as Monochromator
from dodal.common import MsgGenerator, inject
from dodal.devices.undulator import Undulator
from scipy import curve_fit

UNDULATOR = inject("undulator")
DCM = inject("monochromator")

harmonics = [1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23]
# https://www.cyberphysics.co.uk/topics/light/A_level/difraction.htm


@dataclass
class IdGapAlignmentStatus:
    target_energy: Optional[float] = 12.0
    tolerance: Optional[float] = 0.1


def align_idgap(
    harmonic: int = 1,
    undulator: Undulator = UNDULATOR,
    monochromator: Monochromator = DCM,
) -> MsgGenerator:
    """
    Bragg angle motor

    """

    gap = yield from bps.rd(undulator.current_gap)

    # second the idgap lookup tables -
    # for 10-15 points inside the energy range for this element
    # we scan the gap fo the insertion devise, looking for the maximum
    # then quadratic interpolation
    # written into the file, then GDA probably some interpolation
    # TFG calculates frequency from current via voltage
    # so we need to load the panda configuration
    energy_range = np.linspace(10, 15, num=10)
    gap_positions = yield from bps.rd(Undulator.gap_positions)
    quadratic_fit: np.ndarray[float] = np.polyfit(energy_range, gap_positions, 2)
    np.save("gap_lookup_table.npy", quadratic_fit)


# Define a Gaussian function for fitting
def gaussian(x, amp, mean, sigma):
    return amp * np.exp(-((x - mean) ** 2) / (2 * sigma**2))


@dataclass
class IdGapMeasurement:
    bragg: float
    gap: float


@dataclass
class IdGapLookupRecord:
    element: str
    edge: str
    date: datetime
    detector: str
    comment: str
    harmonic: int
    measurements: List[IdGapMeasurement] = field(default_factory=list)

    def to_json(self):
        return json.dumps(asdict(self), default=str, indent=4)

    @classmethod
    def from_json(cls, data: str):
        data_dict = json.loads(data)
        data_dict["date"] = datetime.fromisoformat(data_dict["date"])
        data_dict["harmonic"] = int(data_dict["harmonic"])
        measurements = [IdGapMeasurement(**m) for m in data_dict["measurements"]]
        return cls(**data_dict, measurements=measurements)

    def quadratic_regression(self):
        x = np.array([m.bragg for m in self.measurements])
        y = np.array([m.gap for m in self.measurements])

        def quadratic(x, a, b, c):
            return a * x**2 + b * x + c

        params, _ = curve_fit(quadratic, x, y)
        return params

    def get_regression_function(self):
        params = self.quadratic_regression()

        def regression_function(x):
            a, b, c = params
            return a * x**2 + b * x + c

        return regression_function


async def scan(undulator, diode, lookup_table) -> MsgGenerator:
    """
    the goal here is to make a serializable structure
    for those and some functions, alogn with algorithms
    this would be agnostic wrt the saving mechanism, be it redis or etcd, etc
    """
    min_val = undulator.min
    max_val = undulator.max
    bragg_values = []
    gap_values = []

    for i in range(10):
        # todo not sure about the offsets
        bragg = min_val + i * (max_val - min_val) / 10
        await undulator.set_bragg(bragg)  # Assume set_bragg is an async function
        gap = await diode.read()  # Assume read is an async function
        bragg_values.append(bragg)
        gap_values.append(gap)

    bragg_array = np.array(bragg_values)
    gap_array = np.array(gap_values)

    try:
        popt, _ = curve_fit(
            gaussian,
            bragg_array,
            gap_array,
            p0=[max(gap_array), bragg_array[np.argmax(gap_array)], 1],
        )
        peak_bragg = popt[1]
    except Exception as e:
        print(f"Gaussian fitting failed: {e}")
        peak_bragg = bragg_array[np.argmax(gap_array)]

    record = IdGapLookupRecord(
        element=undulator.element,
        edge=undulator.edge,
        date=datetime.now(),
        detector="Diode",
        comment="Measurement at peak diode value",
        harmonic=undulator.harmonic,
        measurements=[IdGapMeasurement(peak_bragg, max(gap_array))],
    )

    lookup_table.save(record)


async def main_alignment_idgap_plan(undulator, diode, lookup_table) -> MsgGenerator:
    tasks = []
    for h in harmonics:
        undulator.harmonic = h
        undulator.element = "Si"  # Example, set this appropriately
        undulator.edge = "K"  # Example, set this appropriately

        tasks.append(asyncio.create_task(scan(undulator, diode)))

    records = await asyncio.gather(*tasks)
    lookup_table.save(records)
