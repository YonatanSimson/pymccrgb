""" Convenience functions for loading point clouds in various formats """

import os

import numpy as np

try:
    import pdal
except ImportError:
    pdal = None

DEFAULT_COLUMN_INDICES = range(6)
DEFAULT_COLUMN_NAMES = ["X", "Y", "Z", "Red", "Green", "Blue"]
DEFAULT_HEADER = "X,Y,Z,Red,Green,Blue"

# PLY property type to struct format and byte size
_PLY_DTYPE = {
    "float": ("f", 4),
    "double": ("d", 8),
    "int": ("i", 4),
    "uint": ("I", 4),
    "short": ("h", 2),
    "ushort": ("H", 2),
    "uchar": ("B", 1),
}


def read_ply(filename, userows=None, nrows=None):
    """Load a PLY point cloud into a numpy array [x, y, z, r, g, b].

    Supports binary_little_endian PLY with vertex element. Reads x, y, z
    and r, g, b if present (other properties are skipped). If RGB is
    missing, returns zeros for r, g, b so that mcc() can be used.

    Parameters
    ----------
    filename : str
        Path to the PLY file.
    userows : array-like, optional
        Row indices to load. Overrides nrows.
    nrows : int, optional
        Number of random rows to load. Ignored if userows is given.

    Returns
    -------
    np.ndarray
        Shape (n, 6) with columns X, Y, Z, Red, Green, Blue. RGB in [0, 1]
        if stored as float, or [0, 255] if stored as uchar.
    """
    with open(filename, "rb") as f:
        # Read header
        line = f.readline().decode("ascii").strip()
        if line != "ply":
            raise ValueError("Not a PLY file")
        fmt = None
        n_vertex = None
        prop_names = []
        prop_sizes = []
        while True:
            line = f.readline().decode("ascii").strip()
            if line == "end_header":
                break
            parts = line.split()
            if parts[0] == "format":
                if "binary_little_endian" in line:
                    fmt = "<"
                elif "binary_big_endian" in line:
                    fmt = ">"
                else:
                    raise ValueError("Only binary PLY is supported")
            elif parts[0] == "element" and parts[1] == "vertex":
                n_vertex = int(parts[2])
            elif parts[0] == "property":
                dtype_name = parts[1].lower()
                if dtype_name in _PLY_DTYPE:
                    code, size = _PLY_DTYPE[dtype_name]
                    prop_names.append(parts[2])
                    prop_sizes.append((code, size))
        if n_vertex is None:
            raise ValueError("No vertex element in PLY")
        vertex_size = sum(s[1] for s in prop_sizes)
        header_end = f.tell()
        # Read full binary block (for large files with nrows set, this uses ~36 bytes per vertex)
        f.seek(header_end)
        raw = np.fromfile(f, dtype=np.uint8, count=n_vertex * vertex_size)
    raw = raw.reshape(n_vertex, vertex_size)

    # Build columns for x,y,z and r,g,b (in that order)
    # PLY uses "r","g","b" or "red","green","blue"
    want = ["x", "y", "z", "red", "green", "blue", "r", "g", "b"]
    col_names = [p.lower() for p in prop_names]
    offset = 0
    collected = {}  # name -> 1d array
    for i, (code, size) in enumerate(prop_sizes):
        name = col_names[i] if i < len(col_names) else ""
        if name in want:
            if code == "f":
                col = np.frombuffer(
                    raw[:, offset : offset + size].tobytes(), dtype=np.dtype(fmt + "f")
                ).astype(np.float64).copy()
            elif code == "d":
                col = np.frombuffer(
                    raw[:, offset : offset + size].tobytes(), dtype=np.dtype(fmt + "d")
                ).astype(np.float64).copy()
            elif code == "B":
                col = np.asarray(raw[:, offset], dtype=np.float64)
            else:
                col = np.frombuffer(
                    raw[:, offset : offset + size].tobytes(),
                    dtype=np.dtype(fmt + code),
                ).astype(np.float64)
            collected[name] = col
        offset += size

    out = np.zeros((n_vertex, 6), dtype=np.float64)
    for i, key in enumerate(["x", "y", "z", "red", "green", "blue"]):
        if key in collected:
            out[:, i] = collected[key]
    for short, idx in [("r", 3), ("g", 4), ("b", 5)]:
        if short in collected and not np.any(out[:, idx]):
            out[:, idx] = collected[short]

    if userows is not None:
        out = out[np.asarray(userows), :]
    elif nrows is not None:
        nrows = min(int(nrows), n_vertex)
        userows = np.random.choice(n_vertex, size=nrows, replace=False)
        out = out[userows, :]
    return out


