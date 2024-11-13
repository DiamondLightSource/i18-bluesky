import os
# os.environ['EPICS_CA_SERVER_PORT'] = "6064" # set the Epics port before other imports, otherwise wrong value is picked up (5054)

from i18_bluesky.plans.undulator_lookuptable_plan import undulator_lookuptable_scan
from bluesky import RunEngine
from bluesky.callbacks.best_effort import BestEffortCallback

from i18_bluesky.plans.curve_fitting import fit_quadratic_curve, quadratic
from ophyd.sim import SynGauss, SynAxis
from ophyd_async.epics.motor import Motor
import asyncio
import math
from ophyd import EpicsMotor, EpicsSignalRO


def load_ascii_lookuptable(filename, lines_to_skip=0) :
    """
    Load 2-colummn x,y Ascii data from file and convert to numbers (optionally skipping the first few lines)

    :param filename:
    :param lines_to_skip how many lines to skip before storing the data
    :return: dictionary containing the value on each line { x1:y1, x2:y2 ...}

    """
    print("Loading ascii lookup table from {}".format(filename))
    with open(filename, "r") as f :
        for i in range(lines_to_skip) :
            f.readline()

        number_vals={}
        for val in f :
            number_val = [float(s) for s in val.split()]
            number_vals[number_val[0]] = number_val[1]

        return number_vals



def lookup_value(y_search, func, range_min=0, range_max=100, tolerance=1e-6, max_iters=20):
    """
        Lookup x value for a curve y(x), such that y_search = y(x)
        Uses interval bisection to reach desired accuracy tolerance, up to maxiumum number of iterations

    """
    def eval_func(x_pos) :
        return x_pos, func(x_pos)

    def in_range(v, v1, v2) :
        return min(v1, v2) < v < max(v1, v2)

    #evaluate func at lower and upper x bounds :
    lower=eval_func(range_min)
    upper=eval_func(range_max)

    iter_num = 0

    best_y = y_search+100

    while iter_num < max_iters and math.fabs(best_y-y_search) > tolerance :
        # evaluate function at midpoint
        mid = eval_func((lower[0]+upper[0])/2.0)

        # update upper, lower bound depending on midpoint y value relative to y_search
        if in_range(y_search, lower[1], mid[1]):
            upper = mid
        else :
            lower = mid
        best_y = (lower[1]+upper[1])/2.0
        iter_num += 1
        # print(lower, upper)

    # return best x value
    return (lower[0]+upper[0])/2.0


def fit_harmonic_lookuptable_curve(filename, **kwargs) :
    """Load undulator gap lookup table from Ascii file and fit quadratic curve to undlator gap vs Bragg angle

    :param filename:
    :param kwargs:
    :return: function that returns undulator gap for a given Bragg angle
    """

    vals = load_ascii_lookuptable(filename, lines_to_skip=2)
    params, cov = fit_quadratic_curve(vals, **kwargs)

    def best_undulator_gap(angle) :
        return quadratic(angle, *params)

    def gradient(angle) :
        return params[1] + params[2]*bragg_angle

    return best_undulator_gap, gradient


class UndulatorCurve(SynGauss) :
    def __init__(self,  *args, **kwargs):
        self.peak_position_function = None
        self.bragg_motor = None
        super().__init__(*args, **kwargs)

    def _compute(self):
        if self.peak_position_function is not None and self.bragg_motor is not None:
            # update the centre position using peak_position_function with bragg_motor position as parameter
            m = self.bragg_motor.position
            self.center.put(self.peak_position_function(m))
        return super()._compute()


filename="lookuptable_harmonic1.txt"
beamline_lookuptable_dir="/dls_sw/i18/software/gda_versions/gda_9_36/workspace_git/gda-diamond.git/configurations/i18-config/lookupTables/"
filename=beamline_lookuptable_dir+"Si111/lookuptable_harmonic9.txt"

# load lookuptable from ascii file and fit quadratic curve
undulator_gap, bragg_angle = fit_harmonic_lookuptable_curve(filename, show_plot=False)

