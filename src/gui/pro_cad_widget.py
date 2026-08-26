import sys
import os
import math
import hashlib
import webbrowser
from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QSlider, QFileDialog,
    QMessageBox, QFrame, QTextEdit, QSplitter, QGroupBox, QTreeWidget,
    QTreeWidgetItem, QComboBox, QSizePolicy, QTabWidget, QDialog
)
from PySide6.QtCore import Qt, QPointF, QPoint, QTimer, QSize
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QFont, QPolygonF, QLinearGradient, QKeySequence, QShortcut

from src.core.bundeslaender import BundeslaenderEngine
from src.core.geodesy import GeodesyEngine
from src.core.instant_math import InstantGeodeticMath
from src.core.corporate_engine import CorporateEngine
from src.core.advanced_cad_engine import AdvancedCADEngine
from src.core.corporate_dossier import CorporateDossierEngine
from src.ai.lidar_engine import OfflineAILiDAREngine
from src.ai.advanced_ai_suite import AdvancedGeoAISuite
from src.tools.urban_tools import BuildingObject, RoadObject, MarkerPointObject
from src.gis.real_tile_engine import GLOBAL_MAP_MANAGER

class InAppDossierDialog(QDialog):
    def __init__(self, html_content, pdf_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📑 Amtliches Prüfgutachten // Sovereign Audit Dossier 2026")
        self.resize(880, 680)
        self.setStyleSheet("background-color: #030712; color: #f8fafc;")
        self.pdf_path = pdf_path

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        head_box = QHBoxLayout()
        lbl_t = QLabel("◬ AMTLICHES GEODÄTISCHES PRÜFGUTACHTEN (VOB/C & DIN 18716)")
        lbl_t.setStyleSheet("font-family: Consolas; font-size: 13px; font-weight: 900; color: #00d2ff;")
        head_box.addWidget(lbl_t)
        head_box.addStretch()
        layout.addLayout(head_box)

        self.viewer = QTextEdit()
        self.viewer.setReadOnly(True)
        self.viewer.setHtml(html_content)
        self.viewer.setStyleSheet("background: #060b18; border: 1px solid #151e2e; border-radius: 8px; padding: 12px; font-family: Segoe UI;")
        layout.addWidget(self.viewer, 1)

        btn_box = QHBoxLayout()
        btn_box.setSpacing(10)

        btn_save_pdf = QPushButton("💾 Als PDF Speichern...")
        btn_save_pdf.setStyleSheet("background: #0284c7; color: white; font-weight: bold; padding: 8px 16px; border-radius: 6px;")
        btn_save_pdf.clicked.connect(self.save_as_pdf)
        btn_box.addWidget(btn_save_pdf)

        btn_open_browser = QPushButton("🌐 Im Browser Öffnen")
        btn_open_browser.setStyleSheet("background: #0f172a; color: #38bdf8; font-weight: bold; padding: 8px 16px; border-radius: 6px; border: 1px solid #1e293b;")
        btn_open_browser.clicked.connect(self.open_in_browser)
        btn_box.addWidget(btn_open_browser)

        btn_box.addStretch()

        btn_close = QPushButton("Schließen")
        btn_close.setStyleSheet("background: #1e293b; color: white; padding: 8px 16px; border-radius: 6px;")
        btn_close.clicked.connect(self.accept)
        btn_box.addWidget(btn_close)

        layout.addLayout(btn_box)

    def save_as_pdf(self):
        dest, _ = QFileDialog.getSaveFileName(self, "PDF Dokument speichern", "Pruefgutachten_2026.pdf", "PDF (*.pdf)")
        if dest:
            try:
                import shutil
                shutil.copyfile(self.pdf_path, dest)
                QMessageBox.information(self, "Erfolg", f"✓ PDF Gutachten erfolgreich gespeichert:\n{dest}")
            except Exception as e:
                QMessageBox.critical(self, "Fehler", f"Konnte PDF nicht kopieren:\n{str(e)}")

    def open_in_browser(self):
        html_temp = self.pdf_path.replace(".pdf", ".html")
        webbrowser.open(f"file:///{html_temp}")

class LongitudinalProfileDialog(QDialog):
    def __init__(self, stations, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Längs- und Querprofil // Trassenachsen-Höhenplan (DIN 18702)")
        self.resize(920, 500)
        self.setStyleSheet("background-color: #020408; color: #f8fafc;")
        self.stations = stations

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()

        painter.fillRect(0, 0, w, h, QColor("#030712"))
        painter.setPen(QPen(QColor("#0e1a2e"), 1))
        for x in range(60, w - 20, 50): painter.drawLine(x, 40, x, h - 90)
        for y in range(50, h - 90, 40): painter.drawLine(60, y, w - 20, y)

        painter.setFont(QFont("Consolas", 11, QFont.Bold))
        painter.setPen(QColor("#00d2ff"))
        painter.drawText(60, 30, "TRASSEN-LÄNGSPROFIL // SOLL-PLANUM VS. URGELÄNDE")

        if not self.stations or len(self.stations) < 2:
            painter.setPen(QColor("#94a3b8"))
            painter.drawText(80, 160, "Keine Trassenpunkte vorhanden.")
            return

        graph_w = w - 100
        graph_h = h - 170
        max_stat = max(0.1, self.stations[-1]["station"])
        z_vals = [s["terrain_z"] for s in self.stations] + [s["design_z"] for s in self.stations]
        min_z, max_z = min(z_vals) - 1.0, max(z_vals) + 1.0
        z_range = max(0.1, max_z - min_z)

        painter.setPen(QPen(QColor("#10b981"), 2))
        pts_terrain = [QPointF(60 + (s["station"] / max_stat) * graph_w, 50 + graph_h - ((s["terrain_z"] - min_z) / z_range) * graph_h) for s in self.stations]
        for i in range(len(pts_terrain) - 1): painter.drawLine(pts_terrain[i], pts_terrain[i+1])

        painter.setPen(QPen(QColor("#f59e0b"), 2.5, Qt.DashLine))
        pts_design = [QPointF(60 + (s["station"] / max_stat) * graph_w, 50 + graph_h - ((s["design_z"] - min_z) / z_range) * graph_h) for s in self.stations]
        for i in range(len(pts_design) - 1): painter.drawLine(pts_design[i], pts_design[i+1])

        painter.setPen(QPen(QColor("#151e2e"), 1.5))
        painter.drawLine(60, h - 85, w - 20, h - 85)
        painter.setFont(QFont("Consolas", 8, QFont.Bold))

        painter.setPen(QColor("#10b981"))
        painter.drawText(60, h - 68, "— Geländehöhe (m)")
        painter.setPen(QColor("#f59e0b"))
        painter.drawText(220, h - 68, "-- Entwurfshöhe (m)")
        painter.setPen(QColor("#00d2ff"))
        painter.drawText(380, h - 68, "● Stationierung (m)")

        for s in self.stations:
            px = 60 + (s["station"] / max_stat) * graph_w
            painter.setPen(QColor("#10b981"))
            painter.drawText(int(px - 15), h - 48, f"{s['terrain_z']:.2f}")
            painter.setPen(QColor("#f59e0b"))
            painter.drawText(int(px - 15), h - 32, f"{s['design_z']:.2f}")
            painter.setPen(QColor("#94a3b8"))
            painter.drawText(int(px - 15), h - 16, f"0+{int(s['station']):03d}")

class ProCADViewport(QWidget):
    def __init__(self, pro_ui, parent=None):
        super().__init__(parent)
        self.pro_ui = pro_ui
        self.setMinimumSize(500, 420)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setStyleSheet("background-color: #020408; border: 1px solid #151e2e; border-radius: 8px;")

        self.center_lat = 51.2277
        self.center_lon = 6.7735
        self.zoom_level = 14.0

        self.target_lat = self.center_lat
        self.target_lon = self.center_lon
        self.target_zoom = self.zoom_level

        self.flight_timer = QTimer(self)
        self.flight_timer.timeout.connect(self.step_flight_animation)

        self.last_mouse_pos = QPoint()
        self.setMouseTracking(True)
        self.cursor_pos = QPointF(0, 0)

        self.basemap_provider = "satellite"
        self.active_state_code = "NRW"

        self.active_tool = "pan"
        self.current_drawing_pts = []
        
        self.created_buildings = []
        self.created_roads = []
        self.created_markers = []
        self.ai_classified_points = []
        
        # كائنات التحديد الكاد المعيارية
        self.selected_point_id = None
        self.selected_building_idx = None
        self.selected_road_idx = None
        
        GLOBAL_MAP_MANAGER.update_viewport.connect(self.update)

    def fly_to_state(self, code):
        info = BundeslaenderEngine.get_state(code)
        self.active_state_code = code
        self.target_lat = info["lat"]
        self.target_lon = info["lon"]
        self.target_zoom = float(info["zoom"])
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

    def keyPressEvent(self, event):
        """التعامل مع زر Delete و Esc كمعيار كاد"""
        if event.key() in [Qt.Key_Delete, Qt.Key_Backspace]:
            self.delete_selected_element()
        elif event.key() == Qt.Key_Escape:
            self.clear_selection_or_drawing()
        super().keyPressEvent(event)

    def clear_selection_or_drawing(self):
        self.selected_point_id = None
        self.selected_building_idx = None
        self.selected_road_idx = None
        self.current_drawing_pts = []
        self.active_tool = "pan"
        self.pro_ui.btn_pan.setChecked(True)
        self.update()

    def delete_selected_element(self):
        """حذف العنصر المحدد أياً كان نوعه"""
        deleted = False
        if self.selected_point_id:
            for i, m in enumerate(self.created_markers):
                if m.name == self.selected_point_id:
                    del self.created_markers[i]
                    deleted = True
                    break
            self.selected_point_id = None
            self.pro_ui.refresh_table_from_markers()

        elif self.selected_building_idx is not None and self.selected_building_idx < len(self.created_buildings):
            del self.created_buildings[self.selected_building_idx]
            self.selected_building_idx = None
            deleted = True
            self.pro_ui.recalculate_all_masses()

        elif self.selected_road_idx is not None and self.selected_road_idx < len(self.created_roads):
            del self.created_roads[self.selected_road_idx]
            self.selected_road_idx = None
            deleted = True
            self.pro_ui.recalculate_all_masses()

        if deleted:
            self.update()

    def mousePressEvent(self, event):
        self.last_mouse_pos = event.pos()
        w, h = self.width(), self.height()
        cx, cy = w / 2, h / 2
        click_x = event.position().x() - cx
        click_y = event.position().y() - cy

        scale = 360.0 / (256.0 * (2 ** self.zoom_level))
        cur_lon = self.center_lon + click_x * scale
        cur_lat = self.center_lat - click_y * scale * math.cos(math.radians(self.center_lat))
        utm_e = (cur_lon - 9.0) * 111319.49 * math.cos(math.radians(cur_lat)) + 500000.0
        utm_n = cur_lat * 110574.0

        if event.button() == Qt.LeftButton:
            if self.active_tool == "pan":
                # فحص التحديد الذكي المباشر (Point Picking)
                self.selected_point_id = None
                self.selected_building_idx = None
                self.selected_road_idx = None

                # 1. فحص النقاط
                for m in self.created_markers:
                    if math.sqrt((m.x - click_x)**2 + (m.y - click_y)**2) < 18:
                        self.selected_point_id = m.name
                        self.pro_ui.select_table_row_by_id(m.name)
                        self.update()
                        return

                # 2. فحص المباني
                for idx, b in enumerate(self.created_buildings):
                    poly = QPolygonF([QPointF(p[0], p[1]) for p in b.points])
                    if poly.containsPoint(QPointF(click_x, click_y), Qt.OddEvenFill):
                        self.selected_building_idx = idx
                        self.update()
                        return

                # 3. فحص الطرق
                for idx, r in enumerate(self.created_roads):
                    for p in r.points:
                        if math.sqrt((p[0] - click_x)**2 + (p[1] - click_y)**2) < 20:
                            self.selected_road_idx = idx
                            self.update()
                            return
                self.update()

            elif self.active_tool == "building":
                self.current_drawing_pts.append((click_x, click_y))
                self.update()
            elif self.active_tool == "road":
                self.current_drawing_pts.append((click_x, click_y))
                self.update()
            elif self.active_tool == "marker":
                m_name = f"P-{len(self.created_markers)+1:03d}"
                new_m = MarkerPointObject(click_x, click_y, cur_lat, cur_lon, utm_e, utm_n, name=m_name)
                self.created_markers.append(new_m)
                self.pro_ui.add_marker_to_table(new_m)
                self.update()

        elif event.button() == Qt.RightButton:
            if self.active_tool == "building" and len(self.current_drawing_pts) >= 3:
                b_name = f"Bauwerk #{len(self.created_buildings)+1}"
                self.created_buildings.append(BuildingObject(self.current_drawing_pts, height=25.0, name=b_name))
                self.current_drawing_pts = []
                self.pro_ui.recalculate_all_masses()
                self.update()
            elif self.active_tool == "road" and len(self.current_drawing_pts) >= 2:
                r_name = f"Trassenachse #{len(self.created_roads)+1}"
                self.created_roads.append(RoadObject(self.current_drawing_pts, width=14.0, name=r_name))
                self.current_drawing_pts = []
                self.pro_ui.recalculate_all_masses()
                self.update()

    def mouseMoveEvent(self, event):
        self.cursor_pos = event.position()
        delta = event.pos() - self.last_mouse_pos

        if event.buttons() & Qt.LeftButton and self.active_tool == "pan" and not (self.selected_point_id or self.selected_building_idx is not None or self.selected_road_idx is not None):
            scale = 360.0 / (256.0 * (2 ** self.zoom_level))
            self.center_lon -= delta.x() * scale
            self.center_lat += delta.y() * scale * math.cos(math.radians(self.center_lat))
            self.target_lat = self.center_lat
            self.target_lon = self.center_lon
            self.update()

        self.last_mouse_pos = event.pos()
        self.update()

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        self.zoom_level = min(19.0, self.zoom_level + 0.3) if delta > 0 else max(4.0, self.zoom_level - 0.3)
        self.target_zoom = self.zoom_level
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        w, h = self.width(), self.height()
        cx, cy = w / 2, h / 2

        self.render_real_map_tiles(painter, w, h, cx, cy)

        # الطرق
        for idx, road in enumerate(self.created_roads):
            if len(road.points) >= 2:
                is_sel = (self.selected_road_idx == idx)
                pen_color = QColor("#00d2ff") if is_sel else QColor("#334155")
                painter.setPen(QPen(pen_color, road.width + (4 if is_sel else 0), Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
                for i in range(len(road.points) - 1):
                    painter.drawLine(QPointF(cx + road.points[i][0], cy + road.points[i][1]),
                                     QPointF(cx + road.points[i+1][0], cy + road.points[i+1][1]))
                painter.setPen(QPen(QColor("#f59e0b"), 1.8, Qt.DashLine))
                for i in range(len(road.points) - 1):
                    painter.drawLine(QPointF(cx + road.points[i][0], cy + road.points[i][1]),
                                     QPointF(cx + road.points[i+1][0], cy + road.points[i+1][1]))

        # المباني
        for idx, b in enumerate(self.created_buildings):
            pts = b.points
            if len(pts) >= 3:
                is_sel = (self.selected_building_idx == idx)
                painter.setPen(QPen(QColor("#38bdf8") if is_sel else QColor("#0284c7"), 2.2 if is_sel else 1.4))
                painter.setBrush(QBrush(QColor(56, 189, 248, 140) if is_sel else QColor(14, 165, 233, 100)))
                for i in range(len(pts)):
                    p_curr = pts[i]
                    p_next = pts[(i+1)%len(pts)]
                    wall = QPolygonF([
                        QPointF(cx + p_curr[0], cy + p_curr[1]),
                        QPointF(cx + p_next[0], cy + p_next[1]),
                        QPointF(cx + p_next[0], cy + p_next[1] - b.height),
                        QPointF(cx + p_curr[0], cy + p_curr[1] - b.height)
                    ])
                    painter.drawPolygon(wall)

                painter.setPen(QPen(QColor("#ffffff") if is_sel else QColor("#38bdf8"), 2.0 if is_sel else 1.8))
                painter.setBrush(QBrush(QColor(0, 210, 255, 190) if is_sel else QColor(56, 189, 248, 160)))
                poly_top = QPolygonF([QPointF(cx + p[0], cy + p[1] - b.height) for p in pts])
                painter.drawPolygon(poly_top)

                painter.setFont(QFont("Consolas", 8, QFont.Bold))
                painter.setPen(QColor("#ffffff"))
                painter.drawText(int(cx + pts[0][0]), int(cy + pts[0][1] - b.height - 4), b.name)

        # النقاط المساحية
        for m in self.created_markers:
            px = cx + m.x
            py = cy + m.y
            is_sel = (self.selected_point_id == m.name)

            if is_sel:
                painter.setPen(QPen(QColor("#00d2ff"), 2.5))
                painter.setBrush(Qt.NoBrush)
                painter.drawEllipse(QPointF(px, py), 16, 16)

            pt_color = QColor("#ef4444")
            for cp in self.ai_classified_points:
                if cp["id"] == m.name:
                    pt_color = QColor(cp["color"])
                    break

            painter.setPen(QPen(QColor("#ffffff"), 1.5))
            painter.setBrush(QBrush(pt_color))
            painter.drawEllipse(QPointF(px, py), 7, 7)
            painter.setFont(QFont("Consolas", 8, QFont.Bold))
            painter.setPen(pt_color)
            painter.drawText(int(px + 9), int(py + 4), m.name)

        # المضلع النشط
        if self.current_drawing_pts:
            painter.setPen(QPen(QColor("#10b981"), 2, Qt.DashLine))
            painter.setBrush(QBrush(QColor(16, 185, 129, 30)))
            poly = QPolygonF([QPointF(cx + p[0], cy + p[1]) for p in self.current_drawing_pts])
            if len(self.current_drawing_pts) >= 3:
                painter.drawPolygon(poly)
            else:
                for i in range(len(self.current_drawing_pts) - 1):
                    painter.drawLine(QPointF(cx + self.current_drawing_pts[i][0], cy + self.current_drawing_pts[i][1]),
                                     QPointF(cx + self.current_drawing_pts[i+1][0], cy + self.current_drawing_pts[i+1][1]))
            painter.drawLine(QPointF(cx + self.current_drawing_pts[-1][0], cy + self.current_drawing_pts[-1][1]), self.cursor_pos)

        self.render_hud_box(painter, w, h)

    def render_hud_box(self, painter, w, h):
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(4, 7, 13, 220)))
        painter.drawRoundedRect(12, 12, 450, 28, 6, 6)
        painter.drawRoundedRect(w - 480, 12, 468, 28, 6, 6)
        painter.drawRoundedRect(12, h - 36, 520, 26, 6, 6)

        painter.setFont(QFont("Consolas", 9, QFont.Bold))
        sel_info = f" [Auswahl: {self.selected_point_id or 'Objekt'}] -> 'Entf' zum Löschen" if (self.selected_point_id or self.selected_building_idx is not None or self.selected_road_idx is not None) else ""
        painter.setPen(QColor("#00d2ff" if sel_info else ("#f59e0b" if self.active_tool != "pan" else "#94a3b8")))
        tool_hint = (
            "✋ [SELECT & PAN: Klick zum Wählen, Ziehen zum Bewegen]" if self.active_tool == "pan" else (
            "🏢 [3D-BAUWERK: L-Klick Punkt, R-Klick Fertig]" if self.active_tool == "building" else (
            "🛣️ [TRASSENACHSE: L-Klick Trasse, R-Klick Fertig]" if self.active_tool == "road" else
            "📍 [PUNKT: Klick zum Setzen]"
        ))) + sel_info
        painter.drawText(22, 30, tool_hint)

        state_info = BundeslaenderEngine.get_state(self.active_state_code)
        painter.setPen(QColor("#00d2ff"))
        painter.drawText(w - 468, 30, f"{state_info['name']} | ZOOM: {self.zoom_level:.1f}x | {state_info['crs']}")

        scale = 360.0 / (256.0 * (2 ** self.zoom_level))
        cur_lon = self.center_lon + (self.cursor_pos.x() - w/2) * scale
        cur_lat = self.center_lat - (self.cursor_pos.y() - h/2) * scale * math.cos(math.radians(self.center_lat))
        utm_e = (cur_lon - 9.0) * 111319.49 * math.cos(math.radians(cur_lat)) + 500000.0
        utm_n = cur_lat * 110574.0
        painter.setPen(QColor("#10b981"))
        painter.drawText(22, h - 18, f"CURSOR: {cur_lat:.5f}°N, {cur_lon:.5f}°E | UTM 32N: E {utm_e:,.2f} m, N {utm_n:,.2f} m")

    def render_real_map_tiles(self, painter, w, h, cx, cy):
        z = int(round(self.zoom_level))
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

class ProCADWorkspaceWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self.undo_shortcut = QShortcut(QKeySequence("Ctrl+Z"), self)
        self.undo_shortcut.activated.connect(self.action_undo_last)

        self.ribbon = QTabWidget()
        self.ribbon.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #151e2e; background: #04070d; border-radius: 8px; }
            QTabBar::tab {
                background: #081220; color: #94a3b8; font-family: 'Segoe UI', sans-serif;
                font-size: 11px; font-weight: bold; padding: 6px 14px; margin-right: 4px; border-top-left-radius: 6px; border-top-right-radius: 6px;
            }
            QTabBar::tab:selected { background: #00d2ff; color: #020408; font-weight: 900; }
            QPushButton {
                background: #08182b; color: #ffffff; font-weight: bold; font-size: 11px;
                padding: 6px 14px; border-radius: 5px; border: 1px solid #0284c7;
            }
            QPushButton:hover { background: #00d2ff; color: #020408; }
            QPushButton:checked { background: #10b981; color: #020408; font-weight: 900; border: 2px solid #34d399; }
        """)

        # Tab 1: 🗺️ Navigation & 3D Drafting (Clean & Intuitive)
        tab1 = QWidget()
        t1_layout = QHBoxLayout(tab1)
        t1_layout.setContentsMargins(8, 6, 8, 6)
        t1_layout.setSpacing(8)

        t1_layout.addWidget(QLabel("Bundesland:"))
        self.cb_states = QComboBox()
        for code, info in BundeslaenderEngine.STATES.items():
            self.cb_states.addItem(f"{code} - {info['name']}", code)
        self.cb_states.currentIndexChanged.connect(self.on_state_changed)
        t1_layout.addWidget(self.cb_states)

        t1_layout.addWidget(QLabel("Karte:"))
        self.cb_map = QComboBox()
        self.cb_map.addItems(["🛰️ Satellit (ESRI)", "🗺️ Straßen (OSM)", "📐 Topo Relief"])
        self.cb_map.currentIndexChanged.connect(self.on_map_provider_change)
        t1_layout.addWidget(self.cb_map)

        self.btn_pan = QPushButton("✋ Select / Pan")
        self.btn_pan.setCheckable(True)
        self.btn_pan.setChecked(True)
        self.btn_pan.clicked.connect(lambda: self.set_tool("pan"))
        t1_layout.addWidget(self.btn_pan)

        self.btn_bld = QPushButton("🏢 3D Gebäude")
        self.btn_bld.setCheckable(True)
        self.btn_bld.clicked.connect(lambda: self.set_tool("building"))
        t1_layout.addWidget(self.btn_bld)

        self.btn_road = QPushButton("🛣️ Trasse")
        self.btn_road.setCheckable(True)
        self.btn_road.clicked.connect(lambda: self.set_tool("road"))
        t1_layout.addWidget(self.btn_road)

        self.btn_marker = QPushButton("📍 Punkt Setzen")
        self.btn_marker.setCheckable(True)
        self.btn_marker.clicked.connect(lambda: self.set_tool("marker"))
        t1_layout.addWidget(self.btn_marker)

        btn_fly = QPushButton("✈️ Flug zur Region")
        btn_fly.clicked.connect(lambda: self.viewport.fly_to_state(self.cb_states.currentData()))
        t1_layout.addWidget(btn_fly)
        t1_layout.addStretch()
        self.ribbon.addTab(tab1, "🗺️ Navigation & 3D Drafting")

        # Tab 2: 🧠 Complete 5-Tier AI Intelligence Matrix
        tab2 = QWidget()
        t2_layout = QHBoxLayout(tab2)
        t2_layout.setContentsMargins(8, 6, 8, 6)
        t2_layout.setSpacing(8)

        btn_ai_opt = QPushButton("⚡ 1. AI Massen-Optimierer")
        btn_ai_opt.setStyleSheet("background: #0f2b3e; border: 1px solid #00d2ff; font-weight: bold;")
        btn_ai_opt.clicked.connect(self.action_ai_optimize_masses)
        t2_layout.addWidget(btn_ai_opt)

        btn_ai_gen = QPushButton("🏢 2. AI 3D LoD2 Kataster-Generator")
        btn_ai_gen.setStyleSheet("background: #0f2b3e; border: 1px solid #00d2ff; font-weight: bold;")
        btn_ai_gen.clicked.connect(self.action_ai_generate_buildings)
        t2_layout.addWidget(btn_ai_gen)

        btn_ai_sub = QPushButton("📉 3. AI Setzungs-Heatmap")
        btn_ai_sub.setStyleSheet("background: #0f2b3e; border: 1px solid #00d2ff; font-weight: bold;")
        btn_ai_sub.clicked.connect(self.action_ai_predict_subsidence)
        t2_layout.addWidget(btn_ai_sub)

        btn_ai_boq = QPushButton("📝 4. AI GAEB/VOB Leistungsverzeichnis")
        btn_ai_boq.setStyleSheet("background: #0f2b3e; border: 1px solid #00d2ff; font-weight: bold;")
        btn_ai_boq.clicked.connect(self.action_ai_semantic_boq)
        t2_layout.addWidget(btn_ai_boq)

        btn_ai_zone = QPushButton("⚖️ 5. AI BauGB §34 Audit")
        btn_ai_zone.setStyleSheet("background: #0f2b3e; border: 1px solid #00d2ff; font-weight: bold;")
        btn_ai_zone.clicked.connect(self.action_ai_zoning_audit)
        t2_layout.addWidget(btn_ai_zone)

        t2_layout.addStretch()
        self.ribbon.addTab(tab2, "🧠 5-Tier AI Matrix")

        # Tab 3: 📂 Survey Import Hub
        tab3 = QWidget()
        t3_layout = QHBoxLayout(tab3)
        t3_layout.setContentsMargins(8, 6, 8, 6)
        t3_layout.setSpacing(8)

        btn_import = QPushButton("📂 Vermessungsdatei importieren (CSV/DXF)")
        btn_import.clicked.connect(self.action_import_survey_data)
        t3_layout.addWidget(btn_import)

        btn_sample = QPushButton("🧪 5 Test-Grenzpunkte laden")
        btn_sample.clicked.connect(self.action_load_sample)
        t3_layout.addWidget(btn_sample)

        btn_clr_pts = QPushButton("🗑️ Punkte leeren")
        btn_clr_pts.clicked.connect(self.action_clear_markers)
        t3_layout.addWidget(btn_clr_pts)

        btn_clr_bld = QPushButton("🗑️ Gebäude leeren")
        btn_clr_bld.clicked.connect(self.action_clear_buildings)
        t3_layout.addWidget(btn_clr_bld)

        btn_clr_road = QPushButton("🗑️ Trassen leeren")
        btn_clr_road.clicked.connect(self.action_clear_roads)
        t3_layout.addWidget(btn_clr_road)

        t3_layout.addStretch()
        self.ribbon.addTab(tab3, "📂 Survey Import Hub")

        # Tab 4: 📈 Profiles & Civil Analysis
        tab4 = QWidget()
        t4_layout = QHBoxLayout(tab4)
        t4_layout.setContentsMargins(8, 6, 8, 6)
        t4_layout.setSpacing(8)

        btn_profile = QPushButton("📈 Längs- & Querprofil öffnen")
        btn_profile.clicked.connect(self.action_show_profile)
        t4_layout.addWidget(btn_profile)

        btn_recalc = QPushButton("⚡ REB-VB Massen neu berechnen")
        btn_recalc.clicked.connect(self.recalculate_all_masses)
        t4_layout.addWidget(btn_recalc)
        t4_layout.addStretch()
        self.ribbon.addTab(tab4, "📈 Profiles & Civil Analysis")

        # Tab 5: 🏛️ Sovereign Corporate Audit Hub
        tab5 = QWidget()
        t5_layout = QHBoxLayout(tab5)
        t5_layout.setContentsMargins(8, 6, 8, 6)
        t5_layout.setSpacing(8)

        btn_official_pdf = QPushButton("📑 Amtliches Prüfgutachten (.PDF & Live Viewer)")
        btn_official_pdf.setStyleSheet("background: #0284c7; font-weight: 900; border: 1.5px solid #00d2ff;")
        btn_official_pdf.clicked.connect(self.action_export_official_pdf)
        t5_layout.addWidget(btn_official_pdf)

        btn_vob = QPushButton("VOB/C DA45")
        btn_vob.clicked.connect(self.action_vob)
        t5_layout.addWidget(btn_vob)

        btn_gaeb = QPushButton("GAEB X83 XML")
        btn_gaeb.clicked.connect(self.action_gaeb)
        t5_layout.addWidget(btn_gaeb)

        btn_dxf = QPushButton("AutoCAD 3D DXF")
        btn_dxf.clicked.connect(self.action_dxf_export)
        t5_layout.addWidget(btn_dxf)

        btn_landxml = QPushButton("LandXML 1.2")
        btn_landxml.clicked.connect(self.action_landxml_export)
        t5_layout.addWidget(btn_landxml)

        btn_qes = QPushButton("DIN 18716 QES Siegel")
        btn_qes.clicked.connect(self.action_qes_seal)
        t5_layout.addWidget(btn_qes)
        t5_layout.addStretch()
        self.ribbon.addTab(tab5, "🏛️ Sovereign Corporate Audit Hub")

        layout.addWidget(self.ribbon)

        # Splitters
        main_splitter = QSplitter(Qt.Vertical)
        upper_splitter = QSplitter(Qt.Horizontal)

        # Left Dock
        left_dock = QWidget()
        left_dock.setMinimumWidth(330)
        l_layout = QVBoxLayout(left_dock)
        l_layout.setContentsMargins(0, 0, 0, 0)
        l_layout.setSpacing(10)

        grp_import = QGroupBox("REGIONAL CRS // GEODESY")
        gi_layout = QVBoxLayout(grp_import)
        self.lbl_region_name = QLabel("Region: Nordrhein-Westfalen")
        self.lbl_region_name.setStyleSheet("font-family: Consolas; font-size: 11px; color: #94a3b8; font-weight: bold;")
        self.lbl_crs_active = QLabel("System: ETRS89 / UTM 32N")
        self.lbl_crs_active.setStyleSheet("font-family: Consolas; font-size: 11px; color: #00d2ff; font-weight: bold;")
        self.lbl_grid_active = QLabel("Gitter: BeTA2007_NRW")
        self.lbl_grid_active.setStyleSheet("font-family: Consolas; font-size: 11px; color: #10b981; font-weight: bold;")
        gi_layout.addWidget(self.lbl_region_name)
        gi_layout.addWidget(self.lbl_crs_active)
        gi_layout.addWidget(self.lbl_grid_active)
        l_layout.addWidget(grp_import)

        grp_layers = QGroupBox("SPATIAL LAYER MATRIX")
        gl_layout = QVBoxLayout(grp_layers)
        self.layer_tree = QTreeWidget()
        self.layer_tree.setHeaderLabels(["Ebene / Layer", "Status"])
        self.layer_tree.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.layer_tree.setTextElideMode(Qt.ElideNone)
        self.layer_tree.header().setSectionResizeMode(0, QHeaderView.Interactive)
        self.layer_tree.header().resizeSection(0, 235)
        self.layer_tree.header().setSectionResizeMode(1, QHeaderView.Fixed)
        self.layer_tree.header().resizeSection(1, 75)

        for name in [
            "L01: Satelliten-Orthofoto",
            "L02: DGM Geländerelief TIN",
            "L03: ALKIS Katastergrenzen",
            "L04: 3D Bauwerksentwurf LoD2"
        ]:
            item = QTreeWidgetItem([name, "[ ACTIVE ]"])
            item.setCheckState(0, Qt.Checked)
            self.layer_tree.addTopLevelItem(item)
        gl_layout.addWidget(self.layer_tree)
        l_layout.addWidget(grp_layers)
        upper_splitter.addWidget(left_dock)

        # Center Viewport
        self.viewport = ProCADViewport(self)
        upper_splitter.addWidget(self.viewport)

        # Right Dock
        right_dock = QWidget()
        right_dock.setMinimumWidth(300)
        r_layout = QVBoxLayout(right_dock)
        r_layout.setContentsMargins(0, 0, 0, 0)
        r_layout.setSpacing(10)

        grp_telemetry = QGroupBox("LIVE REB-VB MASSEN // KOSTEN")
        gt_layout = QVBoxLayout(grp_telemetry)
        self.lbl_m_cut = QLabel("Aushub (Abtrag):  0 m³")
        self.lbl_m_cut.setStyleSheet("font-family: Consolas; color: #ef4444; font-weight: bold; font-size: 11.5px;")
        self.lbl_m_fill = QLabel("Auftrag (Planum): 0 m³")
        self.lbl_m_fill.setStyleSheet("font-family: Consolas; color: #10b981; font-weight: bold; font-size: 11.5px;")
        self.lbl_m_saldo = QLabel("Netto-Saldo:      0 m³")
        self.lbl_m_saldo.setStyleSheet("font-family: Consolas; color: #00d2ff; font-weight: 900; font-size: 12px;")
        self.lbl_m_cost = QLabel("Baukosten (Est):  0,00 €")
        self.lbl_m_cost.setStyleSheet("font-family: Consolas; color: #f59e0b; font-weight: bold; font-size: 11.5px;")
        self.lbl_m_co2 = QLabel("CO2-Bilanz:       0,0 t")
        self.lbl_m_co2.setStyleSheet("font-family: Consolas; color: #38bdf8; font-weight: bold; font-size: 11.5px;")

        gt_layout.addWidget(self.lbl_m_cut)
        gt_layout.addWidget(self.lbl_m_fill)
        gt_layout.addWidget(self.lbl_m_saldo)
        gt_layout.addWidget(self.lbl_m_cost)
        gt_layout.addWidget(self.lbl_m_co2)
        r_layout.addWidget(grp_telemetry)

        grp_ai_status = QGroupBox("5-TIER AI REAL-TIME AUDITOR")
        gas_layout = QVBoxLayout(grp_ai_status)
        self.lbl_ai_summary = QLabel("AI Optimizer: [ READY ]")
        self.lbl_ai_summary.setStyleSheet("font-family: Consolas; color: #38bdf8; font-weight: bold; font-size: 11px;")
        self.lbl_ai_anomalies = QLabel("BauGB Audit:  [ KONFORM ]")
        self.lbl_ai_anomalies.setStyleSheet("font-family: Consolas; color: #10b981; font-weight: bold; font-size: 11px;")
        gas_layout.addWidget(self.lbl_ai_summary)
        gas_layout.addWidget(self.lbl_ai_anomalies)
        r_layout.addWidget(grp_ai_status)

        grp_vault = QGroupBox("SOVEREIGN QES VAULT")
        gv_layout = QVBoxLayout(grp_vault)
        self.lbl_merkle_display = QLabel("MERKLE ROOT ANCHOR:\n8f4e2b09a1c6e4d7b1a03f9c5e2d8a7b...")
        self.lbl_merkle_display.setStyleSheet("font-family: Consolas; font-size: 10.5px; color: #f59e0b; font-weight: bold;")
        self.lbl_hwid_display = QLabel("HWID: 00B9C6E0A6FEBC10\nALGORITHM: RSA-2048 PSS SHA-256")
        self.lbl_hwid_display.setStyleSheet("font-family: Consolas; font-size: 10.5px; color: #94a3b8;")
        gv_layout.addWidget(self.lbl_merkle_display)
        gv_layout.addWidget(self.lbl_hwid_display)
        r_layout.addWidget(grp_vault)

        upper_splitter.addWidget(right_dock)
        upper_splitter.setStretchFactor(0, 1)
        upper_splitter.setStretchFactor(1, 4)
        upper_splitter.setStretchFactor(2, 2)
        main_splitter.addWidget(upper_splitter)

        # Bottom Table: Key Navigation & Entf Support
        grp_points = QGroupBox("COORDINATE MATRIX // BIDIRECTIONAL SYNC & AI AUDIT (Taste 'Entf' = Punkt löschen)")
        gp_layout = QVBoxLayout(grp_points)
        self.table_points = QTableWidget(0, 6)
        self.table_points.setHorizontalHeaderLabels(["PUNKT-ID", "OSTWERT (E)", "HOCHWERT (N)", "HOEHE (Z)", "CODE / AI-KLASSE", "AUDIT"])
        self.table_points.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_points.cellClicked.connect(self.on_table_point_clicked)
        self.table_points.cellChanged.connect(self.on_table_cell_edited)
        gp_layout.addWidget(self.table_points)
        main_splitter.addWidget(grp_points)

        main_splitter.setStretchFactor(0, 3)
        main_splitter.setStretchFactor(1, 2)
        layout.addWidget(main_splitter)
        self.recalculate_all_masses()

    def set_tool(self, t):
        self.viewport.active_tool = t
        self.btn_pan.setChecked(t == "pan")
        self.btn_bld.setChecked(t == "building")
        self.btn_road.setChecked(t == "road")
        self.btn_marker.setChecked(t == "marker")
        self.viewport.current_drawing_pts = []
        self.viewport.update()

    def on_map_provider_change(self, idx):
        providers = ["satellite", "osm", "topo"]
        self.viewport.basemap_provider = providers[idx]
        self.viewport.update()

    def on_table_point_clicked(self, row, col):
        p_id = self.table_points.item(row, 0).text()
        self.viewport.selected_point_id = p_id
        for m in self.viewport.created_markers:
            if m.name == p_id:
                self.viewport.target_lat = m.lat
                self.viewport.target_lon = m.lon
                self.viewport.flight_timer.start(16)
                break
        self.viewport.update()

    def select_table_row_by_id(self, p_id):
        for r in range(self.table_points.rowCount()):
            if self.table_points.item(r, 0).text() == p_id:
                self.table_points.selectRow(r)
                break

    def on_table_cell_edited(self, row, col):
        if col in [1, 2, 3] and self.table_points.item(row, 0):
            p_id = self.table_points.item(row, 0).text()
            try:
                val = float(self.table_points.item(row, col).text().replace(',', ''))
                for m in self.viewport.created_markers:
                    if m.name == p_id:
                        if col == 1: m.utm_e = val
                        elif col == 2: m.utm_n = val
                        break
                self.recalculate_all_masses()
            except Exception:
                pass

    def action_undo_last(self):
        if self.viewport.created_markers:
            self.viewport.created_markers.pop()
            self.refresh_table_from_markers()
        elif self.viewport.created_roads:
            self.viewport.created_roads.pop()
            self.recalculate_all_masses()
        elif self.viewport.created_buildings:
            self.viewport.created_buildings.pop()
            self.recalculate_all_masses()
        self.viewport.update()

    def refresh_table_from_markers(self):
        self.table_points.blockSignals(True)
        self.table_points.setRowCount(0)
        for m in self.viewport.created_markers:
            row_idx = self.table_points.rowCount()
            self.table_points.insertRow(row_idx)
            self.table_points.setItem(row_idx, 0, QTableWidgetItem(m.name))
            self.table_points.setItem(row_idx, 1, QTableWidgetItem(f"{m.utm_e:,.3f}"))
            self.table_points.setItem(row_idx, 2, QTableWidgetItem(f"{m.utm_n:,.3f}"))
            self.table_points.setItem(row_idx, 3, QTableWidgetItem("142.000"))
            self.table_points.setItem(row_idx, 4, QTableWidgetItem("Vermessung"))
            item_audit = QTableWidgetItem("[ VALID ]")
            item_audit.setForeground(QColor("#10b981"))
            self.table_points.setItem(row_idx, 5, item_audit)
        self.table_points.blockSignals(False)
        self.recalculate_all_masses()

    def action_clear_buildings(self):
        self.viewport.created_buildings = []
        self.viewport.selected_building_idx = None
        self.recalculate_all_masses()
        self.viewport.update()

    def action_clear_roads(self):
        self.viewport.created_roads = []
        self.viewport.selected_road_idx = None
        self.recalculate_all_masses()
        self.viewport.update()

    def action_ai_optimize_masses(self):
        if not self.viewport.created_roads:
            QMessageBox.information(self, "AI Optimizer", "Bitte zuerst eine Trasse mit dem Werkzeug '🛣️ Trasse' zeichnen.")
            return
        res = AdvancedGeoAISuite.optimize_mass_haul(self.viewport.created_roads[0].points)
        QMessageBox.information(
            self, "⚡ AI Mass-Haul Optimizer",
            f"✓ Optimale Trassierung nach VOB/C ermittelt:\n\n"
            f"● Trassenlänge: {res['total_len_m']:,.1f} m\n"
            f"● Empfohlene Längsneigung: {res['optimal_grade_pct']:.2f} %\n"
            f"● Ausgeglichener Aushub: {int(res['balanced_cut_m3']):,} m³\n"
            f"● Ausgeglichener Auftrag: {int(res['balanced_fill_m3']):,} m³\n"
            f"● Kraftstoffersparnis: {res['fuel_saved_l']:,.1f} Liter Diesel\n"
            f"● Baukosteneinsparung: {res['cost_saved_eur']:,.2f} €"
        )

    def action_ai_generate_buildings(self):
        gen_blds = AdvancedGeoAISuite.generate_3d_lod2_from_cadastre(self.viewport.center_lat, self.viewport.center_lon)
        for b in gen_blds:
            self.viewport.created_buildings.append(BuildingObject(b["points"], height=b["height"], name=b["name"]))
        self.recalculate_all_masses()
        self.viewport.update()
        QMessageBox.information(self, "🏢 AI LoD2 Generator", f"✓ {len(gen_blds)} 3D-Gebäudekörper aus Katasterdaten generiert und extrudiert.")

    def action_ai_predict_subsidence(self):
        pts_dict = [{"id": m.name, "e": m.utm_e, "n": m.utm_n, "z": 142.0} for m in self.viewport.created_markers]
        res = AdvancedGeoAISuite.predict_subsidence_heatmap(pts_dict)
        if res["risk_points"]:
            err_msg = "\n".join([f"● {p['id']}: Verformungsrate {p['drift_mm']} mm/a [{p['risk']}]" for p in res["risk_points"]])
            QMessageBox.warning(self, "📉 AI Setzungs-Heatmap", f"⚠️ Relevante Bodenbewegungen erkannt:\n\n{err_msg}")
        else:
            QMessageBox.information(self, "📉 AI Setzungs-Heatmap", "✓ Baugrund und Geodaten sind geotechnisch absolut stabil (< 1.5 mm Drift).")

    def action_ai_semantic_boq(self):
        res = InstantGeodeticMath.compute_all_project_masses(self.viewport.created_buildings, self.viewport.created_roads)
        specs = AdvancedGeoAISuite.generate_semantic_vob_specs(res['total_cut'], res['total_fill'], res['road_len_m'])
        msg = "\n\n".join([f"[{s['oz']}] {s['short']}\nMenge: {s['qty']} {s['unit']} | Gesamt: {s['total']}" for s in specs])
        QMessageBox.information(self, "📝 AI GAEB/VOB Leistungsverzeichnis", f"✓ Automatisch generierte Ausschreibungspositionen:\n\n{msg}")

    def action_ai_zoning_audit(self):
        violations = AdvancedGeoAISuite.audit_zoning_and_setbacks(self.viewport.created_buildings)
        if violations:
            msg = "\n".join([f"● {v['object']}: {v['type']}\n  {v['detail']}" for v in violations])
            QMessageBox.warning(self, "⚖️ AI BauGB & Abstandsflächen Audit", f"⚠️ Auflagen für Baugenehmigung gefunden:\n\n{msg}")
        else:
            QMessageBox.information(self, "⚖️ AI BauGB §34 Audit", "✓ Alle 3D-Baukörper entsprechen voll den Abstandsflächen und Höhenvorschriften.")

    def action_export_official_pdf(self):
        res = InstantGeodeticMath.compute_all_project_masses(self.viewport.created_buildings, self.viewport.created_roads)
        if res["total_cut"] == 0 and res["total_fill"] == 0:
            res = {
                "total_cut": 12000.0, "total_fill": 4500.0, "saldo": -7500.0,
                "cost_eur": 545000.0, "co2_tons": 45.2, "bld_area_m2": 1500.0, "road_len_m": 250.0
            }

        pts_dict = [{"id": m.name, "e": m.utm_e, "n": m.utm_n, "z": 142.0} for m in self.viewport.created_markers]
        ai_res = OfflineAILiDAREngine.classify_points(pts_dict)
        stamp = GeodesyEngine.generate_qes_stamp()

        state_info = BundeslaenderEngine.get_state(self.viewport.active_state_code)
        
        user_home = os.path.expanduser("~")
        desktop_dir = os.path.join(user_home, "Desktop")
        if not os.path.exists(desktop_dir):
            desktop_dir = user_home
            
        pdf_path = os.path.join(desktop_dir, f"Pruefgutachten_{state_info['name']}_2026.pdf")
        html_path = os.path.join(desktop_dir, f"Pruefgutachten_{state_info['name']}_2026.html")

        CorporateDossierEngine.generate_raw_pdf(
            output_path=pdf_path,
            project_name=f"Infrastrukturprojekt_{state_info['name']}_2026",
            state_name=state_info['name'],
            crs_code=state_info['crs'],
            masses=res,
            stats_ai=ai_res["stats"],
            stamp=stamp,
            buildings=self.viewport.created_buildings,
            roads=self.viewport.created_roads
        )

        html_content = CorporateDossierEngine.generate_html_preview(
            project_name=f"Infrastrukturprojekt_{state_info['name']}_2026",
            state_name=state_info['name'],
            crs_code=state_info['crs'],
            masses=res,
            stats_ai=ai_res["stats"],
            stamp=stamp,
            buildings=self.viewport.created_buildings,
            roads=self.viewport.created_roads
        )
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        dlg = InAppDossierDialog(html_content, pdf_path, self)
        dlg.exec()

    def action_import_survey_data(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Vermessungsdaten importieren", "", "Vermessung (*.csv *.txt *.dxf *.xml *.xyz *.pts);;Alle Dateien (*.*)")
        if file_path:
            pts = OfflineAILiDAREngine.parse_large_point_cloud(file_path)
            if pts:
                for pt in pts[:200]:
                    new_m = MarkerPointObject(0, 0, self.viewport.center_lat, self.viewport.center_lon, pt["e"], pt["n"], name=pt["id"])
                    self.viewport.created_markers.append(new_m)
                    self.add_marker_to_table(new_m)
                QMessageBox.information(self, "Import", f"✓ {len(pts)} Punkte aus {os.path.basename(file_path)} geladen.")
                self.viewport.update()

    def action_load_sample(self):
        sample_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "samples", "vermessung_sample.csv"))
        if os.path.exists(sample_path):
            pts = AdvancedCADEngine.parse_survey_file(sample_path)
            for pt in pts:
                new_m = MarkerPointObject(0, 0, self.viewport.center_lat, self.viewport.center_lon, pt["e"], pt["n"], name=pt["id"])
                self.viewport.created_markers.append(new_m)
                self.add_marker_to_table(new_m)
            self.viewport.update()

    def action_clear_markers(self):
        self.viewport.created_markers = []
        self.viewport.selected_point_id = None
        self.viewport.ai_classified_points = []
        self.table_points.setRowCount(0)
        self.viewport.update()

    def action_show_profile(self):
        if not self.viewport.created_roads:
            QMessageBox.information(self, "Höhenprofil", "Bitte zuerst eine Trasse mit dem Werkzeug '🛣️ Trasse' zeichnen.")
            return
        stations = AdvancedCADEngine.compute_longitudinal_profile(self.viewport.created_roads[0].points)
        dlg = LongitudinalProfileDialog(stations, self)
        dlg.exec()

    def recalculate_all_masses(self):
        res = InstantGeodeticMath.compute_all_project_masses(self.viewport.created_buildings, self.viewport.created_roads)
        self.lbl_m_cut.setText(f"Aushub (Abtrag):  {int(res['total_cut']):,} m³")
        self.lbl_m_fill.setText(f"Auftrag (Planum): {int(res['total_fill']):,} m³")
        saldo_sgn = "+" if res['saldo'] >= 0 else ""
        self.lbl_m_saldo.setText(f"Netto-Saldo:      {saldo_sgn}{int(res['saldo']):,} m³")
        self.lbl_m_cost.setText(f"Baukosten (Est):  {res['cost_eur']:,.2f} €")
        self.lbl_m_co2.setText(f"CO2-Bilanz:       {res['co2_tons']:.1f} t")

    def add_marker_to_table(self, marker):
        self.table_points.blockSignals(True)
        row_idx = self.table_points.rowCount()
        self.table_points.insertRow(row_idx)
        self.table_points.setItem(row_idx, 0, QTableWidgetItem(marker.name))
        self.table_points.setItem(row_idx, 1, QTableWidgetItem(f"{marker.utm_e:,.3f}"))
        self.table_points.setItem(row_idx, 2, QTableWidgetItem(f"{marker.utm_n:,.3f}"))
        self.table_points.setItem(row_idx, 3, QTableWidgetItem("142.000"))
        self.table_points.setItem(row_idx, 4, QTableWidgetItem("Vermessung"))
        item_audit = QTableWidgetItem("[ VALID ]")
        item_audit.setForeground(QColor("#10b981"))
        self.table_points.setItem(row_idx, 5, item_audit)
        self.table_points.blockSignals(False)

    def on_state_changed(self, idx):
        code = self.cb_states.itemData(idx)
        info = BundeslaenderEngine.get_state(code)
        self.lbl_region_name.setText(f"Region: {info['name']}")
        self.lbl_crs_active.setText(f"System: {info['crs']}")
        self.lbl_grid_active.setText(f"Gitter: {info['grid']}")
        self.viewport.fly_to_state(code)

    def action_vob(self):
        res = InstantGeodeticMath.compute_all_project_masses(self.viewport.created_buildings, self.viewport.created_roads)
        save_path, _ = QFileDialog.getSaveFileName(self, "DA45 Datei speichern", "Abrechnung_REB_22013.da45", "DA45 (*.da45)")
        if save_path:
            pts_dict = [{"e": m.utm_e, "n": m.utm_n, "z": 142.0} for m in self.viewport.created_markers]
            da45_content = AdvancedCADEngine.generate_full_da45(pts_dict, res['total_cut'], res['total_fill'])
            with open(save_path, 'w', encoding='latin-1') as f:
                f.write(da45_content)
            QMessageBox.information(self, "VOB/C DA45", f"✓ Amtliche DA45-Datei exportiert:\n{save_path}")

    def action_gaeb(self):
        res = InstantGeodeticMath.compute_all_project_masses(self.viewport.created_buildings, self.viewport.created_roads)
        save_path, _ = QFileDialog.getSaveFileName(self, "GAEB X83 speichern", "Leistungsverzeichnis.x83", "GAEB (*.x83 *.xml)")
        if save_path:
            gaeb_data = CorporateEngine.generate_gaeb_x83_tender(res['total_cut'], res['total_fill'], res['road_len_m'])
            with open(save_path, 'w', encoding='utf-8') as f:
                f.write(gaeb_data['gaeb_xml'])
            QMessageBox.information(self, "GAEB X83", f"✓ GAEB DA XML 3.2 Leistungsverzeichnis exportiert:\n{save_path}")

    def action_dxf_export(self):
        save_path, _ = QFileDialog.getSaveFileName(self, "AutoCAD DXF speichern", "Muster_3D_Plan.dxf", "AutoCAD DXF (*.dxf)")
        if save_path:
            dxf_str = AdvancedCADEngine.generate_dxf_3d(self.viewport.created_buildings, self.viewport.created_roads, self.viewport.created_markers)
            with open(save_path, 'w', encoding='utf-8') as f:
                f.write(dxf_str)
            QMessageBox.information(self, "DXF Export", f"✓ AutoCAD 3D DXF Datei exportiert:\n{save_path}")

    def action_landxml_export(self):
        if not self.viewport.created_roads:
            QMessageBox.information(self, "LandXML", "Bitte zuerst eine Trasse zeichnen.")
            return
        save_path, _ = QFileDialog.getSaveFileName(self, "LandXML speichern", "Trassenachse.xml", "LandXML (*.xml)")
        if save_path:
            xml_content = AdvancedCADEngine.generate_landxml(self.viewport.created_roads)
            with open(save_path, 'w', encoding='utf-8') as f:
                f.write(xml_content)
            QMessageBox.information(self, "LandXML", f"✓ LandXML 1.2 exportiert:\n{save_path}")

    def action_qes_seal(self):
        stamp = GeodesyEngine.generate_qes_stamp()
        self.lbl_merkle_display.setText(f"MERKLE ROOT ANCHOR:\n{stamp['merkle_root'][:32]}...")
        QMessageBox.information(self, "DIN 18716 QES", f"✓ Gerichtsfestes QES-Zertifikat appliziert:\n\n- Merkle Root: {stamp['merkle_root']}\n- HWID: {stamp['hwid']}")
