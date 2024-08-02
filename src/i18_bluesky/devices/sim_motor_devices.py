from ophyd.sim import Syn2DGauss, SynAxis, SynGauss

from i18_bluesky.devices.device_utils import (
    create_dummy_motor,
    create_syn_2d_gaussian,
    create_syn_gaussian,
)

dummy_mot1 = create_dummy_motor("dummy_motor1")
dummy_mot2 = create_dummy_motor("dummy_motor2")
dummy_mot1.delay = 0.05


def dummy_motor1(name: str = "dummy_motor1") -> SynAxis:
    return dummy_mot1


def dummy_motor2(name: str = "dummy_motor2") -> SynAxis:
    return dummy_mot2


def sim_gauss_det(name: str = "sim_gauss_det") -> SynGauss:
    return create_syn_gaussian(name, dummy_mot1, "dummy_motor1")


def sim_2d_gauss_det(name: str = "sim_2d_gauss_det") -> Syn2DGauss:
    return create_syn_2d_gaussian(
        name, dummy_mot1, "dummy_motor1", dummy_mot2, "dummy_motor2"
    )
