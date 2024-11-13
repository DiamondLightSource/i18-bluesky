import os
os.environ['EPICS_CA_SERVER_PORT'] = "6064"

from ophyd.pv_positioner import PVPositioner
from ophyd import EpicsSignalRO, EpicsSignal, EpicsMotor
from ophyd import Component as Cpt

from bluesky import RunEngine
from bluesky.callbacks.best_effort import BestEffortCallback
from bluesky.plans import scan


class EpicsMotorPositioner(PVPositioner):
    """PVPositioner implementation that uses a limited subset of the PVs available in Epics motor record.
    Uses the .VAL record to set the position, .RBV for readback, .DMOV
    for the 'busy' status and .STOP to stop the motor.

    """
    setpoint = Cpt(EpicsSignal, ".VAL")
    readback = Cpt(EpicsSignalRO, ".RBV")
    done = Cpt(EpicsSignalRO, ".DMOV")
    stop_signal = Cpt(EpicsSignal, ".STOP")
    stop_value = 1
    done_value = 1

pv_prefix = "ws416-MO-SIM-01:M2"
# pv_prefix = "SR18I-MO-SERVC-01:BLGAPMTR"

simple_positioner = EpicsMotorPositioner(pv_prefix, name="simple_positioner")
epics_motor = EpicsMotor(pv_prefix, name="epics_motor")

bec = BestEffortCallback()
RE = RunEngine()
RE.subscribe(bec)

RE(scan([simple_positioner], simple_positioner, 1, 10, 10))
RE(scan([epics_motor], epics_motor, 1, 10, 10))

