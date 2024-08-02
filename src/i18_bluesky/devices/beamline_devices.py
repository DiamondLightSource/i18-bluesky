from ophyd import EpicsMotor
from ophyd.signal import EpicsSignalRO

from i18_bluesky.devices.device_utils import create_epics_motor


def d7bdiode(
    name: str = "d7bdiode", pv_name: str = "BL18I-DI-PHDGN-07:B:DIODE:I"
) -> EpicsSignalRO:
    return EpicsSignalRO(pv_name, name=name)


def t1x(name: str = "t1x", pv_name: str = "BL18I-MO-TABLE-01:X") -> EpicsMotor:
    return create_epics_motor(name, pv_name)


def t1y(name: str = "t1y", pv_name: str = "BL18I-MO-TABLE-01:Y") -> EpicsMotor:
    return create_epics_motor(name, pv_name)


def t1z(name: str = "t1z", pv_name: str = "BL18I-MO-TABLE-01:Z") -> EpicsMotor:
    return create_epics_motor(name, pv_name)


def t1theta(name: str = "t1z", pv_name: str = "BL18I-MO-TABLE-01:THETA") -> EpicsMotor:
    return create_epics_motor(name, pv_name)
