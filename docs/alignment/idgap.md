# idgap alignment

## prerequistes

- must be ran with beam

## explanations

harmonics are an emergent property of the optics physics, found out empirically
harmonics rise monotonically with Z atomic number. Still
`/dls/science/groups/i18/lookuptable/Fe_Co_Ni_Aug24.txt` - so three elements next to one another, all 3 under the same harmonic

XFAS community uses eV for initial energy and inverse angsotmr sfor final energy

energies for each element are stable for 200 years and often scanned with a 10% margin of errror to read more

Mo hightest energy so at the highest harmonic - 19

<https://docs.scipy.org/doc/scipy/reference/constants.html>

usually 1 element has one edge

## physical description

idgap(undulator)- beam -> Monochromator (Bragg angle) - beam -> diode d7 (readout)

## steps

### preparation step

- set diode to `in line diode` mode
- filter A must be adjusted so that the current is below 20 (magic number found decades ago)
- the diode must be configured so that it's giving maximum intensity variance without being oversaturated
- that is done through adjusting the discrete size of a gap between the diode and the beam

### Scannign step

1. scan goes to the first angle/energy - using the previous lookup table
2. mm on x and readig is in microAmps
3. peak fitting, resulting in a 2d relationship of x,y maxxing the z value

### Cleanup stage

- move d7 filter a back into 'gap' mode
- move d7 filter b back into 'gap' mode

## Common issues

sources of issues when running manually:

- saturation
- if the original idgap is so far out of the scan

usually takes 10 minutes, so for 19 harmonics 3 hours?