def read_data(filename, usecols=None, userows=None, nrows=None):
    """ Loads a point cloud as numpy array

    Parameters
    ----------
        filename: str
            Filename of text file containing point cloud

        usecols: list
            List of column indices (text file) or names (LAS file) to load
            Default: First six columns, e.g.,  (x, y, z, r, g, b)

        userows: list
            List of rows to load. Overrides nrows argument
            Default: All rows

        nrows: int
            Number of random rows to load. Ignored if userows is given.
            Default: Not used.

    Returns
    -------
        A data array of shape (nrows x ncols)
    """
    if filename.endswith(".csv") or filename.endswith(".txt"):
        if usecols is None:
            usecols = DEFAULT_COLUMN_INDICES
        data = read_txt(filename, usecols=usecols, userows=userows, nrows=nrows)
    elif filename.endswith(".las") or filename.endswith(".laz"):
        if usecols is None:
            usecols = DEFAULT_COLUMN_NAMES
        data = read_las(filename, usecols=usecols, userows=userows, nrows=nrows)
    elif filename.endswith(".ply"):
        data = read_ply(filename, userows=userows, nrows=nrows)
        if usecols is not None:
            data = data[:, usecols]
    else:
        raise ValueError(
            "Unsupported format provided. Please provide a CSV file"
            "(.txt or .csv), LAS/LAZ, or PLY file."
        )
    return data


def read_txt(filename, usecols=DEFAULT_COLUMN_INDICES, userows=None, nrows=None):
    """ Loads a point cloud from text file as numpy array

    Parameters
    ----------
        filename: str
            Filename of text file containing point cloud

        usecols: list
            List of column indices to load
            Default: First six columns, e.g.,  (x, y, z, r, g, b)

        userows: list
            List of rows to load. Overrides nrows argument
            Default: All rows

        nrows: int
            Number of random rows to load. Ignored if userows is given.
            Default: Not used.

    Returns
    -------
        A data array of shape (nrows x ncols)
    """

    if userows is None:
        with open(filename, "r") as f:
            for i, s in enumerate(f):
                pass
        nlines = i + 1
        if nrows is not None:
            nrows = int(nrows)
            userows = np.random.choice(nlines, size=nrows)
        else:
            userows = range(nlines)

    data = []
    with open(filename, "r") as f:
        for i, s in enumerate(f):
            if i in userows:
                row = s.split(",")
                row = np.asarray(row)
                row = row[usecols]
                data.append(row)
    return np.array(data)


def read_las(filename, usecols=DEFAULT_COLUMN_NAMES, userows=None, nrows=None):
    """Loads a point cloud from a LAS or LAZ file into a Numpy array

    Theoretically, any file with a PDAL reader can be read with read_las

    Parameters
    ----------
        filename: str
            Filename of LAS or LAZ file containing point cloud

        usecols: list
            List of column names to load
            Default: ['X', 'Y', 'Z', 'Red', 'Green', 'Blue']

        userows: list
            List of rows to load. Overrides nrows argument
            Default: All rows

        nrows: int
            Number of random rows to load. Ignored if userows is given.
            Default: Not used.

    Returns
    -------
        A data array of shape (nrows x ncols)
    """

    if pdal is None:
        raise ImportError("pdal is required to read LAS/LAZ files. Install with: pip install pdal")
    json = '{"pipeline": ["' + filename + '"]}'
    pipeline = pdal.Pipeline(json)


    _ = pipeline.execute()

    out = pipeline.arrays[0]
    if userows is None:
        if nrows is None:
            data = np.hstack([out[key].reshape(-1, 1) for key in usecols])
            return data
        nrows = int(nrows)
        userows = np.random.choice(out.shape[0], size=nrows)

    data = []
    for i in userows:
        point = []
        for key in usecols:
            point.append(out[key][i])
        data.append(point)

    ncols = len(usecols)
    data = np.array(data).reshape(nrows, ncols)

    return data


