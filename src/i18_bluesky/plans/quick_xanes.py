from typing import List
from ophyd_async.core import Device, Component as Cpt
from ophyd_async.epics.signal import epics_signal_rw
from dodal.devices.dcm import DCM
from dodal.devices.xspress3 import Xspress3
from dodal.devices.panda import HDFPanda
from dodal.utils import device_instantiation, CrystalMetadata
from typing import List, Dict, Any, Optional
from bluesky.preprocessors import baseline_decorator, stage_decorator, run_decorator
import bluesky.plan_stubs as bps
from bluesky import RunEngine
import numpy as np
from dls_bluesky_core.core import MsgGenerator, inject
from ophyd_async.core import HardwareTriggeredFlyable, StandardDetector
from ophyd_async.panda import StaticSeqTableTriggerLogic

import bluesky.plan_stubs as bps
import numpy as np
from bluesky import RunEngine
from bluesky.preprocessors import inject
from dls_bluesky_core.core import MsgGenerator
from dodal.devices.dcm import DCM
from dodal.devices.xspress3 import Xspress3
from dodal.utils import CrystalMetadata, device_instantiation

from i18_bluesky.plans.align2 import BEAMLINE_PREFIX


def dcm(wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False) -> DCM:
    return device_instantiation(
        DCM,
        "dcm",
        "",
        wait_for_connection,
        fake_with_ophyd_sim,
        bl_prefix=False,
        motion_prefix=f"{BEAMLINE_PREFIX}-MO-DCM-01:",
        temperature_prefix=f"{BEAMLINE_PREFIX}-DI-DCM-01:",
        crystal_1_metadata=CrystalMetadata(
            usage="Bragg",
            type="silicon",
            reflection=(1, 1, 1),
            d_spacing=(3.13475, "nm"),
        ),
        crystal_2_metadata=CrystalMetadata(
            usage="Bragg",
            type="silicon",
            reflection=(1, 1, 1),
            d_spacing=(3.13475, "nm"),
        ),
    )


monochromator = dcm()


def xspress3_device(prefix: str) -> Xspress3:
    return Xspress3(name="x", prefix=f"{prefix}-EA-XSP-02:")


i0 = xspress3_device(BEAMLINE_PREFIX)
IT = xspress3_device(BEAMLINE_PREFIX)
fluorescence = xspress3_device(BEAMLINE_PREFIX)

# todo panda MO or EA?
panda = HDFPanda(name="panda", prefix=f"{BEAMLINE_PREFIX}-PANDA-01:")


@inject
def quick_qfas_xanes_no_panda(
    angles: List[float], gaps: List[float], count_time: float
) -> MsgGenerator:
    # Ensure the angles and gaps lists are the same length
    assert len(angles) == len(gaps), "Angles and gaps lists must be the same length"

    for angle, gap in zip(angles, gaps):
        # Move the Bragg angle and IDGAP together
        yield from bps.mv(monochromator.angle, angle, monochromator.gap, gap)

        # Set the count time for the detectors
        yield from bps.mv(i0.count_time, count_time)
        yield from bps.mv(IT.count_time, count_time)
        yield from bps.mv(fluorescence.count_time, count_time)

        # Trigger and read data from the detectors
        yield from bps.trigger_and_read([i0, IT, fluorescence])
        i0_data = yield from bps.rd(i0.data)
        IT_data = yield from bps.rd(IT.data)
        fluorescence_data = yield from bps.rd(fluorescence.data)

        print(
            f"Angle: {angle}, Gap: {gap}, i0: {i0_data}, IT: {IT_data}, Fluorescence: {fluorescence_data}"
        )


# Instantiate the RunEngine
RE = RunEngine({})

# Define the list of angles and corresponding gaps for the scan
angles_list = np.linspace(10, 15, num=10).tolist()  # Example angles
gaps_list = np.linspace(5, 10, num=10).tolist()  # Example gaps
scan_count_time = 1.0  # 1 second count time for each scan

# Run the quick QFAS XANES scan
RE(quick_qfas_xanes_no_panda(angles_list, gaps_list, scan_count_time))


@inject
def quick_qfas_xanes(
    angles: List[float],
    gaps: List[float],
    exposure: float,
    panda: HDFPanda = inject(panda),
    detectors: List[StandardDetector] = [i0, IT, fluorescence],
    baseline: List[Device] = [monochromator, panda],
    metadata: Optional[Dict[str, Any]] = None,
) -> MsgGenerator:
    assert len(angles) == len(gaps), "Angles and gaps lists must be the same length"

    stream_name = "main"
    flyer = HardwareTriggeredFlyable(StaticSeqTableTriggerLogic(panda.seq[1]))
    devices = [flyer] + detectors + [panda] + baseline

    # Collect metadata
    plan_args = {
        "angles": angles,
        "gaps": gaps,
        "exposure": exposure,
        "panda": repr(panda),
        "detectors": [repr(device) for device in detectors],
        "baseline": [repr(device) for device in baseline],
    }

    _md = {
        "detectors": [device.name for device in detectors],
        "plan_args": plan_args,
        "hints": {},
    }
    _md.update(metadata or {})

    @baseline_decorator(baseline)
    @stage_decorator(devices)
    @run_decorator(md=_md)
    def inner_plan():
        yield from prepare_seq_table_flyer_and_det(
            flyer=flyer,
            detectors=detectors,
            angles=angles,
            gaps=gaps,
            exposure=exposure,
        )
        yield from fly_and_collect(
            stream_name=stream_name,
            detectors=detectors,
            flyer=flyer,
        )

    yield from inner_plan()


def prepare_seq_table_flyer_and_det(
    flyer: HardwareTriggeredFlyable,
    detectors: List[StandardDetector],
    angles: List[float],
    gaps: List[float],
    exposure: float,
) -> MsgGenerator:
    table_info = create_xanes_seq_table(angles, gaps, exposure)
    for det in detectors:
        yield from bps.prepare(det, table_info, wait=False, group="prep")
    yield from bps.prepare(flyer, table_info, wait=False, group="prep")
    yield from bps.wait(group="prep")


def create_xanes_seq_table(
    angles: List[float],
    gaps: List[float],
    exposure: float,
) -> StaticSeqTableTriggerLogic:
    rows = [
        {
            "bragg": angle,
            "idgap": gap,
            "exposure": exposure,
            "detectors": {"i0": True, "IT": True, "fluorescence": True},
        }
        for angle, gap in zip(angles, gaps)
    ]

    seq_table = StaticSeqTableTriggerLogic(rows)
    return seq_table


def fly_and_collect(
    stream_name: str,
    detectors: List[StandardDetector],
    flyer: HardwareTriggeredFlyable,
) -> MsgGenerator:
    yield from bps.fly(flyer)
    yield from bps.collect(detectors, stream_name)
