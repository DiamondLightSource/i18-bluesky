from dodal.utils import BeamlinePrefix, get_beamline_name

BL = get_beamline_name("i18")
BEAMLINE_PREFIX = BeamlinePrefix(BL).beamline_prefix