NODATA_DEM = -9999.0


def _ellipsoidal_to_vertical(x, y, z, horizontal_crs, vertical_crs):
    """Convert ellipsoidal heights to the given vertical CRS using PROJ. Returns z_orthometric.

    (x, y) are in horizontal_crs; z is ellipsoidal height. Converts via ETRS89 3D (4937)
    to compound CRS horizontal_crs + vertical_crs and returns the vertical component.
    Requires PROJ >= 9.2 (vertical CRS and geoid support).
    """
    try:
        from pyproj import Transformer
    except ImportError as e:
        raise ImportError(
            "pyproj is required for vertical conversion. Install with: pip install pyproj"
        ) from e
    trans_xy = Transformer.from_crs(horizontal_crs, "EPSG:4937", always_xy=True)
    target_compound = f"{horizontal_crs}+{vertical_crs}"
    trans_z = Transformer.from_crs("EPSG:4937", target_compound, always_xy=True)
    lon, lat, _ = trans_xy.transform(x, y, np.zeros_like(x))
    _, _, z_ortho = trans_z.transform(lon, lat, z)
    return np.asarray(z_ortho, dtype=np.float64)


def _convert_z_to_vertical_crs(data, horizontal_crs, vertical_crs):
    """Convert data[:, 2] from ellipsoidal to the given vertical_crs (e.g. EPSG:3900)."""
    if vertical_crs is None or horizontal_crs is None:
        return data
    x, y, z = data[:, 0], data[:, 1], data[:, 2]
    z_new = _ellipsoidal_to_vertical(x, y, z, horizontal_crs, vertical_crs)
    out = data.copy()
    out[:, 2] = z_new
    return out


def _write_dem_rasterio(data, filename, resolution=1, srs=None, vertical_crs=None):
    """Write DEM from points using rasterio (no PDAL/GDAL). Bins points by cell, mean Z."""
    try:
        import rasterio
        from rasterio.crs import CRS
        from rasterio.transform import from_bounds
    except ImportError as e:
        raise ImportError(
            "rasterio is required when PDAL/GDAL is unavailable. "
            "Install with: pip install rasterio"
        ) from e

    x = np.asarray(data[:, 0], dtype=np.float64)
    y = np.asarray(data[:, 1], dtype=np.float64)
    z = np.asarray(data[:, 2], dtype=np.float64)

    minx, maxx = x.min(), x.max()
    miny, maxy = y.min(), y.max()
    # Align extent to resolution so cells are regular
    minx = np.floor(minx / resolution) * resolution
    maxx = np.ceil(maxx / resolution) * resolution
    miny = np.floor(miny / resolution) * resolution
    maxy = np.ceil(maxy / resolution) * resolution

    width = int(np.round((maxx - minx) / resolution))
    height = int(np.round((maxy - miny) / resolution))
    if width <= 0 or height <= 0:
        raise ValueError("Point cloud extent too small for resolution.")

    col = np.clip(
        np.floor((x - minx) / resolution).astype(np.intp), 0, width - 1
    )
    row = np.clip(
        np.floor((maxy - y) / resolution).astype(np.intp), 0, height - 1
    )
    lin = row * width + col
    n_cells = height * width
    sum_z = np.bincount(lin, weights=z, minlength=n_cells)
    count = np.bincount(lin, minlength=n_cells)
    mean_z = np.where(
        count > 0,
        sum_z / count,
        NODATA_DEM,
    )
    grid = mean_z.astype(np.float32).reshape(height, width)

    transform = from_bounds(minx, miny, maxx, maxy, width, height)
    crs = CRS.from_string(srs) if srs else None
    if vertical_crs:
        band_descriptions = [f"height (m), {vertical_crs}"]
    else:
        band_descriptions = ["ellipsoidal height (m)"]

    with rasterio.open(
        filename,
        "w",
        driver="GTiff",
        height=height,
        width=width,
        count=1,
        dtype=np.float32,
        crs=crs,
        transform=transform,
        nodata=NODATA_DEM,
    ) as dst:
        dst.write(grid, 1)
        if band_descriptions:
            dst.descriptions = band_descriptions


