from ophyd import EpicsMotor
from ophyd.sim import Syn2DGauss, SynAxis, SynGauss


def create_epics_motor(motor_name="epics_motor", motor_base_pv="ws416-MO-SIM-01:M1") :
    print(f"Creating Epics motor for {motor_base_pv}")
    epics_motor = EpicsMotor(motor_base_pv, name=motor_name)
    # epics_motor.wait_for_connection(timeout=5) # blueapi fails to connect any PVs!
    return epics_motor

def create_dummy_motor(motor_name="dummy_motor") :
    print(f"Creating dummy motor {motor_name}")
    return SynAxis(name=motor_name, labels = {"motors"})

def create_syn_gaussian(det_name, motor, motor_field, noise="none", noise_multiplier=1) :
    print(f"Creating synthetic Gaussian detector {det_name}")
    syn_gauss = SynGauss(det_name, motor, motor_field, center=0, Imax=5, sigma=0.5, labels={"detectors"})
    syn_gauss.noise.put(noise)
    syn_gauss.noise_multiplier.put(noise_multiplier)
    return syn_gauss

def create_syn_2d_gaussian(det_name, motor1, motor1_field, motor2, motor2_field, noise="none", noise_multiplier=1) :
    print(f"Creating synthetic 2d Gaussian detector {det_name}")

    syn_gauss = Syn2DGauss(det_name, motor1, motor1_field, motor2, motor2_field, center=0, Imax=1, labels={"detectors"})
    syn_gauss.noise.put(noise)
    syn_gauss.noise_multiplier.put(noise_multiplier)
    return syn_gauss