pv_prefix="ws416-"
use_epics_motors = False
beamline = True

bragg_pv_name = "BL18I-MO-DCM-01:BRAGG" if beamline else pv_prefix+"MO-SIM-01:M1"
undulator_gap_pv_name = "SR18I-MO-SERVC-01:BLGAPMTR" if beamline else pv_prefix+"MO-SIM-01:M2"

def make_epics_motor(*args, **kwargs) :
    mot = EpicsMotor(*args, **kwargs)
    #mot = Motor(*args, **kwargs)
    if isinstance(mot, EpicsMotor):
        mot.wait_for_connection()
    elif isinstance(mot, Motor):
        asyncio.run(mot.connect())

    return mot

# Setup the motors and detector for the environment
if beamline:
    os.environ['EPICS_CA_SERVER_PORT'] = "5064"

    bragg_motor = make_epics_motor(bragg_pv_name, name="bragg_angle")
    undulator_gap_motor = make_epics_motor(undulator_gap_pv_name, name="undulator_gap_motor")
    d7diode = EpicsSignalRO("BL18I-DI-PHDGN-07:B:DIODE:I", name="d7diode")
else:
    if use_epics_motors:
        bragg_motor = make_epics_motor(bragg_pv_name, name="bragg_angle")
        undulator_gap_motor = make_epics_motor(undulator_gap_pv_name, name="undulator_gap_motor")
        #bragg_motor.wait_for_connection()
        #undulator_gap_motor.wait_for_connection()
        # make sure mres is set to small value to show the small changes in position (e.g. 0.001(
    else:
        bragg_motor= SynAxis(name="bragg_motor", labels={"motors"})
        undulator_gap_motor = SynAxis(name="undulator_gap_motor", labels={"motors"}, delay=0.01)
        undulator_gap_motor.precision = 6 # decimal places of precision in readout value
        undulator_gap_motor.pause = 0

    # Setup diode to return gaussian intensity profile
    d7diode = UndulatorCurve("d7diode", undulator_gap_motor, "undulator_gap_motor",
        center=0,
        Imax=1)
    # peak of the intensity depends on position of bragg_motor, and peak position from quadratic curve 'undulator_gap'
    # i.e. peak_position = undulator_gap(bragg_motor.position)
    d7diode.peak_position_function = undulator_gap
    d7diode.bragg_motor = bragg_motor
    d7diode.sigma.put(0.006)
    d7diode.trigger()
    d7diode.precision = 5


# Bragg angle start position, stepsize, number of steps
# bragg_start = 55
# bragg_step = 0.3
# bragg_num_steps = 20

bragg_start = 11.4
bragg_step = 0.3
bragg_num_steps = 5
# gap_range = 0.06

# Undulator range : lookup undulator values for Bragg start position and range
gap_start = undulator_gap(bragg_start)
gap_end = undulator_gap(bragg_start-bragg_step)
gap_range = 2.5*(gap_end-gap_start) # double, to make sure don't miss the peak

gap_start = undulator_gap(bragg_start) - 0.5*gap_range

print("Gap for start Bragg=%.3f : %.4f\nGap start, range, end : %.4f, %.4f, %.4f"
      %(bragg_start, undulator_gap(bragg_start), gap_start, gap_range, gap_start+gap_range))


bec = BestEffortCallback()
RE = RunEngine()
RE.subscribe(bec)

from databroker import Broker
db = Broker.named('temp') # only works if name is 'temp' !
# Insert all metadata/data captured into db.
RE.subscribe(db.insert)

from bluesky.plans import scan

RE(scan([d7diode], undulator_gap_motor, 6.8, 7.2, 41))



"""
RE(scan([d7diode], undulator_gap_motor, gap_start, gap_start+gap_range, 41))
"""

"""

RE(undulator_lookuptable_scan(bragg_start, -bragg_step, bragg_num_steps,
                              gap_start, gap_range, 0.01,
                              bragg_motor, undulator_gap_motor, d7diode,
                              gap_offset=0.0, use_last_peak=True,
                              show_plot=True))
"""