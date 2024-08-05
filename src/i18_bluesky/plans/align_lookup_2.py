from dataclasses import dataclass
from typing import List, Optional

import bluesky.plan_stubs as bps
import numpy as np
import sympy as sp
from bluesky.devices.monochromator import DCM
from dls_bluesky_core.core import MsgGenerator, inject

monochromator = inject("monochromator")
undulator = inject("undulator")
pinhole = inject("pinhole")
KBMirror = inject("kb_mirror")


def calculate_derivative_maxima(data: np.ndarray) -> List[float]:
    x = sp.Symbol("x")
    y = sp.interpolating_spline(3, sp.lambdify(x, data))
    derivative = y.diff(x)
    critical_points = sp.solve(derivative, x)
    return [float(cp) for cp in critical_points if cp.is_real]


@dataclass
class BeamlineAlignmentParams:
    target_energy: Optional[float] = 12.0
    tolerance: Optional[float] = 0.1


def calibrate_monochromator(monochromator: DCM) -> MsgGenerator:
    yield from bps.mv(monochromator, "calibrate_dcm")
    # todo this measure foil makes no sense at the moment
    yield from bps.mv(monochromator, "measure_foil", "Fe")
    yield from bps.mv(monochromator, "measure_foil", "Mg")


def adjust_bragg_offset_using_absorption_spectrum(
    monochromator,
    absorption_spectrum: np.ndarray,
) -> MsgGenerator:
    energy_positions = calculate_derivative_maxima(absorption_spectrum)
    for position in energy_positions:
        yield from bps.mv(monochromator.bragg_in_degrees, position)


def scan_undulator_gap_within_energy_range(
    undulator, energy_range: np.ndarray
) -> MsgGenerator:
    for energy in energy_range:
        yield from bps.mv(undulator.gap, energy)
        yield from bps.trigger_and_read([undulator])


def centralize_pinhole(pinhole) -> MsgGenerator:
    yield from bps.mv(pinhole.size, 200)
    yield from bps.mv(pinhole, "centralize")


def focus_kb_mirror_until_tolerance(
    KBMirror, pinhole, tolerance: float
) -> MsgGenerator:
    # Set initial positions for the KB mirrors
    yield from bps.mv(KBMirror.horizontal_bend1, "start_position")
    yield from bps.mv(KBMirror.horizontal_bend2, "start_position")
    yield from bps.mv(KBMirror.vertical_bend1, "start_position")
    yield from bps.mv(KBMirror.vertical_bend2, "start_position")

    # Adjust horizontal bends first
    for i in range(10):
        yield from bps.mv(KBMirror.horizontal_bend1, f"horizontal_step_{i}")
        yield from bps.mv(KBMirror.horizontal_bend2, f"horizontal_step_{i}")

        t1x = yield from bps.rd(KBMirror.t1x)
        t1y = yield from bps.rd(KBMirror.t1y)
        t1theta = yield from bps.rd(KBMirror.theta)
        assert t1x is int and t1y is int and t1theta is int
        yield from bps.trigger_and_read([t1x, t1y, t1theta])
        absorption_profile = yield from bps.rd(t1x, "absorption_profile")

        beam_size = np.std(absorption_profile)
        if beam_size < tolerance:
            break

    # Adjust vertical bends next
    for i in range(10):
        yield from bps.mv(KBMirror.vertical_bend1, f"vertical_step_{i}")
        yield from bps.mv(KBMirror.vertical_bend2, f"vertical_step_{i}")

        yield from bps.trigger_and_read([t1x, t1y, t1theta])
        absorption_profile = yield from bps.rd(t1x.absorption_profile)

        beam_size = np.std(absorption_profile)
        if beam_size < tolerance:
            break

    # Move mirrors and pinhole to final positions
    yield from bps.mv(KBMirror.horizontal_bend1, "final_position")
    yield from bps.mv(KBMirror.horizontal_bend2, "final_position")
    yield from bps.mv(KBMirror.vertical_bend1, "final_position")
    yield from bps.mv(KBMirror.vertical_bend2, "final_position")
    yield from bps.mv(pinhole, "final_position")


def align_beamline(
    undulator, monochromator, params: BeamlineAlignmentParams
) -> MsgGenerator:
    yield from calibrate_monochromator()

    yield from bps.mv(monochromator, "measure_absorption_spectrum")
    absorption_spectrum = yield from bps.rd(monochromator.absorption_spectrum)
    yield from adjust_bragg_offset_using_absorption_spectrum(absorption_spectrum)

    yield from bps.mv(undulator, "load_lookup_table")

    energy_range = np.linspace(10, 15, num=10)
    yield from scan_undulator_gap_within_energy_range(energy_range)

    gap_positions = yield from bps.rd(undulator.gap_positions)
    quadratic_fit = np.polyfit(energy_range, gap_positions, 2)
    np.save("gap_lookup_table.npy", quadratic_fit)

    yield from centralize_pinhole()
    yield from focus_kb_mirror_until_tolerance(params.tolerance)

    print("Beamline alignment complete")
