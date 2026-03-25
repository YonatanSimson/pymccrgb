"""
Calculate indices and other features from multi-channel point cloud data

Inputs are assumed to be n x 6 arrays with each row being x, y, z, r, g, b
"""

import numpy as np

from skimage.exposure import rescale_intensity

# sRGB-to-XYZ (D65) matrix
_SRGB_TO_XYZ = np.array(
    [[0.4124564, 0.3575761, 0.1804375],
     [0.2126729, 0.7151522, 0.0721750],
     [0.0193339, 0.1191920, 0.9503041]],
    dtype=np.float32,
)
_LAB_EPS = np.float32((6 / 29) ** 3)
_LAB_K   = np.float32((29 / 6) ** 2 / 3)
_LAB_OFF = np.float32(4 / 29)


def _rgb_to_lab(rgb):
    """Convert uint8 (n, 3) RGB array to CIE-Lab using vectorised float32 ops."""
    f = rgb.astype(np.float32) * np.float32(1 / 255)
    mask = f > np.float32(0.04045)
    f[mask]  = ((f[mask] + np.float32(0.055)) * np.float32(1 / 1.055)) ** np.float32(2.4)
    f[~mask] *= np.float32(1 / 12.92)
    xyz = f @ _SRGB_TO_XYZ.T
    xyz[:, 0] *= np.float32(1 / 0.95047)
    xyz[:, 2] *= np.float32(1 / 1.08883)
    t = np.where(xyz > _LAB_EPS, np.cbrt(xyz), _LAB_K * xyz + _LAB_OFF)
    L = np.float32(116) * t[:, 1] - np.float32(16)
    a = np.float32(500) * (t[:, 0] - t[:, 1])
    b = np.float32(200) * (t[:, 1] - t[:, 2])
    return np.stack([L, a, b], axis=1)


def calculate_color_features(data):
    """ Calculates color features related to the greenness of each point.

    The default features are [a, b, NGRDVI] where a and b are the green-red and
    blue-yellow coordinates of the CIE-Lab color space.

    Parameters
    ----------
        data: array
        An n x d array of input data. Rows are [x, y, z, r, g, b, ...]

    Returns
    -------
        An n x 3 array of features for each point.
    """

    rgb = rescale_intensity(data[:, 3:6], out_range="uint8").astype(np.uint8)
    lab = _rgb_to_lab(rgb)
    red = rgb[:, 0].astype(int).reshape(-1, 1)
    green = rgb[:, 1].astype(int).reshape(-1, 1)
    denom = (green + red).astype(float)
    denom[denom == 0] = np.nan
    ngrdvi = (green - red) / denom
    return np.hstack([lab[:, 1:3], ngrdvi])


def calculate_eigenvalue_features(data):
    raise NotImplementedError("This method has not yet been implemented.")


def calculate_ngrdvi(data):
    """ Calculates red-green difference index (NGRDVI) from color data

    Parameters
    ----------
        data: array
        An n x d array of input data. Rows are [x, y, z, r, g, b, ...]

    Returns
    -------
        An n x 1 array of NGRDVI values
    """

    rgb = rescale_intensity(data[:, 3:6], out_range="uint8").astype(np.uint8)
    red = rgb[:, 0].astype(int).reshape(-1, 1)
    green = rgb[:, 1].astype(int).reshape(-1, 1)

    denom = (green + red).astype(float)
    denom[denom == 0] = np.nan
    return (green - red) / denom



def calculate_vdvi(data):
    """ Calculates visual difference vegetation index (VDVI) from color data

    Parameters
    ----------
        data: array
        An n x d array of input data. Rows are [x, y, z, r, g, b, ...]

    Returns
    -------
        An n x 1 array of VDVI values
    """

    rgb = rescale_intensity(data[:, 3:6], out_range="uint8").astype(np.uint8)
    red = rgb[:, 0].reshape(-1, 1)
    green = rgb[:, 1].reshape(-1, 1)
    blue = rgb[:, 2].reshape(-1, 1)

    red = red.astype(int)
    green = green.astype(int)
    blue = blue.astype(int)
    denom = (2 * green + red + blue).astype(float)
    denom[denom == 0] = np.nan
    return (2 * green - red - blue) / denom
