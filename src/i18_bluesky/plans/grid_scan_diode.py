import bluesky.plans as bp
from dodal.common import MsgGenerator, inject
from dodal.devices.i18.diode import Diode
from dodal.devices.i18.table import Table
from dodal.plans.data_session_metadata import attach_data_session_metadata_decorator

DIODE = inject("diode")

TABLE = inject("table")


# todo make it use scanspec instead


@attach_data_session_metadata_decorator()
def grid_scan_diode(
    x_start: float,
    x_stop: float,
    x_steps: int,
    y_start: float,
    y_stop: float,
    y_steps: int,
    diode: Diode = DIODE,
    table: Table = TABLE,
) -> MsgGenerator:
    yield from bp.grid_scan(
        [diode], table.x, x_start, x_stop, x_steps, table.y, y_start, y_stop, y_steps
    )
