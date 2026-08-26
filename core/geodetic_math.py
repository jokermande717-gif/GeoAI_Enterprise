import numpy as np
import pandas as pd
from scipy.spatial import Delaunay
import pyproj
from typing import Tuple, Union, List, Dict, Any


def calculate_gauss_elling_area(points: Union[np.ndarray, List[Tuple[float, float]]]) -> float:
    """Berechnet die exakte Fläche eines Polygons nach der Gaußschen Trapezformel (Elling'sche Formel).

    In der deutschen Geodäsie gilt:
    x = Hochwert (Northing), y = Rechtswert (Easting).
    Formel: 2 * A = sum(x_i * (y_{i+1} - y_{i-1}))

    Args:
        points: Array oder Liste von (x, y) oder (Easting, Northing) Koordinaten.

    Returns:
        Absolute Fläche in Quadratmetern (m²).
    """
    pts = np.asarray(points, dtype=np.float64)
    if pts.ndim != 2 or pts.shape[1] < 2:
        raise ValueError("Eingabepunkte müssen eine N x 2 Matrix sein (X, Y).")

    if not np.allclose(pts[0], pts[-1]):
        pts = np.vstack([pts, pts[0]])

    x = pts[:, 0]
    y = pts[:, 1]

    y_next = np.roll(y, -1)
    y_prev = np.roll(y, 1)

    double_area = np.sum(x * (y_next - y_prev))
    return float(np.abs(double_area) / 2.0)


def calculate_reb_22013_volumes(
    data: Union[pd.DataFrame, np.ndarray], base_z: float
) -> Dict[str, float]:
    """Berechnet Abtrag-, Auftrag- und Nettovolumina aus 3D-Punktmengen gemäß REB 22.013.

    Verwendet eine 2D-Delaunay-Triangulierung (DGM) und führt eine exakte analytische
    Prismen- und Tetraeder-Volumenintegration für jedes Dreieck bezüglich der Bezugebene (base_z) durch.
    """
    if isinstance(data, pd.DataFrame):
        coords = data[["x", "y", "z"]].to_numpy(dtype=np.float64)
    else:
        coords = np.asarray(data, dtype=np.float64)

    if coords.shape[1] < 3:
        raise ValueError("Die Punktmenge muss 3D-Koordinaten (X, Y, Z) enthalten.")

    xy = coords[:, :2]
    z = coords[:, 2] - float(base_z)

    tri = Delaunay(xy)
    simplices = tri.simplices

    total_cut = 0.0
    total_fill = 0.0
    total_area = 0.0

    for sim in simplices:
        p1, p2, p3 = xy[sim[0]], xy[sim[1]], xy[sim[2]]
        h1, h2, h3 = z[sim[0]], z[sim[1]], z[sim[2]]

        area_2d = 0.5 * np.abs(
            p1[0] * (p2[1] - p3[1]) + p2[0] * (p3[1] - p1[1]) + p3[0] * (p1[1] - p2[1])
        )
        total_area += area_2d

        if area_2d < 1e-12:
            continue

        heights = np.array([h1, h2, h3], dtype=np.float64)

        if np.all(heights >= 0):
            v = area_2d * np.mean(heights)
            total_cut += v

        elif np.all(heights <= 0):
            v = area_2d * np.abs(np.mean(heights))
            total_fill += v

        else:
            sort_idx = np.argsort(heights)
            h_sorted = heights[sort_idx]
            h0, h1_h, h2_h = h_sorted[0], h_sorted[1], h_sorted[2]

            if h1_h <= 0:
                f_02 = -h0 / (h2_h - h0)
                f_12 = -h1_h / (h2_h - h1_h)

                area_cut = area_2d * (1.0 - f_02) * (1.0 - f_12)
                vol_cut = (area_cut * h2_h) / 3.0

                total_mean_abs = np.abs(np.mean(heights))
                vol_total_abs = area_2d * total_mean_abs
                vol_fill = vol_total_abs - vol_cut

                total_cut += vol_cut
                total_fill += max(0.0, vol_fill)

            else:
                f_01 = -h0 / (h1_h - h0)
                f_02 = -h0 / (h2_h - h0)

                area_fill = area_2d * f_01 * f_02
                vol_fill = (area_fill * np.abs(h0)) / 3.0

                total_mean_abs = np.mean(heights)
                vol_total_abs = area_2d * total_mean_abs
                vol_cut = vol_total_abs + vol_fill

                total_fill += vol_fill
                total_cut += max(0.0, vol_cut)

    return {
        "cut_volume": float(total_cut),
        "fill_volume": float(total_fill),
        "net_volume": float(total_cut - total_fill),
        "total_area_2d": float(total_area),
    }


def transform_crs(
    x_array: Union[np.ndarray, List[float]],
    y_array: Union[np.ndarray, List[float]],
    source_epsg: int,
    target_epsg: int,
) -> Tuple[np.ndarray, np.ndarray]:
    """Transformiert Koordinatenfelder hochperformant zwischen zwei EPSG-Referenzsystemen."""
    x_arr = np.asarray(x_array, dtype=np.float64)
    y_arr = np.asarray(y_array, dtype=np.float64)

    transformer = pyproj.Transformer.from_crs(
        f"EPSG:{source_epsg}", f"EPSG:{target_epsg}", always_xy=True
    )

    x_trans, y_trans = transformer.transform(x_arr, y_arr)
    return np.asarray(x_trans, dtype=np.float64), np.asarray(y_trans, dtype=np.float64)