import math

import bluesky.plan_stubs as bps
import bluesky.plans as bsp
import numpy as np
from bluesky.preprocessors import subs_decorator
from i18_bluesky.plans.curve_fitting import FitCurves, fit_quadratic_curve


def trial_gaussian(x, a, b, c):
    return a*np.exp( -((x-c)*b)**2)


def bounds_provider(xvals, yvals):
    bounds_a = 0, max(yvals)+0.1
    bounds_b = 0, 10000

    # compute approximate centre position from weighted x position :
    weighted_centre = sum(np.array(xvals)*np.array(yvals))/sum(yvals)
    # set the centre range 10% either side of the peak position
    c_range = max(xvals)-min(xvals)
    centre_range = c_range*0.1
    bounds_c = weighted_centre-centre_range, weighted_centre+centre_range

    return  (bounds_a[0], bounds_b[0], bounds_c[0]), (bounds_a[1], bounds_b[1], bounds_c[1])

def normalise_xvals(xvals, yvals):
    return [x - xvals[0] for x in xvals], yvals


fit_curve_callback = FitCurves()
fit_curve_callback.fit_function = trial_gaussian
fit_curve_callback.set_transform_function(normalise_xvals) # set transform function to make x values relative before fitting
fit_curve_callback.set_bounds_provider(bounds_provider)


def undulator_lookuptable_scan(bragg_start, bragg_step, n_steps,
                               initial_gap_start, gap_range, gap_step,
                               bragg_device,
                               undulator_gap_device,
                               detector,
                               use_last_peak=False,
                               gap_offset=0,
                               *args, **kwargs) :


    # Generate undulator gap values to be used for each inner scan
    # (values are relative to the start position)
    undulator_points = np.linspace(0, gap_range, math.floor(gap_range/gap_step))
    bragg_points = np.linspace(bragg_start, bragg_start+n_steps*bragg_step, n_steps)

    # Move undulator to initial position
    yield from bps.mov(undulator_gap_device, initial_gap_start)

    last_peak_position = None
    bragg_angle = bragg_start
    fit_results = {}

    for bragg_angle in bragg_points :
        print("Bragg angle : {}".format(bragg_angle))
        yield from bps.mov(bragg_device, bragg_angle)

        # Make new set of undulator gap values to be scanned...
        if use_last_peak and last_peak_position is not None:
            # gap start is last peak position
            start_gap = last_peak_position
        else :
            # gap start is current position of undulator gap
            msg = yield from bps.read(undulator_gap_device)
            start_gap = msg[undulator_gap_device.name]['value']
            print("Current undulator gap position : {}".format(start_gap))

        gap_points = undulator_points+start_gap+gap_offset

        print("Undulator values : {}".format(gap_points))

        # fit_curve_callback.fit_bounds = ((0, 0, 0), (10, 1000, undulator_points[-1]))

        @subs_decorator(fit_curve_callback)
        def processing_decorated_plan():
            msg = yield from bsp.list_scan([detector], undulator_gap_device, gap_points)
            return msg

        msg = yield from processing_decorated_plan()

        print("Fit results : {}".format(fit_curve_callback.results))

        # save the peak x position from the curve fit result
        # (fitted x values are relative to first point, so add the start gap position)
        fit_results[bragg_angle] = fit_curve_callback.results[0][0][-1]+gap_points[0]
        last_peak_position = fit_results[bragg_angle]

        print("Fitted peak position : bragg = {}, undulator gap = {}".format(bragg_angle, last_peak_position))
        bragg_angle += bragg_step

    return fit_quadratic_curve(fit_results, *args, **kwargs)


