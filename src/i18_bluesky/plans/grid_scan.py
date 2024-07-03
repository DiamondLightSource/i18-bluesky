from typing import Any, Dict, Optional

import bluesky.plan_stubs as bps
from bluesky import RunEngine
from dls_bluesky_core.core import MsgGenerator, inject
from dodal.devices.excalibur import Excalibur
from ophyd_async.core import Component as Cpt
from ophyd_async.core import Device
from ophyd_async.epics.signal import epics_signal_rw


class StageMotor(Device):
    position = Cpt(epics_signal_rw, "position")


# Instantiate the stage motors
h_stage_motor = StageMotor("h_stage_motor_prefix", name="h_stage_motor")
v_stage_motor = StageMotor("v_stage_motor_prefix", name="v_stage_motor")

# Instantiate the Excalibur detector
excalibur = Excalibur(name="excalibur", prefix=f"{BEAMLINE_PREFIX}-EA-EXC-01:")


@inject
def grid_scan(
    h_start: float,
    h_stop: float,
    v_start: float,
    v_stop: float,
    step_size: float,
    time_per_pixel: float,
    h_stage_motor: StageMotor = inject(h_stage_motor),
    v_stage_motor: StageMotor = inject(v_stage_motor),
    detector: Excalibur = inject(excalibur),
    metadata: Optional[Dict[str, Any]] = None,
) -> MsgGenerator:
    h_positions = np.arange(h_start, h_stop, step_size)
    v_positions = np.arange(v_start, v_stop, step_size)

    _md = {
        "detectors": [detector.name],
        "plan_args": {
            "h_start": h_start,
            "h_stop": h_stop,
            "v_start": v_start,
            "v_stop": v_stop,
            "step_size": step_size,
            "time_per_pixel": time_per_pixel,
        },
        "hints": {},
    }
    _md.update(metadata or {})

    @run_decorator(md=_md)
    def inner_plan():
        for v_pos in v_positions:
            yield from bps.mv(v_stage_motor.position, v_pos)
            for h_pos in h_positions:
                yield from bps.mv(h_stage_motor.position, h_pos)
                yield from bps.mv(detector.exposure_time, time_per_pixel)
                yield from bps.trigger_and_read([detector])
                yield from bps.sleep(time_per_pixel)  # Ensure proper timing

    yield from inner_plan()


# Instantiate the RunEngine
RE = RunEngine({})

# Define the scan parameters
h_start = 0.0
h_stop = 10.0
v_start = 0.0
v_stop = 10.0
step_size = 1.0
time_per_pixel = 0.1  # 0.1 seconds per pixel

# Run the grid scan
RE(grid_scan(h_start, h_stop, v_start, v_stop, step_size, time_per_pixel))
