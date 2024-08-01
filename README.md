[![CI](https://github.com/DiamondLightSource/i18-bluesky/actions/workflows/ci.yml/badge.svg)](https://github.com/DiamondLightSource/i18-bluesky/actions/workflows/ci.yml)
[![Coverage](https://codecov.io/gh/DiamondLightSource/i18-bluesky/branch/main/graph/badge.svg)](https://codecov.io/gh/DiamondLightSource/i18-bluesky)
[![PyPI](https://img.shields.io/pypi/v/i18-bluesky.svg)](https://pypi.org/project/i18-bluesky)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

# i18_bluesky

Plans and devices for the DLS beamline i18

This is where you should write a short paragraph that describes what your module does,
how it does it, and why people should use it.

table again, t1 theta and d7bdiode
MO table is ok

    16 channels Xspress3 detector
        -EA-XPS-02:CAM:MaxSizeX_RBV
      also ArraySize
      also :CONNECTED

pinhole PVs? -AL-APTR-01:TEMP1

diode reading and also DRAIN
diode is ok, there are A and B variants
motors A and B
camera not used

|  Source  |     <https://github.com/DiamondLightSource/i18-bluesky>      |
| :------: | :----------------------------------------------------------: |
|   PyPI   |                  `pip install i18-bluesky`                   |
| Releases | <https://github.com/DiamondLightSource/i18-bluesky/releases> |

This is where you should put some images or code snippets that illustrate
some relevant examples. If it is a library then you might put some
introductory code here:

```python
from i18_bluesky import __version__

print(f"Hello i18_bluesky {__version__}")
```

Or if it is a commandline tool then you might put some example commands here:

```
python -m i18_bluesky --version
```
