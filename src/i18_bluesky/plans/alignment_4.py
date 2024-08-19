import bluesky.plan_stubs as bps
from bluesky.devices.monochromator import DCM as Monochromator
from dodal.common import MsgGenerator, inject
from dodal.devices.undulator import Undulator

UNDULATOR = inject("undulator")
DCM = inject("monochromator")


def align_idgap(
    harmonic: int = 1,
    undulator: Undulator = UNDULATOR,
    monochromator: Monochromator = DCM,
) -> MsgGenerator:
    """
    Bragg angle motor

    """

    gap = yield from bps.rd(undulator.current_gap)
    monochromator.bragg_in_degrees
