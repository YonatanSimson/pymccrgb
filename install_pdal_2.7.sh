#!/usr/bin/env bash
# install_pdal_2.7.sh
# Builds PDAL 2.7.x from source, pinned to GDAL 3.8 (libgdal.so.34) and
# PROJ 9 (libproj.so.25) to avoid the libproj.so.22 / libproj.so.25 dual-load
# segfault that occurs when PDAL is linked against the older libgdal.so.30.
#
# Usage:
#   sudo bash install_pdal_2.7.sh
#   PDAL_VERSION=2.7.2 VENV=/path/to/venv sudo bash install_pdal_2.7.sh
set -euo pipefail

PDAL_VERSION="${PDAL_VERSION:-2.7.2}"
VENV="${VENV:-/home/yonatan_s/env_system_cuda13}"
BUILD_DIR="${BUILD_DIR:-/tmp/pdal_build}"
INSTALL_PREFIX="/usr/local"
JOBS=$(nproc)

# Pinned library paths — GDAL 3.8 and PROJ 9 only; do not let cmake find libgdal.so.30 or libproj.so.22
GDAL_INCLUDE="/usr/include/gdal"
GDAL_LIB="/usr/lib/x86_64-linux-gnu/libgdal.so.34"
PROJ_INCLUDE="/usr/include"
PROJ_LIB="/usr/lib/x86_64-linux-gnu/libproj.so.25"

echo "=== Building PDAL ${PDAL_VERSION} → ${INSTALL_PREFIX} ==="
echo "    GDAL : ${GDAL_LIB}"
echo "    PROJ : ${PROJ_LIB}"
echo "    venv : ${VENV}"
echo "    jobs : ${JOBS}"
echo ""

# --- Sanity checks ---
for f in "${GDAL_LIB}" "${PROJ_LIB}" "${GDAL_INCLUDE}/gdal.h" "${PROJ_INCLUDE}/proj.h"; do
    if [ ! -e "${f}" ]; then
        echo "ERROR: required file not found: ${f}"
        echo "Install libgdal34, libgdal-dev, libproj25, libproj-dev and re-run."
        exit 1
    fi
done

GDAL_VERSION=$(gdal-config --version 2>/dev/null || true)
PROJ_VERSION=$(pkg-config --modversion proj 2>/dev/null || true)
echo "System GDAL: ${GDAL_VERSION}  |  PROJ: ${PROJ_VERSION}"
if [[ "${GDAL_VERSION}" != 3.8* ]]; then
    echo "WARNING: expected GDAL 3.8.x but got ${GDAL_VERSION}. Continuing anyway."
fi
echo ""

# --- Build dependencies ---
echo "--- Installing build dependencies ---"
sudo apt-get update -q
sudo apt-get install -y \
    build-essential cmake ninja-build git curl \
    libgdal-dev libproj-dev \
    libpq-dev libtiff-dev libgeotiff-dev \
    libboost-filesystem-dev libboost-iostreams-dev \
    libboost-program-options-dev libboost-system-dev \
    liblzma-dev zlib1g-dev libcurl4-openssl-dev \
    libarpack2-dev liblapack-dev \
    python3-dev

# --- Remove any old PDAL installation to avoid stale libpdalcpp.so links ---
echo ""
echo "--- Removing old PDAL installation (if any) ---"
sudo rm -f \
    "${INSTALL_PREFIX}/bin/pdal" \
    "${INSTALL_PREFIX}/lib/libpdalcpp.so"* \
    "${INSTALL_PREFIX}/lib/libpdal_plugin_"* \
    "${INSTALL_PREFIX}/lib/cmake/PDAL/"* 2>/dev/null || true
sudo ldconfig

# --- Download PDAL source ---
echo ""
echo "--- Downloading PDAL ${PDAL_VERSION} ---"
mkdir -p "${BUILD_DIR}" && cd "${BUILD_DIR}"

if [ ! -d "PDAL-${PDAL_VERSION}-src" ]; then
    TARBALL="PDAL-${PDAL_VERSION}-src.tar.bz2"
    curl -fLO "https://github.com/PDAL/PDAL/releases/download/${PDAL_VERSION}/${TARBALL}"
    tar -xjf "${TARBALL}"
fi

# --- CMake configure & build ---
echo ""
echo "--- Configuring CMake (pinned GDAL 3.8 + PROJ 9) ---"
cd "PDAL-${PDAL_VERSION}-src"
mkdir -p build && cd build

cmake .. \
    -GNinja \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_INSTALL_PREFIX="${INSTALL_PREFIX}" \
    \
    -DGDAL_INCLUDE_DIR="${GDAL_INCLUDE}" \
    -DGDAL_LIBRARY="${GDAL_LIB}" \
    \
    -DPROJ_INCLUDE_DIR="${PROJ_INCLUDE}" \
    -DPROJ_LIBRARY="${PROJ_LIB}" \
    \
    -DWITH_TESTS=OFF \
    -DBUILD_PLUGIN_CPD=OFF \
    -DBUILD_PLUGIN_GREYHOUND=OFF \
    -DBUILD_PLUGIN_ICEBRIDGE=OFF \
    -DBUILD_PLUGIN_MATLAB=OFF \
    -DBUILD_PLUGIN_NITF=OFF \
    -DBUILD_PLUGIN_OPENSCENEGRAPH=OFF \
    -DBUILD_PLUGIN_RIVLIB=OFF

echo ""
echo "--- Building (${JOBS} jobs) — this takes ~5 minutes ---"
ninja -j"${JOBS}"

echo ""
echo "--- Installing to ${INSTALL_PREFIX} ---"
sudo ninja install
sudo ldconfig

# --- Verify no stale libproj.so.22 or libgdal.so.30 links ---
echo ""
echo "--- Verifying library links are clean ---"
BAD_LIBS=$(ldd "${INSTALL_PREFIX}/bin/pdal" | grep -E "libproj\.so\.22|libgdal\.so\.30" || true)
if [ -n "${BAD_LIBS}" ]; then
    echo "ERROR: pdal still links against conflicting libraries:"
    echo "${BAD_LIBS}"
    echo "Something is wrong with the GDAL/PROJ pin above — do not use this build."
    exit 1
fi
echo "OK — no libproj.so.22 or libgdal.so.30 in pdal's link set."

echo ""
echo "--- PDAL system install ---"
pdal --version

# --- Install Python bindings into venv ---
echo ""
echo "--- Installing pdal Python package into ${VENV} ---"
"${VENV}/bin/pip" install --upgrade pip
"${VENV}/bin/pip" install pdal

echo ""
echo "--- Verifying Python bindings ---"
"${VENV}/bin/python" -c "import pdal; print(f'pdal Python: {pdal.__version__}')"

echo ""
echo "=== Done. PDAL ${PDAL_VERSION} installed cleanly (GDAL 3.8 / PROJ 9). ==="
