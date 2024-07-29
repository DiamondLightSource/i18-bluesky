from devices.device_utils import *
import os

# Make sure EPICS_CA_SERVER_PORT is set to correct value (6064 for DLS sim area detector and motors, 5064 on beamlines)
os.environ['EPICS_CA_SERVER_PORT'] = "6064"

# def sim_x(name : str, pv_name : str) -> EpicsMotor:
def sim_x(name: str = "sim_x", pv_name: str = "ws416-MO-SIM-01:M1") -> EpicsMotor:
    return create_epics_motor(name, pv_name)

def sim_y(name: str="sim_y", pv_name: str = "ws416-MO-SIM-01:M2") -> EpicsMotor:
    return create_epics_motor(name, pv_name)
