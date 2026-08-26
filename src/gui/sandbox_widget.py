import sys
import os
import math
import webbrowser
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QComboBox, QSlider, QSizePolicy, QButtonGroup, QMessageBox
)
from PySide6.QtCore import Qt, QPointF, QPoint, QTimer, QSize
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QFont, QPolygonF, QLinearGradient, QTransform

from src.core.bundeslaender import BundeslaenderEngine
from src.tools.urban_tools import BuildingObject, RoadObject
from src.gis.real_tile_engine import GLOBAL_MAP_MANAGER

class Sandbox3DViewport(QWidget):
    def __init__(self, sandbox_ui, parent=None):
        super().__init__(parent)
        self.sandbox_ui = sandbox_ui
        self.setMinimumSize(500, 420)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.center_lat = 51.2277
        self.center_lon = 6.7735
        self.zoom_level = 14.5

        self.camera_pitch = 45.0
        self.camera_yaw = 0.0

        self.target_lat = self.center_lat
        self.target_lon = self.center_lon
        self.target_zoom = self.zoom_level

        self.flight_timer = QTimer(self)
        self.flight_timer.timeout.connect(self.step_flight_animation)

        self.last_mouse_pos = QPoint()
        self.setMouseTracking(True)
        self.cursor_pos = QPointF(0, 0)

        self.sun_hour = 14.0
        self.active_tool = "pan"
        self.basemap_provider = "topo"
        self.current_drawing_pts = []
        
        self.created_buildings = []
        self.created_roads = []
        
        GLOBAL_MAP_MANAGER.update_viewport.connect(self.update)

    def set_camera_preset(self, preset_name):
        if preset_name == "top":
            self.camera_pitch = 90.0
            self.camera_yaw = 0.0
        elif preset_name == "iso":
            self.camera_pitch = 45.0
            self.camera_yaw = 35.0
        elif preset_name == "front":
            self.camera_pitch = 20.0
            self.camera_yaw = 0.0
        self.sandbox_ui.sync_slider_angles(self.camera_pitch, self.camera_yaw)
        self.update()

    def fly_to(self, lat, lon, zoom):
        self.target_lat = lat
        self.target_lon = lon
        self.target_zoom = float(zoom)
        self.flight_timer.start(16)

    def step_flight_animation(self):
        d_lat = (self.target_lat - self.center_lat) * 0.12
        d_lon = (self.target_lon - self.center_lon) * 0.12
        d_zoom = (self.target_zoom - self.zoom_level) * 0.12

        self.center_lat += d_lat
        self.center_lon += d_lon
        self.zoom_level += d_zoom

        if abs(d_lat) < 0.0001 and abs(d_lon) < 0.0001 and abs(d_zoom) < 0.01:
            self.center_lat = self.target_lat
            self.center_lon = self.target_lon
            self.zoom_level = self.target_zoom
            self.flight_timer.stop()

        self.update()

    def project_3d_point(self, x, y, z, cx, cy):
        rad_yaw = math.radians(self.camera_yaw)
        rad_pitch = math.radians(self.camera_pitch)

        rx = x * math.cos(rad_yaw) - y * math.sin(rad_yaw)
        ry = x * math.sin(rad_yaw) + y * math.cos(rad_yaw)

        proj_x = cx + rx
        proj_y = cy + ry * math.sin(rad_pitch) - z * math.cos(rad_pitch)
        return QPointF(proj_x, proj_y)

    def mousePressEvent(self, event):
        self.last_mouse_pos = event.pos()
        w, h = self.width(), self.height()
        cx, cy = w / 2, h / 2
        click_x = event.position().x() - cx
        click_y = event.position().y() - cy

        if event.button() == Qt.LeftButton:
            if self.active_tool in ["building", "road"]:
                self.current_drawing_pts.append((click_x, click_y))
                self.update()
        elif event.button() == Qt.RightButton:
            if self.active_tool == "building" and len(self.current_drawing_pts) >= 3:
                b_name = f"3D-Bauwerk #{len(self.created_buildings)+1}"
                self.created_buildings.append(BuildingObject(self.current_drawing_pts, height=30.0, name=b_name))
                self.current_drawing_pts = []
                self.sandbox_ui.update_sandbox_telemetry()
                self.update()
            elif self.active_tool == "road" and len(self.current_drawing_pts) >= 2:
                r_name = f"Trasse #{len(self.created_roads)+1}"
                self.created_roads.append(RoadObject(self.current_drawing_pts, width=14.0, name=r_name))
                self.current_drawing_pts = []
                self.sandbox_ui.update_sandbox_telemetry()
                self.update()

    def mouseMoveEvent(self, event):
        self.cursor_pos = event.position()
        delta = event.pos() - self.last_mouse_pos

        if event.buttons() & Qt.LeftButton and self.active_tool == "pan":
            scale = 360.0 / (256.0 * (2 ** self.zoom_level))
            self.center_lon -= delta.x() * scale
            self.center_lat += delta.y() * scale * math.cos(math.radians(self.center_lat))
            self.target_lat = self.center_lat
            self.target_lon = self.center_lon
            self.update()

        elif event.buttons() & Qt.RightButton and self.active_tool == "pan":
            self.camera_yaw = (self.camera_yaw + delta.x() * 0.5) % 360.0
            self.camera_pitch = max(10.0, min(90.0, self.camera_pitch - delta.y() * 0.3))
            self.sandbox_ui.sync_slider_angles(self.camera_pitch, self.camera_yaw)
            self.update()

        self.last_mouse_pos = event.pos()
        self.update()

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        max_z = 16.2 if self.basemap_provider == "topo" else 19.0
        if delta > 0:
            self.zoom_level = min(max_z, self.zoom_level + 0.3)
        else:
            self.zoom_level = max(4.0, self.zoom_level - 0.3)
        self.target_zoom = self.zoom_level
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        w, h = self.width(), self.height()
        cx, cy = w / 2, h / 2

        # 1. رسم بلاطات الخريطة
        self.render_real_map_tiles(painter, w, h, cx, cy)

        # 2. رسم الطرق
        self.render_roads_3d(painter, cx, cy)

        # 3. رسم المباني 3D
        self.render_buildings_3d(painter, cx, cy)

        # 4. رسم المضلع النشط
        if self.current_drawing_pts:
            painter.setPen(QPen(QColor("#10b981"), 2, Qt.DashLine))
            painter.setBrush(QBrush(QColor(16, 185, 129, 35)))
            poly = QPolygonF([QPointF(cx + p[0], cy + p[1]) for p in self.current_drawing_pts])
            if len(self.current_drawing_pts) >= 3:
                painter.drawPolygon(poly)
            else:
                for i in range(len(self.current_drawing_pts) - 1):
                    painter.drawLine(QPointF(cx + self.current_drawing_pts[i][0], cy + self.current_drawing_pts[i][1]),
                                     QPointF(cx + self.current_drawing_pts[i+1][0], cy + self.current_drawing_pts[i+1][1]))
            painter.drawLine(QPointF(cx + self.current_drawing_pts[-1][0], cy + self.current_drawing_pts[-1][1]), self.cursor_pos)

        # 5. شريط HUD منسق داخل صندوق شبه شفاف
        self.render_tactical_hud(painter, w, h)

    def render_tactical_hud(self, painter, w, h):
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(4, 7, 13, 210)))
        painter.drawRoundedRect(12, 12, 380, 28, 6, 6)
        painter.drawRoundedRect(w - 360, 12, 348, 28, 6, 6)

        painter.setFont(QFont("Consolas", 9, QFont.Bold))
        painter.setPen(QColor("#00d2ff"))
        painter.drawText(22, 30, f"📐 PITCH: {self.camera_pitch:.0f}° | YAW: {self.camera_yaw:.0f}° | ☀️ {int(self.sun_hour):02d}:00")

        painter.setPen(QColor("#10b981"))
        painter.drawText(w - 348, 30, "🖱️ [R-DRAG] 360° Orbit | [L-DRAG] Pan")

    def render_real_map_tiles(self, painter, w, h, cx, cy):
        z = int(round(self.zoom_level))
        if self.basemap_provider == "topo" and z > 16:
            z = 16

        n = 2.0 ** z
        lat_rad = math.radians(self.center_lat)
        center_x_tile = (self.center_lon + 180.0) / 360.0 * n
        center_y_tile = (1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n

        tile_size = 256.0 * (2.0 ** (self.zoom_level - z))
        tiles_x = int(math.ceil(w / tile_size)) + 2
        tiles_y = int(math.ceil(h / tile_size)) + 2

        start_x = int(math.floor(center_x_tile - tiles_x / 2))
        start_y = int(math.floor(center_y_tile - tiles_y / 2))

        for tx in range(start_x, start_x + tiles_x + 1):
            for ty in range(start_y, start_y + tiles_y + 1):
                if 0 <= tx < int(n) and 0 <= ty < int(n):
                    px = cx + (tx - center_x_tile) * tile_size
                    py = cy + (ty - center_y_tile) * tile_size

                    pix = GLOBAL_MAP_MANAGER.get_tile(z, tx, ty, self.basemap_provider)
                    if pix:
                        painter.drawPixmap(int(px), int(py), int(tile_size), int(tile_size), pix)
                    else:
                        painter.fillRect(int(px), int(py), int(tile_size), int(tile_size), QColor("#081426"))
                        painter.setPen(QPen(QColor("#0e2444"), 1))
                        painter.drawRect(int(px), int(py), int(tile_size), int(tile_size))

    def render_roads_3d(self, painter, cx, cy):
        for road in self.created_roads:
            if len(road.points) >= 2:
                painter.setPen(QPen(QColor("#1e293b"), road.width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
                for i in range(len(road.points) - 1):
                    p1 = self.project_3d_point(road.points[i][0], road.points[i][1], 0, cx, cy)
                    p2 = self.project_3d_point(road.points[i+1][0], road.points[i+1][1], 0, cx, cy)
                    painter.drawLine(p1, p2)

                painter.setPen(QPen(QColor("#f59e0b"), 2, Qt.DashLine))
                for i in range(len(road.points) - 1):
                    p1 = self.project_3d_point(road.points[i][0], road.points[i][1], 0, cx, cy)
                    p2 = self.project_3d_point(road.points[i+1][0], road.points[i+1][1], 0, cx, cy)
                    painter.drawLine(p1, p2)

    def render_buildings_3d(self, painter, cx, cy):
        sun_rad = math.radians((self.sun_hour - 12.0) * 15.0)
        shadow_dx = math.sin(sun_rad) * 20.0
        shadow_dy = math.cos(sun_rad) * 12.0

        for b in self.created_buildings:
            pts = b.points
            if len(pts) >= 3:
                painter.setPen(Qt.NoPen)
                painter.setBrush(QBrush(QColor(0, 0, 0, 110)))
                poly_shadow = QPolygonF([self.project_3d_point(p[0] + shadow_dx, p[1] + shadow_dy, 0, cx, cy) for p in pts])
                painter.drawPolygon(poly_shadow)

                painter.setPen(QPen(QColor("#0284c7"), 1.4))
                painter.setBrush(QBrush(QColor(14, 165, 233, 110)))
                for i in range(len(pts)):
                    p_curr = pts[i]
                    p_next = pts[(i+1)%len(pts)]
                    
                    p_b1 = self.project_3d_point(p_curr[0], p_curr[1], 0, cx, cy)
                    p_b2 = self.project_3d_point(p_next[0], p_next[1], 0, cx, cy)
                    p_t2 = self.project_3d_point(p_next[0], p_next[1], b.height, cx, cy)
                    p_t1 = self.project_3d_point(p_curr[0], p_curr[1], b.height, cx, cy)

                    painter.drawPolygon(QPolygonF([p_b1, p_b2, p_t2, p_t1]))

                painter.setPen(QPen(QColor("#38bdf8"), 1.8))
                painter.setBrush(QBrush(QColor(56, 189, 248, 170)))
                poly_top = QPolygonF([self.project_3d_point(p[0], p[1], b.height, cx, cy) for p in pts])
                painter.drawPolygon(poly_top)

                p_label = self.project_3d_point(pts[0][0], pts[0][1], b.height + 4, cx, cy)
                painter.setFont(QFont("Segoe UI", 8, QFont.Bold))
                painter.setPen(QColor("#ffffff"))
                painter.drawText(int(p_label.x()), int(p_label.y()), b.name)

class SandboxWorkspaceWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        bar = QFrame()
        bar.setStyleSheet("background: #04070d; border: 1px solid #151e2e; border-radius: 8px; padding: 6px 12px;")
        b_layout = QHBoxLayout(bar)
        b_layout.setContentsMargins(0, 0, 0, 0)
        b_layout.setSpacing(8)

        b_layout.addWidget(QLabel("Bundesland:"))
        self.cb_states = QComboBox()
        for code, info in BundeslaenderEngine.STATES.items():
            self.cb_states.addItem(f"{code} - {info['name']}", (info["lat"], info["lon"], info["zoom"]))
        self.cb_states.currentIndexChanged.connect(self.on_state_change)
        b_layout.addWidget(self.cb_states)

        b_layout.addWidget(QLabel("Karte:"))
        self.cb_map = QComboBox()
        self.cb_map.addItems(["📐 Topo Relief", "🛰️ Satellit (ESRI)", "🗺️ Straßen (OSM)"])
        self.cb_map.currentIndexChanged.connect(self.on_map_provider_change)
        b_layout.addWidget(self.cb_map)

        self.btn_pan = QPushButton("✋ Pan/Nav")
        self.btn_pan.setCheckable(True)
        self.btn_pan.setChecked(True)
        self.btn_pan.clicked.connect(lambda: self.set_tool("pan"))
        b_layout.addWidget(self.btn_pan)

        self.btn_bld = QPushButton("🏢 3D Gebäude")
        self.btn_bld.setCheckable(True)
        self.btn_bld.clicked.connect(lambda: self.set_tool("building"))
        b_layout.addWidget(self.btn_bld)

        self.btn_road = QPushButton("🛣️ Straße")
        self.btn_road.setCheckable(True)
        self.btn_road.clicked.connect(lambda: self.set_tool("road"))
        b_layout.addWidget(self.btn_road)

        btn_top = QPushButton("📐 Top")
        btn_top.clicked.connect(lambda: self.viewport.set_camera_preset("top"))
        b_layout.addWidget(btn_top)

        btn_iso = QPushButton("🧊 Iso 3D")
        btn_iso.clicked.connect(lambda: self.viewport.set_camera_preset("iso"))
        b_layout.addWidget(btn_iso)

        btn_solar = QPushButton("⚡ Solar")
        btn_solar.clicked.connect(self.action_solar_calc)
        b_layout.addWidget(btn_solar)

        layout.addWidget(bar)

        body_box = QHBoxLayout()
        self.viewport = Sandbox3DViewport(self)
        body_box.addWidget(self.viewport, 4)

        side_card = QFrame()
        side_card.setStyleSheet("background: #04070d; border: 1px solid #151e2e; border-radius: 8px; padding: 14px;")
        side_card.setMinimumWidth(260)
        sc_layout = QVBoxLayout(side_card)
        sc_layout.setSpacing(10)

        lbl_head = QLabel("🌍 3D CAMERA & PERSPECTIVE")
        lbl_head.setStyleSheet("color: #00d2ff; font-weight: 900; font-family: Consolas; font-size: 12px;")
        sc_layout.addWidget(lbl_head)

        sc_layout.addWidget(QLabel("Kamera-Neigung (Pitch):"))
        self.slider_pitch = QSlider(Qt.Horizontal)
        self.slider_pitch.setRange(10, 90)
        self.slider_pitch.setValue(45)
        self.slider_pitch.valueChanged.connect(self.on_pitch_change)
        sc_layout.addWidget(self.slider_pitch)

        sc_layout.addWidget(QLabel("360° Drehung (Yaw):"))
        self.slider_yaw = QSlider(Qt.Horizontal)
        self.slider_yaw.setRange(0, 360)
        self.slider_yaw.setValue(0)
        self.slider_yaw.valueChanged.connect(self.on_yaw_change)
        sc_layout.addWidget(self.slider_yaw)

        sc_layout.addWidget(QLabel("☀️ Sonnenstand (Uhrzeit):"))
        self.slider_sun = QSlider(Qt.Horizontal)
        self.slider_sun.setRange(6, 20)
        self.slider_sun.setValue(14)
        self.slider_sun.valueChanged.connect(self.on_sun_changed)
        sc_layout.addWidget(self.slider_sun)

        sc_layout.addSpacing(10)
        lbl_stats_title = QLabel("📊 CREATIVE METRICS")
        lbl_stats_title.setStyleSheet("color: #00d2ff; font-weight: 900; font-family: Consolas; font-size: 12px;")
        sc_layout.addWidget(lbl_stats_title)

        self.lbl_bld_count = QLabel("● Gebäude: 0 Einheiten")
        self.lbl_bld_count.setStyleSheet("color: #f8fafc; font-family: Consolas; font-weight: bold;")
        self.lbl_solar_pot = QLabel("● Solar-Potenzial: 0.0 MWh/a")
        self.lbl_solar_pot.setStyleSheet("color: #10b981; font-family: Consolas; font-weight: bold;")
        self.lbl_co2_sav = QLabel("● CO2-Einsparung: 0.0 t/a")
        self.lbl_co2_sav.setStyleSheet("color: #38bdf8; font-family: Consolas; font-weight: bold;")

        sc_layout.addWidget(self.lbl_bld_count)
        sc_layout.addWidget(self.lbl_solar_pot)
        sc_layout.addWidget(self.lbl_co2_sav)
        sc_layout.addStretch()

        btn_reset = QPushButton("🗑️ Szene Zurücksetzen")
        btn_reset.clicked.connect(self.reset_scene)
        sc_layout.addWidget(btn_reset)
        body_box.addWidget(side_card, 1)

        layout.addLayout(body_box)

    def set_tool(self, t):
        self.viewport.active_tool = t
        self.btn_pan.setChecked(t == "pan")
        self.btn_bld.setChecked(t == "building")
        self.btn_road.setChecked(t == "road")
        self.viewport.current_drawing_pts = []
        self.viewport.update()

    def sync_slider_angles(self, pitch, yaw):
        self.slider_pitch.blockSignals(True)
        self.slider_yaw.blockSignals(True)
        self.slider_pitch.setValue(int(pitch))
        self.slider_yaw.setValue(int(yaw))
        self.slider_pitch.blockSignals(False)
        self.slider_yaw.blockSignals(False)

    def on_pitch_change(self, val):
        self.viewport.camera_pitch = float(val)
        self.viewport.update()

    def on_yaw_change(self, val):
        self.viewport.camera_yaw = float(val)
        self.viewport.update()

    def on_map_provider_change(self, idx):
        providers = ["topo", "satellite", "osm"]
        self.viewport.basemap_provider = providers[idx]
        if self.viewport.basemap_provider == "topo" and self.viewport.zoom_level > 16.2:
            self.viewport.zoom_level = 16.0
            self.viewport.target_zoom = 16.0
        self.viewport.update()

    def on_sun_changed(self, val):
        self.viewport.sun_hour = float(val)
        self.viewport.update()

    def on_state_change(self, idx):
        lat, lon, zoom = self.cb_states.itemData(idx)
        self.viewport.fly_to(lat, lon, zoom)

    def update_sandbox_telemetry(self):
        b_count = len(self.viewport.created_buildings)
        total_mwh = b_count * 47.5
        co2_t = total_mwh * 0.48
        self.lbl_bld_count.setText(f"● Gebäude: {b_count} Einheiten")
        self.lbl_solar_pot.setText(f"● Solar-Potenzial: {total_mwh:,.1f} MWh/a")
        self.lbl_co2_sav.setText(f"● CO2-Einsparung: {co2_t:,.1f} t/a")

    def action_solar_calc(self):
        count = len(self.viewport.created_buildings)
        if count == 0:
            QMessageBox.information(self, "Solar-Analyse", "Bitte zeichnen Sie zuerst 3D-Gebäude mit dem Werkzeug '🏢 3D Gebäude'.")
            return
        QMessageBox.information(
            self, "Rooftop Solar Potential",
            f"✓ Dachflächen-Photovoltaik Analyse:\n\n"
            f"● Berechnete Solardachfläche: {count*380} m²\n"
            f"● Spitzenleistung (kWp): {count*76.0} kWp\n"
            f"● Jahresertrag: {count*47.5:,.1f} MWh/Jahr"
        )

    def reset_scene(self):
        self.viewport.created_buildings = []
        self.viewport.created_roads = []
        self.viewport.current_drawing_pts = []
        self.update_sandbox_telemetry()
        self.viewport.update()
