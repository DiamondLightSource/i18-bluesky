from typing import List

import bluesky.plan_stubs as bps
from bluesky import RunEngine
from bluesky.preprocessors import inject
from dls_bluesky_core.core import MsgGenerator
from dodal.devices.xspress3.xspress3 import Xspress3

# Instantiate the devices
element_changer = ElementChanger("element_changer_prefix", name="element_changer")
i0 = Xpress3Detector("i0_detector_prefix", name="i0")
IT = Xpress3Detector("IT_detector_prefix", name="IT")


def xspress3mini(
    wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
) -> Xspress3:
    """Get the i03 Xspress3Mini device, instantiate it if it hasn't already been.
    If this is called when already instantiated in i03, it will return the existing object.
    """
    return device_instantiation(
        Xspress3,
        "xspress3mini",
        "-EA-XSP3-01:",
        wait_for_connection,
        fake_with_ophyd_sim,
    )


@inject
def fluorescence_scan(elements: List[str], count_time: float) -> MsgGenerator:
    for element in elements:
        yield from bps.mv(element_changer.current_element, element)
        yield from bps.mv(i0.count_time, count_time)
        yield from bps.mv(IT.count_time, count_time)

        yield from bps.trigger_and_read([i0, IT])
        i0_data = yield from bps.rd(i0.data)
        IT_data = yield from bps.rd(IT.data)

        print(f"Element: {element}, i0: {i0_data}, IT: {IT_data}")


# Instantiate the RunEngine
RE = RunEngine({})

# Define the list of elements for the scan
elements_list = ["Fe", "Cu", "Zn", "Mn", "Ni", "Co", "Cr", "V"]
scan_count_time = 1.0  # 1 second count time for each scan

# Run the fluorescence scan
RE(fluorescence_scan(elements_list, scan_count_time))
