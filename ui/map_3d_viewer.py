"""
ui/map_3d_viewer.py
-------------------
Hochleistungs-OpenGL 3D-Viewer auf Basis von VisPy.
- GPU-beschleunigtes Rendern von Millionen Punkten.
- Interaktive Werkzeuge: Polygon-Zuschnitt (Cropping) & Profilschnitte (Cross-Sections).
- Dynamische Farbschemata (Z-Höhengradient & ASPRS-Klassifikation).
"""

from typing import Optional, Tuple
from matplotlib import path as mpl_path
import numpy as np
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QButtonGroup,
    QDoubleSpinBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)
from vispy import scene
from vispy.color import Colormap


class FastPointCloudViewer(QWidget):
    """Hochleistungs-OpenGL 3D-Viewer mit interaktiver geodätischer Bearbeitung."""

    points_clipped_signal = pyqtSignal(np.ndarray)
    cross_section_generated_signal = pyqtSignal(np.ndarray, float)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

        self.raw_coords = np.empty((0, 3), dtype=np.float32)
        self.active_coords = np.empty((0, 3), dtype=np.float32)
        self.classifications = np.empty((0,), dtype=np.uint8)
        self.center_offset = np.zeros(3, dtype=np.float32)

        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # 1. شريط الأدوات العلوي للتحكم والتحرير
        toolbar_group = QGroupBox("3D-Werkzeuge & Geodätische Analyse")
        tb_layout = QHBoxLayout(toolbar_group)

        self.btn_reset_view = QPushButton("Ansicht Reset")
        self.btn_reset_data = QPushButton("Filter Reset")

        self.rb_color_height = QRadioButton("Höhengradient")
        self.rb_color_class = QRadioButton("ASPRS Klassen")
        self.rb_color_height.setChecked(True)

        color_group = QButtonGroup(self)
        color_group.addButton(self.rb_color_height)
        color_group.addButton(self.rb_color_class)

        lbl_thickness = QLabel("Schnittbreite (m):")
        self.spin_section_width = QDoubleSpinBox()
        self.spin_section_width.setRange(0.1, 50.0)
        self.spin_section_width.setValue(1.0)
        self.spin_section_width.setSingleStep(0.5)

        self.btn_apply_clip = QPushButton("Polygon-Zuschnitt")
        self.btn_cross_section = QPushButton("Profilschnitt")

        tb_layout.addWidget(self.btn_reset_view)
        tb_layout.addWidget(self.btn_reset_data)
        tb_layout.addWidget(self.rb_color_height)
        tb_layout.addWidget(self.rb_color_class)
        tb_layout.addWidget(lbl_thickness)
        tb_layout.addWidget(self.spin_section_width)
        tb_layout.addWidget(self.btn_apply_clip)
        tb_layout.addWidget(self.btn_cross_section)

        layout.addWidget(toolbar_group)

        # 2. محرك VisPy SceneCanvas
        self.canvas = scene.SceneCanvas(
            keys="interactive", show=True, bgcolor="#020617"
        )
        layout.addWidget(self.canvas.native)

        self.view = self.canvas.central_widget.add_view()
        self.view.camera = scene.cameras.TurntableCamera(
            fov=45, elevation=30, azimuth=45
        )

        # عناصر الرسم الأساسية
        self.grid = scene.visuals.GridLines(parent=self.view.scene, color=(0.2, 0.3, 0.4, 0.5))
        self.markers = scene.visuals.Markers(parent=self.view.scene)
        self.colormap_height = Colormap(["#1e3a8a", "#0284c7", "#10b981", "#facc15", "#dc2626"])

        # ربط الأحداث
        self.btn_reset_view.clicked.connect(self._reset_camera)
        self.btn_reset_data.clicked.connect(self._reset_data)
        self.rb_color_height.toggled.connect(self._update_colors)
        self.rb_color_class.toggled.connect(self._update_colors)
        self.btn_apply_clip.clicked.connect(self._demo_polygon_clip)
        self.btn_cross_section.clicked.connect(self._demo_generate_cross_section)

    def load_points(
        self,
        coords: np.ndarray,
        classifications: Optional[np.ndarray] = None
    ) -> None:
        pts = np.asarray(coords, dtype=np.float32)
        if pts.ndim != 2 or pts.shape[1] < 3:
            raise ValueError("Eingabekoordinaten müssen ein (N, 3) NumPy-Array sein.")

        if len(pts) == 0:
            return

        self.raw_coords = pts.copy()
        self.active_coords = pts.copy()

        if classifications is not None and len(classifications) == len(pts):
            self.classifications = np.asarray(classifications, dtype=np.uint8)
        else:
            self.classifications = np.ones(len(pts), dtype=np.uint8) * 2

        self.center_offset = np.mean(self.active_coords, axis=0)
        self._render_pointcloud()
        self._reset_camera()

    def _render_pointcloud(self) -> None:
        if len(self.active_coords) == 0:
            self.markers.set_data(pos=np.empty((0, 3)), face_color=np.empty((0, 4)))
            self.canvas.update()
            return

        centered_pts = self.active_coords - self.center_offset
        face_colors = self._compute_colors()

        self.markers.set_data(
            pos=centered_pts,
            face_color=face_colors,
            edge_color=None,
            size=2.5,
        )
        self.canvas.update()

    def _compute_colors(self) -> np.ndarray:
        n_pts = len(self.active_coords)
        if self.rb_color_height.isChecked():
            z_vals = self.active_coords[:, 2]
            z_min, z_max = np.min(z_vals), np.max(z_vals)
            z_range = z_max - z_min if (z_max - z_min) > 1e-6 else 1.0
            z_norm = (z_vals - z_min) / z_range
            return self.colormap_height.map(z_norm)
        else:
            # ASPRS Color Palette
            colors = np.ones((n_pts, 4), dtype=np.float32)
            class_map = {
                2: [0.55, 0.27, 0.07, 1.0],   # Ground (بني)
                3: [0.13, 0.55, 0.13, 1.0],   # Low Veg (أخضر فاتح)
                4: [0.00, 0.50, 0.00, 1.0],   # Medium Veg
                5: [0.00, 0.39, 0.00, 1.0],   # High Veg (أخضر غامق)
                6: [0.86, 0.08, 0.24, 1.0],   # Building (أحمر)
            }
            for cls_id, col in class_map.items():
                mask = self.classifications == cls_id
                colors[mask] = col
            return colors

    def clip_by_polygon(self, polygon_2d: np.ndarray, keep_inside: bool = True) -> None:
        """قص سحابة النقاط عبر مضلع ثنائي الأبعاد."""
        if len(self.active_coords) == 0:
            return

        poly_path = mpl_path.Path(polygon_2d)
        xy_pts = self.active_coords[:, :2]
        inside_mask = poly_path.contains_points(xy_pts)

        mask = inside_mask if keep_inside else ~inside_mask
        self.active_coords = self.active_coords[mask]
        self.classifications = self.classifications[mask]

        self._render_pointcloud()
        self.points_clipped_signal.emit(self.active_coords)

    def extract_cross_section(
        self,
        start_pt: np.ndarray,
        end_pt: np.ndarray,
        buffer_width: float = 1.0
    ) -> Tuple[np.ndarray, float]:
        """استخراج مقطع عرضي (Distance vs Height) على مسار محدد."""
        line_vec = end_pt[:2] - start_pt[:2]
        line_len = float(np.linalg.norm(line_vec))
        if line_len == 0:
            return np.empty((0, 2)), 0.0

        line_unit = line_vec / line_len
        normal_vec = np.array([-line_unit[1], line_unit[0]])

        rel_pts = self.active_coords[:, :2] - start_pt[:2]
        dist_along = np.dot(rel_pts, line_unit)
        dist_perp = np.abs(np.dot(rel_pts, normal_vec))

        mask = (dist_along >= 0) & (dist_along <= line_len) & (dist_perp <= buffer_width / 2.0)
        section_coords = self.active_coords[mask]

        if len(section_coords) == 0:
            return np.empty((0, 2)), line_len

        section_2d = np.vstack((dist_along[mask], section_coords[:, 2])).T
        sort_idx = np.argsort(section_2d[:, 0])
        section_2d = section_2d[sort_idx]

        self.cross_section_generated_signal.emit(section_2d, line_len)
        return section_2d, line_len

    def _demo_polygon_clip(self) -> None:
        if len(self.active_coords) == 0:
            return
        x_min, x_max = np.min(self.active_coords[:, 0]), np.max(self.active_coords[:, 0])
        y_min, y_max = np.min(self.active_coords[:, 1]), np.max(self.active_coords[:, 1])

        dx, dy = (x_max - x_min) * 0.25, (y_max - y_min) * 0.25
        poly = np.array([
            [x_min + dx, y_min + dy],
            [x_max - dx, y_min + dy],
            [x_max - dx, y_max - dy],
            [x_min + dx, y_max - dy]
        ])
        self.clip_by_polygon(poly, keep_inside=True)

    def _demo_generate_cross_section(self) -> None:
        if len(self.active_coords) == 0:
            return
        start = np.min(self.active_coords, axis=0)
        end = np.max(self.active_coords, axis=0)
        self.extract_cross_section(start, end, buffer_width=self.spin_section_width.value())

    def _update_colors(self) -> None:
        if len(self.active_coords) > 0:
            self._render_pointcloud()

    def _reset_data(self) -> None:
        if len(self.raw_coords) > 0:
            self.load_points(self.raw_coords, self.classifications)

    def _reset_camera(self) -> None:
        if len(self.active_coords) == 0:
            return
        centered_pts = self.active_coords - self.center_offset
        max_bound = float(np.max(np.abs(centered_pts)) * 2.5)
        self.view.camera.center = (0, 0, 0)
        self.view.camera.depth_value = max_bound if max_bound > 0 else 10.0
        self.canvas.update()