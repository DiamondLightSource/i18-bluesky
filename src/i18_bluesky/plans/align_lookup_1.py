from dataclasses import dataclass
from typing import Optional

import bluesky.plan_stubs as bps
import numpy as np
import sympy as sp
from dodal.common import MsgGenerator, inject
from dodal.devices.undulator import Undulator

monochromator = inject("monochromator")

I0 = inject("i0")
IT = inject("it")
t1x = inject("t1x")
t1y = inject("t1y")
t1theta = inject("t1theta")
# note the theta variant is for tomography

pinhole = inject("pinhole")

# get the gaussian shape IT transmission detector we get the shape


def derivative_max(data):
    x, y = sp.symbols("x y")
    y = sp.Function("y")(x)
    derivative = sp.diff(y, x)
    argmax = sp.solve(sp.Eq(derivative, 0), x)
    return argmax


@dataclass
class BeamlineAlignmentParams:
    target_energy: Optional[float] = 12.0
    tolerance: Optional[float] = 0.1


@inject
def align_beamline(KBMirror, tolerance: float) -> MsgGenerator:
    # first, we lookup table - calibratre the DCM -
    # measure foil, etc Fe, Mg, then absorption spectrum
    # then the xanes absorption - then derivative, argmax of the first derivative
    # https://www.geeksforgeeks.org/python-sympy-derivative-method/
    # then Bragg offset is adjusted to match the calibrated value
    yield from bps.mv(monochromator, "calibrate_dcm")
    yield from bps.mv(monochromator, "measure_foil", "Fe")
    yield from bps.mv(monochromator, "measure_foil", "Mg")

    yield from bps.mv(monochromator, "measure_absorption_spectrum")
    absorption_spectrum = yield from bps.rd(monochromator.absorption_spectrum)
    energy_positions = derivative_max(absorption_spectrum)

    for position in energy_positions:
        yield from bps.mv(monochromator.bragg_offset, position)

    yield from bps.mv(Undulator, "load_lookup_table")

    # second the idgap lookup tables -
    # for 10-15 points inside the energy range for this element
    # we scan the gap fo the insertion devise, looking for the maximum
    # then quadratic interpolation
    # written into the file, then GDA probably some interpolation
    # TFG calculates frequency from current via voltage
    # so we need to load the panda configuration
    energy_range = np.linspace(10, 15, num=10)

    for energy in energy_range:
        yield from bps.mv(Undulator.current_gap, energy)
        yield from bps.trigger_and_read([Undulator])

    gap_positions = yield from bps.rd(Undulator.gap_positions)
    quadratic_fit: np.ndarray[float] = np.polyfit(energy_range, gap_positions, 2)
    np.save("gap_lookup_table.npy", quadratic_fit)

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

    yield from bps.mv(pinhole.size, 200)
    yield from bps.mv(pinhole, "centralize")

    yield from bps.mv(KBMirror.vertical_bend1, "start_position")
    yield from bps.mv(KBMirror.vertical_bend2, "start_position")
    yield from bps.mv(KBMirror.horizontal_bend1, "start_position")
    yield from bps.mv(KBMirror.horizontal_bend2, "start_position")

    # visual comparison fo the derivative- best if without the tails,
    # could be parametrized
    # or 50 micron beam - and then defocus to get to that
    for i in range(10):
        yield from bps.mv(KBMirror.vertical_bend1, f"step_{i}")
        yield from bps.mv(KBMirror.vertical_bend2, f"step_{i}")
        yield from bps.mv(KBMirror.horizontal_bend1, f"step_{i}")
        yield from bps.mv(KBMirror.horizontal_bend2, f"step_{i}")

        yield from bps.trigger_and_read([t1x, t1y, t1theta])
        absorption_profile = yield from bps.rd(t1x.absorption_profile)

        beam_size = np.std(absorption_profile)
        if beam_size < tolerance:
            break

    yield from bps.mv(KBMirror, "final_position")
    yield from bps.mv(pinhole, "final_position")

    print("Beamline alignment complete")
