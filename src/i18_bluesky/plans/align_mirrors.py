import bluesky.plan_stubs as bps
import numpy as np
from dodal.common import MsgGenerator, inject

UNDULATOR = inject("undulator")
DCM = inject("monochromator")


def focus_kb_mirror_until_tolerance(mirror, pinhole, tolerance: float) -> MsgGenerator:
    # Set initial positions for the KB mirrors
    yield from bps.mv(mirror.horizontal_bend1, "start_position")
    yield from bps.mv(mirror.horizontal_bend2, "start_position")
    yield from bps.mv(mirror.vertical_bend1, "start_position")
    yield from bps.mv(mirror.vertical_bend2, "start_position")

    # Adjust horizontal bends first
    for i in range(10):
        yield from bps.mv(mirror.horizontal_bend1, f"horizontal_step_{i}")
        yield from bps.mv(mirror.horizontal_bend2, f"horizontal_step_{i}")

        t1x = yield from bps.rd(mirror.t1x)
        t1y = yield from bps.rd(mirror.t1y)
        t1theta = yield from bps.rd(mirror.theta)
        assert t1x is int and t1y is int and t1theta is int
        yield from bps.trigger_and_read([t1x, t1y, t1theta])
        absorption_profile = yield from bps.rd(t1x, "absorption_profile")

        beam_size = np.std(absorption_profile)
        if beam_size < tolerance:
            break

    # Adjust vertical bends next
    for i in range(10):
        yield from bps.mv(mirror.vertical_bend1, f"vertical_step_{i}")
        yield from bps.mv(mirror.vertical_bend2, f"vertical_step_{i}")

        yield from bps.trigger_and_read([t1x, t1y, t1theta])
        absorption_profile = yield from bps.rd(t1x.absorption_profile)

        beam_size = np.std(absorption_profile)
        if beam_size < tolerance:
            break

    # Move mirrors and pinhole to final positions
    yield from bps.mv(mirror.horizontal_bend1, "final_position")
    yield from bps.mv(mirror.horizontal_bend2, "final_position")
    yield from bps.mv(mirror.vertical_bend1, "final_position")
    yield from bps.mv(mirror.vertical_bend2, "final_position")
    yield from bps.mv(pinhole, "final_position")
