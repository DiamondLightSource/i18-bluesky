# alignment plan overview

sample stages T1X
T1Y

(for tomography also T1Theta)

two ion chambers

kb motors, two mirrors vertical and horizontal
ecah has 2 motors, bend1, bend2
usually moved simultaneously, but for fine focus separately

get the gaussian shape IT transmission detector we get the shape

    first, we lookup table - calibrate the DCM
    - measure foil, etc Fe, Mg, then absorption spectrum
    then the xanes absorption - then derivative, argmax of the first derivative
    https://www.geeksforgeeks.org/python-sympy-derivative-method/
    then Bragg offset is adjusted to match the calibrated value

    second the idgap lookup tables
    - for 10-15 points inside the energy range for this element
    we scan the gap fo the insertion devise, looking for the maximum
    then quadratic interpolation, written into the file,
    then GDA probably some interpolation
    TFG calculates frequency from current via voltage
    so we need to load the panda configuration

    align the pinhole to reduce the scatter -
    400 micron or 200 micron, then centralize it
    usuallly not seen immediately
    FocusingMirror misses curvature
    preparation for the wire stage - check if we have any
    gold wires on the sample stage - scanned in one direction
    first horizonal, vertical
    then record with IT the absorption profile, derviative and fitting
    then changing the bend
    could be 10 iterations, in either direction
    to minimuze the beam size until it changes
    to see the beam shape and the size
    takes usually 30 minutes to go through focusing manually, 2-3 hours

    visual comparison fo the drviative -
    best if without the tails, could be parametrized
    or 50 micron beam - and then defocus to get to that

    golden plate with wires is moved by some other location

## Alignment types

There are three major types of alignment:

- idgap
- pinhole
- wire scan

Other alignment (non exhaustive):

- KB mirror optimization (?)

Only the idgap one caches the results in a lookup table.

### IDGAP alignment details

moving the monochromator to a given Bragg angle, keeping it fixed and then scanning the undulator gap across a small range.

On the d7 diode the Bragg with a peak is that gap

2d scan of Bragg angle vs undulator gap, and peak compared to d7

### pinhole

## from the files

first, we lookup table - calibratre the DCM -
measure foil, etc Fe, Mg, then absorption spectrum
then the xanes absorption - then derivative, argmax of the first derivative
https://www.geeksforgeeks.org/python-sympy-derivative-method/
then Bragg offset is adjusted to match the calibrated value

second the idgap lookup tables -
for 10-15 points inside the energy range for this element
we scan the gap fo the insertion devise, looking for the maximum
then quadratic interpolation
written into the file, then GDA probably some interpolation
TFG calculates frequency from current via voltage
so we need to load the panda configuration

align the pinhole to reduce the scatter

- 400 micron or 200 micron, then centralize it
  usuallly not seen immediately
  FocusingMirror misses curvature
  preparation for the wire stage - check if we have any
  gold wires on the sample stage - scanned in one direction
  first horizonal, vertical
  then record with IT the absorption profile, derviative and fitting
  then changing the bend
  could be 10 iterations, in either direction
  to minimuze the beam size until it changes
  to see the beam shape and the size
  takes usually 30 minutes to go through focusing manually, 2-3 hours

visual comparison fo the derivative- best if without the tails,
could be parametrized
or 50 micron beam - and then defocus to get to that
