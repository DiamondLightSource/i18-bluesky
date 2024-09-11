import bluesky.plan_stubs as bps
import bluesky.plans as bp
import bluesky.preprocessors as bpp
from dodal.common import MsgGenerator, inject
from dodal.devices.i18.diode import Diode
from dodal.devices.i18.table import Table

DIODE = inject("diode")

TABLE = inject("table")


# todo make it use scanspec instead
def grid_scan_diode(
    start_x: float,
    steps_x: int,
    start_y: float,
    steps_y: int,
    diode: Diode = DIODE,
    table: Table = TABLE,
) -> MsgGenerator:
    """
    Scan wrapping `bp.grid_scan`

    Args:
        detectors: List of readable devices, will take a reading at each point
        motor1: name of motor to be moved
        scan_args1: [start, stop, step]
        motor2: name of motor to be moved
        scan_args2: [start, stop, step]
        metadata
        snake_axes: if True, the second axis will reverse direction
    """
    detectors = [diode]

    plan_args = {
        "diode": repr(diode),
        "steps_x": 5,
        "steps_y": 5,
        "start_x": 0,
        "start_y": 0,
    }

    _md_ = {
        "detectors": list(map(repr, detectors)),
        "plan_name": "grid_scan",
        "plan_args": plan_args,
        "shape": [steps_x, steps_y],
    }

    @bpp.stage_decorator(detectors)
    @bpp.run_decorator(md=_md_)
    def inner_grid_scan_plan():
        # todo move to the starting position
        yield from bps.mv(table, start_x, start_y)
        # todo make sure this is right
        yield from bp.grid_scan(detectors, md=_md_)
        # todo consider commented out variant
        # todo consider linspace and numpy instead
        yield from bps.read(detectors)
        # for x in range(steps_x):
        #     for y in range(steps_y):
        #         yield from bps.mv(table, start_x + x, start_y + y)
        #         yield from bps.trigger_and_read(detectors)

    yield from inner_grid_scan_plan()
