from dodal.common import MsgGenerator, inject


PINHOLE = inject("pinhole")


# align the pinhole to reduce the scatter
# - 400 micron or 200 micron, then centralize it
# usuallly not seen immediately
# FocusingMirror misses curvature
# preparation for the wire stage - check if we have any
# gold wires on the sample stage - scanned in one direction
# first horizonal, vertical
# then record with IT the absorption profile, derviative and fitting
# then changing the bend
# could be 10 iterations, in either direction
# to minimuze the beam size until it changes
# to see the beam shape and the size
# takes usually 30 minutes to go through focusing manually, 2-3 hours
async def align_pinhole(pinhole: Pinhole = PINHOLE) -> MsgGenerator:
    pass