def write_dem(
    data,
    filename,
    resolution=1,
    radius=None,
    srs=None,
    vertical_crs=None,
    horizontal_crs=None,
):
    """Write ground points to a DEM GeoTIFF. Uses PDAL when available; falls back to rasterio if PDAL/GDAL fails.

    Parameters
    ----------
    data : np.ndarray
        Ground points, shape (n, 3) or (n, 6); only X,Y,Z are used.
    filename : str
        Output path (e.g. .tif).
    resolution : float
        Raster cell size in X/Y units.
    radius : float, optional
        Search radius for interpolation (PDAL only); default resolution * sqrt(2).
    srs : str, optional
        Output horizontal CRS, e.g. "EPSG:2393" (KKJ Finland).
    vertical_crs : str, optional
        Vertical CRS for heights (e.g. "EPSG:3900"). When set, Z is converted from
        ellipsoidal to this datum (requires horizontal_crs and pyproj). When not set,
        height is left as ellipsoidal.
    horizontal_crs : str, optional
        CRS of (x, y); required when vertical_crs is set (for geoid lookup).
    """
    if radius is None:
        radius = resolution * np.sqrt(2)

    data = np.atleast_2d(data)
    if data.shape[1] < 3:
        raise ValueError("data must have at least 3 columns (X, Y, Z).")

    # If vertical_crs is None, leave height as ellipsoidal (no conversion)
    if vertical_crs and horizontal_crs:
        data = _convert_z_to_vertical_crs(data, horizontal_crs, vertical_crs)

    if pdal is not None:
        try:
            write_las(data, "temp.las")
            gdal_opts = (
                '"resolution": "'
                + str(resolution)
                + '", "radius": "'
                + str(radius)
                + '", "filename": "'
                + filename.replace("\\", "\\\\").replace('"', '\\"')
                + '", "data_type": "float", "nodata": '
                + str(NODATA_DEM)
            )
            if srs is not None:
                gdal_opts += (
                    ', "override_srs": "'
                    + str(srs).replace("\\", "\\\\").replace('"', '\\"')
                    + '"'
                )
            json_str = (
                '{"pipeline": [{"type": "readers.las", "filename": "temp.las"}, '
                '{"type": "writers.gdal", '
                + gdal_opts
                + "}]}"
            )
            pipeline = pdal.Pipeline(json_str)
            pipeline.execute()
            if os.path.exists("temp.las"):
                os.remove("temp.las")
            return
        except Exception:
            if os.path.exists("temp.las"):
                try:
                    os.remove("temp.las")
                except OSError:
                    pass
            # Fall through to rasterio

    _write_dem_rasterio(
        data,
        filename,
        resolution=resolution,
        srs=srs,
        vertical_crs=vertical_crs,
    )


def write_las(arr, filename):
    write_pdal(arr, filename, writer="writers.las")


def write_pdal(arr, filename, writer, header=DEFAULT_HEADER):
    if pdal is None:
        raise ImportError("pdal is required to write LAS files. Install with: pip install pdal")
    np.savetxt("temp.csv", arr, header=header, delimiter=",", comments="")

    json = (
        '{"pipeline": [{"type": "readers.text", "filename": "temp.csv"}, {"type": "'
        + writer
        + '", "filename": "'
        + filename
        + '"}]}'
    )
    pipeline = pdal.Pipeline(json)


    _ = pipeline.execute()

    os.remove("temp.csv")
