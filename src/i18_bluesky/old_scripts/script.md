
Adjust undulator gap to using current lookup table for initial Bragg angle
Scan across desired range of Bragg angles, for each angle :
    Scan undulator gap (current gap value ± small range) and measure on d7bdiode (Diode PV is BL18I-DI-PHDGN-07:B:DIODE:I)
    Find undulator gap that gives peak d7bdiode value (fit gaussian curve, store peak position).
    Fit quadratic curve to the set of Bragg angle - undulator gap values. These values are used to generate the lookup table of undulator gap vs. Bragg angle.
    Scan is currently done by the client; quadratic curve fit is done using IDL.
    Undulator gap scans are are carried out at each harmonic.
Beamline staff manually update the lookup table - copy-pasting updated section (i.e. values for a range of bragg angles) into text file to replace old values.
