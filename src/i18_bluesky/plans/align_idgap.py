import asyncio
import json
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Optional

import bluesky.plan_stubs as bps
import numpy as np
from bluesky.devices.monochromator import DCM as Monochromator
from dodal.common import MsgGenerator, inject
from dodal.devices.undulator import Undulator
from scipy import curve_fit

UNDULATOR = inject("undulator")
DCM = inject("monochromator")
DIODE = inject("diode")


@dataclass
class IdGapLookupRecord:
    element: str
    edge: str
    date: datetime
    detector: str
    comment: str
    harmonic: int
    measurements: np.ndarray = np.array([])

    def to_json(self):
        return json.dumps(asdict(self), default=str, indent=4)

    @classmethod
    def from_json(cls, data: str):
        data_dict = json.loads(data)
        data_dict["date"] = datetime.fromisoformat(data_dict["date"])
        data_dict["harmonic"] = int(data_dict["harmonic"])
        # todo fix unpacking a numpy array
        measurements = data_dict["measurements"]
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


# todo need to hardcode the relationship between element and harmonic

element_harmonics_edges = {
    "Mo": {
        "harmonics": [19],
        "edges": ["K", "L1", "L2", "L3"],
        "starting_energy_eV": 17,
        "ending_energy_inverse_angstorm": 25,
    },
    # Ga values are guesswork at the moment
    "Ga": {"harmonics": [13], "edges": ["K"]},
}


@dataclass
class IdGapAlignmentStatus:
    target_energy: Optional[float] = 12.0
    tolerance: Optional[float] = 0.1


# Define a Gaussian function for fitting
def gaussian(x, amp, mean, sigma):
    return amp * np.exp(-((x - mean) ** 2) / (2 * sigma**2))


def align_idgap(
    element: str = "Ga",
    edge: str = "K",
    harmonic: int | None = None,
    undulator: Undulator = UNDULATOR,
    monochromator: Monochromator = DCM,
    diode=DIODE,
) -> MsgGenerator:
    assert element in element_harmonics_edges, "element not supported"
    if harmonic is not None:
        harmonic = element_harmonics_edges[element]["harmonics"][0]
    else:
        assert (
            harmonic in element_harmonics_edges[element]["harmonics"]
        ), "element is ok, harmonic not supported"
    assert edge in element_harmonics_edges[element]["edges"], "edge not supported"

    # todo saving for reference
    initial_gap = yield from bps.rd(undulator.current_gap)

    min_val = undulator.min
    max_val = undulator.max
    bragg_values = []
    gap_values = []
    intensity_values = []

    # todo start looking around the previous value
    for i in range(10):
        # todo not sure about the offsets
        bragg = min_val + i * (max_val - min_val) / 10
        yield from monochromator.set_bragg(
            bragg
        )  # Assume set_bragg is an async function
        gap = yield from bps.rd(undulator.current_gap)
        intensity = yield from bps.read(diode)  # Assume read is an async function
        bragg_values.append(bragg)
        gap_values.append(gap)
        intensity_values.append(intensity)

    bragg_array = np.array(bragg_values)
    gap_array = np.array(gap_values)
    intensity_array = np.array(intensity_values)

    # todo correlate to the Monochromator crystal metadata
    record = IdGapLookupRecord(
        element=undulator.element,
        edge=undulator.edge,
        date=datetime.now(),
        detector="Diode",
        comment="Measurement at peak diode value",
        harmonic=undulator.harmonic,
        measurements=[bragg_array, gap_array, intensity_array],
    )

    # todo not sure maybe save into the monochromator instead
    undulator.save(record)


# harmonics partial explanation https://www.cyberphysics.co.uk/topics/light/A_level/difraction.htm


async def align_gaps_for_all_elements_at_run_start(
    undulator: Undulator = UNDULATOR, diode=DIODE
) -> MsgGenerator:
    tasks = []
    for element in element_harmonics_edges:
        for edge in element_harmonics_edges[element]["edges"]:
            for harmonic in element_harmonics_edges[element]["harmonics"]:
                tasks.append(
                    asyncio.create_task(
                        align_idgap(element, edge, harmonic, undulator, diode)
                    )
                )

    records = await asyncio.gather(*tasks)
    undulator.save(records)


def prep_beamline_for_alignment(diode=DIODE):
    # todo no idea what is the correct method
    yield from bps.mv(diode.filter_b.mode, "in line diode")
    diode_saturation = yield from bps.read(diode.current)
    MIN = 2
    BEST = 18
    MAX = 20
    # todo change filter a size until it's near best
    # todo need the diode device with a sensible list of apertures
    yield from bps.mv(diode.filter_a.size, 5)
