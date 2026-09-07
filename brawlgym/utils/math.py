"""
A basic library for useful 2D mathematical operations.
"""

import numpy as np


def get_dist(x, y):
    return np.subtract(x, y)


def vecmag(vec):
    return np.linalg.norm(vec)


def unitvec(vec):
    norm = vecmag(vec)
    if norm == 0:
        return np.zeros_like(vec, dtype=np.float32)
    return np.divide(vec, norm)


def ray_directions(n_rays: int) -> np.ndarray:
    """
    Unit vectors for n rays spread evenly over the circle, starting along +x and going through
    +y (down, in screen coordinates). Shape (n_rays, 2).
    """
    angles = np.arange(n_rays, dtype=np.float64) * (2.0 * np.pi / n_rays)
    return np.stack([np.cos(angles), np.sin(angles)], axis=1)


def raycast(origin, directions: np.ndarray, segments: np.ndarray, max_range: float) -> np.ndarray:
    """
    Distance along each ray to the nearest segment, or inf if nothing is hit within max_range.

    :param origin: (x, y) the rays start from, or (R, 2) for one origin per ray.
    :param directions: (R, 2) unit direction per ray.
    :param segments: (S, 2, 2) line segments as ((x1, y1), (x2, y2)).
    :return: (R,) distances.
    """
    directions = np.asarray(directions, dtype=np.float64)
    hits = np.full(directions.shape[0], np.inf)
    if segments is None or len(segments) == 0:
        return hits
    segments = np.asarray(segments, dtype=np.float64)
    o = np.asarray(origin, dtype=np.float64).reshape(-1, 2)   # (1, 2) or (R, 2)

    a = segments[:, 0]                      # (S, 2)
    e = segments[:, 1] - segments[:, 0]     # (S, 2) segment vectors
    d = directions                          # (R, 2)

    # solve o + t*d = a + u*e for every (ray, segment) pair
    denom = d[:, None, 0] * e[None, :, 1] - d[:, None, 1] * e[None, :, 0]    # (R, S)
    ao = a[None, :, :] - o[:, None, :]                                       # (R or 1, S, 2)
    with np.errstate(divide="ignore", invalid="ignore"):
        t = (ao[..., 0] * e[None, :, 1] - ao[..., 1] * e[None, :, 0]) / denom
        u = (ao[..., 0] * d[:, None, 1] - ao[..., 1] * d[:, None, 0]) / denom
    valid = (np.abs(denom) > 1e-12) & (t >= 0.0) & (t <= max_range) & (u >= 0.0) & (u <= 1.0)
    t = np.where(valid, t, np.inf)
    return t.min(axis=1)
