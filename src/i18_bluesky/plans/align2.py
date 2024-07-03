from dataclasses import dataclass
from typing import List, Optional

import bluesky.plan_stubs as bps
import numpy as np
import sympy as sp
from dls_bluesky_core.core import MsgGenerator, inject
from dodal.common.beamlines.beamline_utils import device_instantiation
from dodal.devices.aperturescatterguard import ApertureScatterguard
from dodal.devices.dcm import DCM
from dodal.devices.i22.dcm import CrystalMetadata
from dodal.devices.undulator import Undulator
from dodal.utils import BeamlinePrefix, get_beamline_name
from doddal.devices.focusingmirror import FocusingMirror
from ophyd_async.core import StandardDetector
from ophyd_async.epics.signal import epics_signal_rw

BL = get_beamline_name("i18")

monochromator = DCM()


class IonChamber(StandardDetector):
    pass


t1x = IonChamber(name="t1x")
t1y = IonChamber(name="t1y")
t1theta = IonChamber(name="t1theta")
# note the theta variant is for tomography


def dcm(
    wait_for_connection: bool = True,
    fake_with_ophyd_sim: bool = False,
) -> DCM:
    return device_instantiation(
        DCM,
        "dcm",
        "",
        wait_for_connection,
        fake_with_ophyd_sim,
        bl_prefix=False,
        motion_prefix=f"{BeamlinePrefix(BL).beamline_prefix}-MO-DCM-01:",
        temperature_prefix=f"{BeamlinePrefix(BL).beamline_prefix}-DI-DCM-01:",
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


def vfm(
    wait_for_connection: bool = True,
    fake_with_ophyd_sim: bool = False,
) -> FocusingMirror:
    return device_instantiation(
        FocusingMirror,
        "vfm",
        "-OP-KBM-01:VFM:",
        wait_for_connection,
        fake_with_ophyd_sim,
    )


def hfm(
    wait_for_connection: bool = True,
    fake_with_ophyd_sim: bool = False,
) -> FocusingMirror:
    return device_instantiation(
        FocusingMirror,
        "hfm",
        "-OP-KBM-01:HFM:",
        wait_for_connection,
        fake_with_ophyd_sim,
    )


class KBMirror:
    # usually moved simultaneously, but for fine focus separately
    vertical_bend1 = epics_signal_rw()
    vertical_bend2 = epics_signal_rw()
    horizontal_bend1 = epics_signal_rw()
    horizontal_bend2 = epics_signal_rw()


pinhole = ApertureScatterguard()


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


def calibrate_monochromator() -> MsgGenerator:
    yield from bps.mv(monochromator, "calibrate_dcm")
    yield from bps.mv(monochromator, "measure_foil", "Fe")
    yield from bps.mv(monochromator, "measure_foil", "Mg")


def adjust_bragg_offset_using_absorption_spectrum(
    absorption_spectrum: np.ndarray,
) -> MsgGenerator:
    energy_positions = calculate_derivative_maxima(absorption_spectrum)
    for position in energy_positions:
        yield from bps.mv(monochromator.bragg_in_degrees, position)


def scan_undulator_gap_within_energy_range(energy_range: np.ndarray) -> MsgGenerator:
    for energy in energy_range:
        yield from bps.mv(Undulator.gap, energy)
        yield from bps.trigger_and_read([Undulator])


def centralize_pinhole() -> MsgGenerator:
    yield from bps.mv(pinhole.size, 200)
    yield from bps.mv(pinhole, "centralize")


def focus_kb_mirror_until_tolerance(tolerance: float) -> MsgGenerator:
    # Set initial positions for the KB mirrors
    yield from bps.mv(KBMirror.horizontal_bend1, "start_position")
    yield from bps.mv(KBMirror.horizontal_bend2, "start_position")
    yield from bps.mv(KBMirror.vertical_bend1, "start_position")
    yield from bps.mv(KBMirror.vertical_bend2, "start_position")

    # Adjust horizontal bends first
    for i in range(10):
        yield from bps.mv(KBMirror.horizontal_bend1, f"horizontal_step_{i}")
        yield from bps.mv(KBMirror.horizontal_bend2, f"horizontal_step_{i}")

        yield from bps.trigger_and_read([t1x, t1y, t1theta])
        absorption_profile = yield from bps.rd(t1x.absorption_profile)

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


@inject
def align_beamline(params: BeamlineAlignmentParams) -> MsgGenerator:
    yield from calibrate_monochromator()

    yield from bps.mv(monochromator, "measure_absorption_spectrum")
    absorption_spectrum = yield from bps.rd(monochromator.absorption_spectrum)
    yield from adjust_bragg_offset_using_absorption_spectrum(absorption_spectrum)

    yield from bps.mv(Undulator, "load_lookup_table")

    energy_range = np.linspace(10, 15, num=10)
    yield from scan_undulator_gap_within_energy_range(energy_range)

    gap_positions = yield from bps.rd(Undulator.gap_positions)
    quadratic_fit = np.polyfit(energy_range, gap_positions, 2)
    np.save("gap_lookup_table.npy", quadratic_fit)

    yield from centralize_pinhole()
    yield from focus_kb_mirror_until_tolerance(params.tolerance)

    print("Beamline alignment complete")