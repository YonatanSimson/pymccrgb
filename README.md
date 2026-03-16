# pymccrgb

[![Build Status](https://travis-ci.com/stgl/pymccrgb.svg?branch=master)](https://travis-ci.com/rmsare/pymccrgb)
[![Documentation Status](https://readthedocs.org/projects/pymccrgb/badge/?version=latest)](https://pymccrgb.readthedocs.io/en/latest/?badge=latest)
[![DOI](https://joss.theoj.org/papers/10.21105/joss.01777/status.svg)](https://doi.org/10.21105/joss.01777)

**pymccrgb** is a Python package for multiscale curvature classification of
point clouds with color attributes. 

It extends a popular classification method
([MCC lidar](https://sourceforge.net/p/mcclidar/wiki/Home/)) [[0]](#references) to point cloud datasets with multiple color channels, such as those
commonly produced in surveys using drone photography or other platforms. It can be used to distinguish points from the
ground surface and low vegetation in data produced by structure from motion photogrammetry,
stereo photogrammetry, or multi-spectral lidar scanning, or to filter colorized lidar point clouds in LAS/LAZ or CSV format.

The intended users are scientists in geomorphology, ecology, or planetary science
who want to classify point clouds for topographic analysis, canopy height measurements, or other spectral classification.

### Installation

This package is developed for Linux and Python 3.10+. It depends on common
Python packages like sklearn, numpy, PDAL, the LibLAS C API, and
[MCC Python bindings](https://github.com/stgl/pymcc).

#### 1. Install system dependencies (LibLAS, PDAL, and build tools)

LibLAS is not available via apt on Ubuntu 22.04+, so it must be built from source:

```bash
sudo apt update
sudo apt install -y cmake g++ libgdal-dev libboost-all-dev \
    libgeotiff-dev libtiff-dev

git clone https://github.com/libLAS/libLAS.git
cd libLAS
mkdir build && cd build
cmake ..
make -j$(nproc)
sudo make install
```

PDAL must be built from source on Ubuntu 22.04+ to avoid a GDAL/PROJ version
conflict. The apt and conda-forge packages link PDAL against `libgdal.so.30`
(GDAL 3.4), which pulls in both `libproj.so.22` and `libproj.so.25`
simultaneously, causing a segfault on startup.

Use the provided install script, which pins the build to GDAL 3.8
(`libgdal.so.34`) and PROJ 9 (`libproj.so.25`):

```bash
# From the pymcc repo root:
sudo bash install_pdal_2.7.sh

# Override defaults if needed:
PDAL_VERSION=2.7.2 VENV=/path/to/venv sudo -E bash install_pdal_2.7.sh
```

The script will verify after installation that no conflicting libraries are
linked, and will fail fast if the build is not clean.

#### 2. Install pymccrgb in a virtual environment

```bash
git clone https://github.com/stgl/pymccrgb
cd pymccrgb
python -m venv venv
source venv/bin/activate
pip install scikit-build-core cython numpy
pip install --no-build-isolation -e .
py.test pymccrgb/tests
```

#### Conda (alternative)

```bash
git clone https://github.com/stgl/pymccrgb
cd pymccrgb
conda env create -f environment.yml
conda activate pymcc
pip install --no-build-isolation -e .
py.test pymccrgb/tests
```

### Requirements

The LibLAS C library and PDAL are required for MCC and `pymccrgb`. The MCC
wrapper also requires Boost and the C++11 or later standard library.
Building from source requires `scikit-build-core`, `cython`, and `cmake`.

See the [LibLAS install guide](https://liblas.org/start.html#installation) and
[PDAL install guide](https://pdal.io/en/stable/download.html) for more details.

### Examples

Example notebooks are available in the docs or at [docs/source/examples](docs/source/examples).

#### Topography under tree cover

```python
from pymccrgb import mcc, mcc_rgb
from pymccrgb.datasets import load_mammoth_lidar
from pymccrgb.plotting import plot_results

# Load sample data (Mammoth Mountain, CA)
data = load_mammoth_lidar(npoints=1e6)

# MCC algorithm
ground_mcc, labels_mcc = mcc(data)

# MCC-RGB algorithm
ground_mccrgb, labels_mccrgb = mcc_rgb(data)

plot_results(data, labels_mcc, labels_mccrgb)
```

[![MCC results](docs/img/mccrgb.png)]()

Results of MCC and MCC-RGB on a forested area near Mammoth Mountain, CA. 

### Documentation

Read the documentation for example use cases, an API reference, and more at [pymccrgb.readthedocs.io](https://pymccrgb.readthedocs.io). 

### Contributing

#### Bug reports

Bug reports are much appreciated. Please [open an issue](https://github.com/rmsare/pymccrgb/issues/new) with the `bug` label,
and provide a minimal example illustrating the problem.

#### Suggestions

Feel free to [suggest new features](https://github.com/rmsare/pymccrgb/issues/new) in an issue with the `new-feature` label.

#### Pull requests

If you would like to add a feature or fix a bug, please fork the repository, create a feature branch, and [submit a PR](https://github.com/rmsare/pymccrgb/compare) and reference any relevant issues. There are nice guides to contributing with GitHub [here](https://akrabat.com/the-beginners-guide-to-contributing-to-a-github-project/) and [here](https://yourfirstpr.github.io/). Please include tests where appropriate and check that the test suite passes (a Travis build or `pytest pymccrgb/tests`) before submitting.

### Support and questions

Please [open an issue](https://github.com/rmsare/pymccrgb/issues/new) with your question.

### References

[0] Evans, J. S., & Hudak, A. T. 2007. A multiscale curvature algorithm for classifying discrete return LiDAR in forested environments. IEEE Transactions on Geoscience and Remote Sensing, 45(4), 1029-1038 [doi](https://doi.org/10.1109/TGRS.2006.890412) 

### License

This work is licensed under the MIT License (see [LICENSE](LICENSE)). It also
incorporates a wrapper for the [`mcc-lidar` implementation](https://sourceforge.net/p/mcclidar),
which is distributed under the Apache license (see [LICENSE.txt](https://sourceforge.net/p/mcclidar/code/HEAD/tree/tags/2.1/LICENSE.txt)).
