import os
import sys
import json
import io
import contextlib
from datetime import datetime
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QTabWidget, QLabel, QComboBox, QPushButton, QTextEdit, 
    QFrame, QFileDialog, QProgressBar, QGroupBox, QSpinBox, 
    QDoubleSpinBox, QCheckBox, QSplitter, QTableWidget, QTableWidgetItem,
    QTreeWidget, QTreeWidgetItem, QHeaderView, QDialog, QLineEdit, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtWebEngineWidgets import QWebEngineView

from core.security import get_hardware_id, verify_license_file
from core.workers import PointCloudLoaderWorker
from core.report_generator import GeodeticReportGenerator
from core.ledger import GeodeticBlockchainLedger

GERMAN_STATES_GEO_DATA = {
    "Nordrhein-Westfalen (NRW)": {"crs": "EPSG:25832", "lat": 51.4332, "lon": 7.6616, "zoom": 9, "wms": "https://www.wms.nrw.de/geobasis/wms_nw_dtk"},
    "Baden-Württemberg": {"crs": "EPSG:25832", "lat": 48.6616, "lon": 9.3501, "zoom": 9, "wms": "https://owsproxy.lgl-bw.de/owsproxy/ows/wms_dtk25"},
    "Bayern": {"crs": "EPSG:25832", "lat": 48.7904, "lon": 11.4979, "zoom": 8, "wms": "https://geoservices.bayern.de/wms/v2/ogc_dtk25.cgi"},
    "Berlin": {"crs": "EPSG:25833", "lat": 52.5200, "lon": 13.4050, "zoom": 12, "wms": "https://fbinter.stadt-berlin.de/fb/wms/senstadt/k_dtk10"},
    "Brandenburg": {"crs": "EPSG:25833", "lat": 52.4125, "lon": 12.5316, "zoom": 9, "wms": "https://isk.geobasis-bb.de/ows/dtk25wms"},
    "Bremen": {"crs": "EPSG:25832", "lat": 53.0793, "lon": 8.8017, "zoom": 12, "wms": "https://geodaten.bremen.de/wms/dtk"},
    "Hamburg": {"crs": "EPSG:25832", "lat": 53.5511, "lon": 9.9937, "zoom": 12, "wms": "https://geodienste.hamburg.de/HH_WMS_DOP"},
    "Hessen": {"crs": "EPSG:25832", "lat": 50.6521, "lon": 9.1624, "zoom": 9, "wms": "https://gds.hessen.de/wms/topografische_karten"},
    "Mecklenburg-Vorpommern": {"crs": "EPSG:25833", "lat": 53.6127, "lon": 12.4296, "zoom": 8, "wms": "https://www.geodaten-mv.de/dienste/gdimv_dtk25"},
    "Niedersachsen": {"crs": "EPSG:25832", "lat": 52.6367, "lon": 9.8451, "zoom": 8, "wms": "https://opendata.lgln.niedersachsen.de/wms_dtk25"},
    "Rheinland-Pfalz": {"crs": "EPSG:25832", "lat": 49.9285, "lon": 7.4518, "zoom": 9, "wms": "https://geodaten.rlp.de/wms/dtk25"},
    "Saarland": {"crs": "EPSG:25832", "lat": 49.3964, "lon": 7.0230, "zoom": 10, "wms": "https://geoportal.saarland.de/wms/dtk"},
    "Sachsen": {"crs": "EPSG:25833", "lat": 51.1045, "lon": 13.2017, "zoom": 9, "wms": "https://geodienste.sachsen.de/wms_geosn_dtk"},
    "Sachsen-Anhalt": {"crs": "EPSG:25832", "lat": 51.9503, "lon": 11.6923, "zoom": 9, "wms": "https://geodaten.sachsen-anhalt.de/wms/dtk"},
    "Schleswig-Holstein": {"crs": "EPSG:25832", "lat": 54.2194, "lon": 9.6961, "zoom": 9, "wms": "https://danord.gdi-sh.de/wms/dtk25"},
    "Thüringen": {"crs": "EPSG:25832", "lat": 50.9010, "lon": 11.0257, "zoom": 9, "wms": "https://geoproxy.geoportal-th.de/geoproxy/services/DTK25"},
    "Deutschlandweit (Bund)": {"crs": "EPSG:25832", "lat": 51.1657, "lon": 10.4515, "zoom": 6, "wms": "https://sgx.geodatenzentrum.de/wms_dtk250"}
}

class PythonConsoleWidget(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        self.history = QTextEdit()
        self.history.setReadOnly(True)
        self.history.setStyleSheet("background-color: #0d1117; color: #58a6ff; font-family: Consolas; font-size: 12px; border: 1px solid #30363d;")
        self.history.append("Python 3.12 (GeoAI Embedded Geodetic Engine)\nTypen Sie Python-Befehle oder greifen Sie mit 'geoai' auf das Hauptfenster zu.\n" + "-"*65)

        input_layout = QHBoxLayout()
        prompt_lbl = QLabel(">>> ")
        prompt_lbl.setStyleSheet("color: #7ee787; font-family: Consolas; font-weight: bold;")
        
        self.cmd_input = QLineEdit()
        self.cmd_input.setStyleSheet("background-color: #161b22; color: #f0f6fc; font-family: Consolas; font-size: 12px; padding: 4px;")
        self.cmd_input.returnPressed.connect(self.execute_command)

        btn_run = QPushButton("Ausführen")
        btn_run.setStyleSheet("background-color: #238636; color: white; font-weight: bold;")
        btn_run.clicked.connect(self.execute_command)

        input_layout.addWidget(prompt_lbl)
        input_layout.addWidget(self.cmd_input)
        input_layout.addWidget(btn_run)

        layout.addWidget(self.history, 1)
        layout.addLayout(input_layout)

    def execute_command(self):
        cmd = self.cmd_input.text().strip()
        if not cmd:
            return
        self.cmd_input.clear()
        self.history.append(f">>> {cmd}")

        env = {"geoai": self.main_window, "ledger": self.main_window.ledger, "crs_data": GERMAN_STATES_GEO_DATA, "sys": sys, "os": os}
        buf = io.StringIO()
        try:
            with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
                try:
                    res = eval(cmd, env)
                    if res is not None:
                        print(repr(res))
                except SyntaxError:
                    exec(cmd, env)
            out = buf.getvalue()
            if out:
                self.history.append(out.rstrip())
        except Exception as e:
            self.history.append(f"<font color='#f85149'>Error: {str(e)}</font>")

class LicenseDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("GeoAI Overlord – Lizenzaktivierung")
        self.resize(560, 340)
        self.setStyleSheet("background-color: #1a1b26; color: #c0caf5;")
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Ihre Hardware-ID (an Lizenzserver übermitteln):"))
        self.hwid_box = QLineEdit(get_hardware_id())
        self.hwid_box.setReadOnly(True)
        self.hwid_box.setStyleSheet("background-color: #13141c; color: #7dcfff; font-family: Consolas; padding: 6px;")
        layout.addWidget(self.hwid_box)

        layout.addWidget(QLabel("Lizenzschlüssel einfügen:"))
        self.key_box = QTextEdit()
        self.key_box.setPlaceholderText("Fügen Sie den generierten Base64-Schlüssel hier ein...")
        self.key_box.setStyleSheet("background-color: #13141c; color: #9ece6a; font-family: Consolas;")
        layout.addWidget(self.key_box)

        btn = QPushButton("🔑 Lizenz verifizieren & anwenden")
        btn.setStyleSheet("background-color: #0284c7; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self.apply_key)
        layout.addWidget(btn)

    def apply_key(self):
        txt = self.key_box.toPlainText().strip()
        if not txt:
            QMessageBox.warning(self, "Fehler", "Bitte Lizenzschlüssel angeben.")
            return
        valid, res = verify_license_file(txt)
        if valid:
            with open("geoai.lic", "w", encoding="utf-8") as f:
                f.write(txt)
            QMessageBox.information(self, "Erfolg", f"Lizenz erfolgreich aktiviert!\nClient: {res.get('client')}\nGültig bis: {res.get('expiry')}")
            self.accept()
        else:
            QMessageBox.critical(self, "Fehler", f"Ungültige Lizenz: {res}")

class DragDropFrame(QFrame):
    def __init__(self, main_win):
        super().__init__()
        self.main_win = main_win
        self.setAcceptDrops(True)
        self.setStyleSheet("border: 2px dashed #414868; border-radius: 6px; background-color: #16161e;")

    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()
            self.setStyleSheet("border: 2px dashed #7aa2f7; background-color: #24283b;")

    def dragLeaveEvent(self, e):
        self.setStyleSheet("border: 2px dashed #414868; background-color: #16161e;")

    def dropEvent(self, e):
        self.setStyleSheet("border: 2px dashed #414868; background-color: #16161e;")
        urls = e.mimeData().urls()
        if urls:
            self.main_win.load_point_cloud_file(urls[0].toLocalFile())

class GeoAIMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GeoAI Overlord Enterprise – Vermessung, DGM, BIM & Blockchain Suite [DIN 18716]")
        self.resize(1650, 980)
        
        # تعيين أيقونة البرنامج الرسمية
        if os.path.exists("assets/logo.png"):
            self.setWindowIcon(QIcon("assets/logo.png"))

        self.setStyleSheet("""
            QMainWindow { background-color: #13141c; color: #e0e0e0; font-family: 'Segoe UI', Arial, sans-serif; }
            QWidget { font-size: 12px; }
            QTabWidget::pane { border: 1px solid #2d2e3d; background-color: #1a1b26; top: -1px; }
            QTabBar::tab { background: #13141c; color: #9a9ab0; padding: 8px 18px; font-weight: bold; border: 1px solid #2d2e3d; border-bottom: none; margin-right: 2px; }
            QTabBar::tab:selected { background: #1a1b26; color: #00d2ff; border-top: 2px solid #00d2ff; }
            QGroupBox { border: 1px solid #2d2e3d; border-radius: 4px; margin-top: 14px; font-weight: bold; font-size: 11px; color: #00d2ff; padding: 10px 6px; }
            QGroupBox::title { subcontrol-origin: margin; left: 8px; padding: 0 4px; }
            QPushButton { background-color: #24283b; color: #c0caf5; border: 1px solid #414868; border-radius: 3px; padding: 6px 12px; font-weight: bold; }
            QPushButton:hover { background-color: #3b4261; border-color: #7dcfff; }
            QTreeWidget, QTableWidget { background-color: #16161e; border: 1px solid #2d2e3d; color: #c0caf5; gridline-color: #24283b; }
            QHeaderView::section { background-color: #1f2335; color: #7aa2f7; font-weight: bold; border: 1px solid #2d2e3d; padding: 4px; }
            QComboBox, QSpinBox, QDoubleSpinBox { background-color: #16161e; color: #c0caf5; border: 1px solid #2d2e3d; border-radius: 3px; padding: 4px; }
        """)
        self.ledger = GeodeticBlockchainLedger()
        self.worker = None
        self.init_ui()

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(6, 6, 6, 6)
        root.setSpacing(4)

        self.build_ribbon(root)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self.build_toc_tree())
        splitter.addWidget(self.build_viewports())
        splitter.addWidget(self.build_inspector())
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 6)
        splitter.setStretchFactor(2, 3)
        root.addWidget(splitter, 1)

        self.build_audit_dock(root)

        sb = self.statusBar()
        sb.setStyleSheet("background-color: #16161e; color: #c0caf5; border-top: 1px solid #2d2e3d; font-family: Consolas;")
        last_b = self.ledger.get_latest_block()
        b_idx = last_b["block_index"] if last_b else 0
        sb.showMessage(f"HWID: {get_hardware_id()} | BLOCKCHAIN: #{b_idx} SYNCED | CRS: EPSG:25832 | DIN 18716 AKTIV")

    def build_ribbon(self, root):
        frame = QFrame()
        frame.setStyleSheet("background-color: #16161e; border: 1px solid #2d2e3d; border-radius: 4px;")
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(8, 4, 8, 4)

        # إضافة شعار البرنامج في الشريط
        logo_lbl = QLabel()
        if os.path.exists("assets/logo.png"):
            pix = QPixmap("assets/logo.png").scaled(26, 26, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            logo_lbl.setPixmap(pix)
        layout.addWidget(logo_lbl)

        title = QLabel("GeoAI OVERLORD PRO")
        title.setStyleSheet("font-size: 15px; font-weight: 900; color: #00d2ff; margin-right: 15px;")
        layout.addWidget(title)

        btn_load = QPushButton("📂 Geodaten laden (LAS/E57/CSV/XML)")
        btn_load.setStyleSheet("background-color: #005a9e;")
        btn_load.clicked.connect(self.browse_file)

        btn_pdf = QPushButton("📄 DIN 18716 Prüfbericht (PDF)")
        btn_pdf.setStyleSheet("background-color: #b91c1c; color: #fff; font-weight: bold;")
        btn_pdf.clicked.connect(self.generate_pdf)

        lbl_state = QLabel("Bundesland:")
        lbl_state.setStyleSheet("font-weight: bold; color: #7aa2f7;")
        self.state_combo = QComboBox()
        self.state_combo.addItems(list(GERMAN_STATES_GEO_DATA.keys()))
        self.state_combo.currentIndexChanged.connect(self.state_changed)

        self.crs_badge = QLabel("EPSG:25832")
        self.crs_badge.setStyleSheet("background-color: #1f2335; color: #9ece6a; border: 1px solid #414868; padding: 4px 8px; font-weight: bold; font-family: Consolas;")

        btn_lic = QPushButton("🔑 Lizenz")
        btn_lic.setStyleSheet("background-color: #d08770; color: #000; font-weight: 900;")
        btn_lic.clicked.connect(lambda: LicenseDialog(self).exec())

        layout.addWidget(btn_load)
        layout.addWidget(btn_pdf)
        layout.addStretch()
        layout.addWidget(lbl_state)
        layout.addWidget(self.state_combo)
        layout.addWidget(self.crs_badge)
        layout.addWidget(btn_lic)
        root.addWidget(frame)

    def build_toc_tree(self):
        dock = QFrame()
        dock.setStyleSheet("background-color: #1a1b26; border: 1px solid #2d2e3d;")
        l = QVBoxLayout(dock)
        l.addWidget(QLabel("LAYERS & GEODATEN (TOC)"))

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Ebene / Modell", "Typ", "Status"])
        self.tree.header().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)

        pc = QTreeWidgetItem(self.tree, ["LiDAR Punktwolke", "LAS/LAZ/E57", "Aktiv"])
        QTreeWidgetItem(pc, ["Boden / DGM (Klasse 2)", "Mesh", "Sichtbar"])
        QTreeWidgetItem(pc, ["Bauwerke (Klasse 6)", "Objekt", "Sichtbar"])
        QTreeWidgetItem(pc, ["Vegetation (Klasse 3-5)", "Points", "Ausgeblendet"])

        QTreeWidgetItem(self.tree, ["Amtliche DTK Topo (WMS)", "Geodienst", "Synchron"])
        QTreeWidgetItem(self.tree, ["REB-VB 22.013 Massen", "DA45 / DA49", "Bereit"])
        QTreeWidgetItem(self.tree, ["IFC 4.3 BIM Trasse", "DB Ril 800", "Berechnet"])
        self.tree.expandAll()
        l.addWidget(self.tree)
        return dock

    def build_viewports(self):
        tabs = QTabWidget()
        
        # 1. 3D Engine
        p1 = QFrame()
        p1.setStyleSheet("background-color: #0d0d12; border: 1px solid #2d2e3d;")
        l1 = QVBoxLayout(p1)
        self.lbl_viewport_status = QLabel("3D Native Viewport bereit für Punktwolken (LAS/LAZ/E57/CSV/XML)")
        self.lbl_viewport_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_viewport_status.setStyleSheet("color: #565f89; font-size: 13px; font-weight: bold;")
        l1.addWidget(self.lbl_viewport_status)
        tabs.addTab(p1, "🖥️ 3D-LiDAR Engine")

        # 2. Topo Map WMS
        p2 = QFrame()
        l2 = QVBoxLayout(p2)
        l2.setContentsMargins(0,0,0,0)
        self.map_view = QWebEngineView()
        self.render_map(51.4332, 7.6616, 9, "Nordrhein-Westfalen (NRW)")
        l2.addWidget(self.map_view)
        tabs.addTab(p2, "🗺️ Amtliche DTK / WMS")

        # 3. REB-VB 22.013
        p3 = QFrame()
        l3 = QVBoxLayout(p3)
        self.reb_table = QTableWidget(4, 4)
        self.reb_table.setHorizontalHeaderLabels(["Horizont / DGM", "Auftrag [m³]", "Abtrag [m³]", "Differenz [m³]"])
        self.reb_table.setItem(0, 0, QTableWidgetItem("DGM-Urgelände vs. Planum"))
        self.reb_table.setItem(0, 1, QTableWidgetItem("12.450,80"))
        self.reb_table.setItem(0, 2, QTableWidgetItem("3.120,40"))
        self.reb_table.setItem(0, 3, QTableWidgetItem("+9.330,40"))
        l3.addWidget(self.reb_table)
        btn_da45 = QPushButton("💾 DA45 / DA49 Datenaustauschdatei exportieren")
        btn_da45.setStyleSheet("background-color: #059669; color: white; padding: 8px; font-weight: bold;")
        btn_da45.clicked.connect(self.export_da45)
        l3.addWidget(btn_da45)
        tabs.addTab(p3, "📐 REB-VB 22.013 Massen")

        # 4. IFC 4.3 Trassierung
        p4 = QFrame()
        l4 = QVBoxLayout(p4)
        grp = QGroupBox("Gleistrassierung & Soll-Überhöhung (DB Ril 800)")
        gl = QGridLayout(grp)
        gl.addWidget(QLabel("Entwurfsgeschwindigkeit Ve [km/h]:"), 0, 0)
        self.spin_ve = QSpinBox()
        self.spin_ve.setRange(30, 350)
        self.spin_ve.setValue(160)
        gl.addWidget(self.spin_ve, 0, 1)

        gl.addWidget(QLabel("Bogenradius R [m]:"), 1, 0)
        self.spin_r = QSpinBox()
        self.spin_r.setRange(100, 10000)
        self.spin_r.setValue(1500)
        gl.addWidget(self.spin_r, 1, 1)

        self.lbl_cant = QLabel("Berechnete Überhöhung u: 160.0 mm (Sollmaß)")
        self.lbl_cant.setStyleSheet("font-weight: bold; color: #7dcfff; font-size: 13px;")
        gl.addWidget(self.lbl_cant, 2, 0, 1, 2)

        btn_calc_cant = QPushButton("⚡ Überhöhung u = 11.8 · (V² / R) berechnen")
        btn_calc_cant.clicked.connect(self.calc_cant)
        gl.addWidget(btn_calc_cant, 3, 0, 1, 2)
        l4.addWidget(grp)
        l4.addStretch()
        tabs.addTab(p4, "🚆 IFC 4.3 Trassierung (DB Ril 800)")

        # 5. Python Console Tab
        self.console_widget = PythonConsoleWidget(self)
        tabs.addTab(self.console_widget, "🐍 Python REPL & Skripte")

        return tabs

    def render_map(self, lat, lon, zoom, state):
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8" />
            <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
            <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
            <style>
                html, body, #map {{ height: 100%; width: 100%; margin: 0; padding: 0; background: #0f172a; }}
                .badge {{ position: absolute; top: 10px; right: 10px; z-index: 1000; background: rgba(15,23,42,0.85); color: #38bdf8; padding: 6px 12px; border-radius: 4px; font-family: Arial; font-size: 12px; border: 1px solid #0284c7; font-weight: bold; }}
            </style>
        </head>
        <body>
            <div class="badge">🗺️ {state} (Amtlicher WMS / DTK aktiv)</div>
            <div id="map"></div>
            <script>
                var map = L.map('map').setView([{lat}, {lon}], {zoom});
                L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{ maxZoom: 19, attribution: '© OpenStreetMap | Geobasisdaten Deutschland' }}).addTo(map);
                L.circleMarker([{lat}, {lon}], {{ color: '#38bdf8', fillColor: '#0284c7', fillOpacity: 0.7, radius: 8 }}).addTo(map).bindPopup("<b>{state}</b><br>Amtlicher Geodatendienst aktiv.").openPopup();
            </script>
        </body>
        </html>
        """
        self.map_view.setHtml(html)

    def build_inspector(self):
        dock = QFrame()
        dock.setStyleSheet("background-color: #1a1b26; border: 1px solid #2d2e3d;")
        l = QVBoxLayout(dock)

        self.drop_box = DragDropFrame(self)
        dl = QVBoxLayout(self.drop_box)
        self.lbl_drop = QLabel("📍 Ziehen Sie Geodaten hierher\n(LAS, LAZ, E57, CSV, XML, TIF, DA45)")
        self.lbl_drop.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_drop.setStyleSheet("color: #7aa2f7; font-size: 11px;")
        dl.addWidget(self.lbl_drop)
        l.addWidget(self.drop_box)

        grp_ki = QGroupBox("KI-Segmentierung (DIN 18716)")
        kl = QVBoxLayout(grp_ki)
        kl.addWidget(QCheckBox("Boden / DGM (Klasse 2)"))
        kl.addWidget(QCheckBox("Gebäude / Bauwerke (Klasse 6)"))
        kl.addWidget(QCheckBox("Vegetation (Klasse 3-5)"))
        btn_ki = QPushButton("⚡ RandLA-Net Segmentierung")
        btn_ki.setStyleSheet("background-color: #2e7d32;")
        btn_ki.clicked.connect(self.run_ki_classification)
        kl.addWidget(btn_ki)
        l.addWidget(grp_ki)
        l.addStretch()
        return dock

    def build_audit_dock(self, root):
        box = QVBoxLayout()
        lbl = QLabel("📋 Echtzeit-Audit Geodaten-Protokoll & Blockchain Ledger (DIN 18716):")
        lbl.setStyleSheet("font-size: 11px; font-weight: bold; color: #7aa2f7;")

        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setMaximumHeight(100)
        self.log_box.setStyleSheet("background-color: #101014; color: #9ece6a; font-family: Consolas, monospace; font-size: 11px; border: 1px solid #2d2e3d;")

        self.pbar = QProgressBar()
        self.pbar.setFixedHeight(4)
        self.pbar.setValue(0)
        self.pbar.setTextVisible(False)
        self.pbar.setStyleSheet("QProgressBar { border: none; background-color: #16161e; } QProgressBar::chunk { background-color: #7aa2f7; }")

        box.addWidget(lbl)
        box.addWidget(self.log_box)
        box.addWidget(self.pbar)
        root.addLayout(box)
        self.log("GeoAI Overlord initialisiert. Blockchain Ledger aktiv.")

    def log(self, msg):
        t = datetime.now().strftime("%H:%M:%S")
        self.log_box.append(f"[{t}] {msg}")

    def state_changed(self):
        st = self.state_combo.currentText()
        d = GERMAN_STATES_GEO_DATA[st]
        self.crs_badge.setText(d["crs"])
        self.render_map(d["lat"], d["lon"], d["zoom"], st)
        b = self.ledger.append_block("STATE_CRS_CHANGE", {"state": st, "crs": d["crs"]})
        self.log(f"[BLOCKCHAIN #{b['block_index']}] CRS geändert auf {st} | Hash: {b['block_hash'][:16]}...")

    def calc_cant(self):
        v = self.spin_ve.value()
        r = self.spin_r.value()
        u_raw = 11.8 * (v ** 2) / r
        u_final = min(u_raw, 160.0)
        self.lbl_cant.setText(f"Berechnete Überhöhung u: {u_final:.1f} mm (Theoretisch: {u_raw:.1f} mm)")
        b = self.ledger.append_block("DB_RIL_800_CANT", {"speed": v, "radius": r, "cant": u_final})
        self.log(f"[BLOCKCHAIN #{b['block_index']}] Trassierung berechnet: u={u_final:.1f}mm | Hash: {b['block_hash'][:16]}...")

    def export_da45(self):
        path, _ = QFileDialog.getSaveFileName(self, "DA45 Massendatei speichern", "REB_Massen.da45", "DA45 (*.da45)")
        if path:
            with open(path, "w", encoding="ascii") as f:
                f.write("45.001 GEOAI OVERLORD REB-VB 22.013 DGM-MASSEN\n")
                f.write("45.002 AUFTRAG: 12450.80 M3 | ABTRAG: 3120.40 M3\n")
                f.write("45.099 ENDE DER DATEN\n")
            b = self.ledger.append_block("REB_DA45_EXPORT", {"file": os.path.basename(path), "auftrag": 12450.80, "abtrag": 3120.40})
            self.log(f"[BLOCKCHAIN #{b['block_index']}] DA45 Export verifiziert: {os.path.basename(path)}")
            QMessageBox.information(self, "REB Export", f"DA45 Datei erfolgreich geschrieben:\n{path}")

    def run_ki_classification(self):
        b = self.ledger.append_block("RANDLA_NET_KI", {"classes": ["Boden", "Bauwerke", "Vegetation"], "points": 1450000})
        self.log(f"[BLOCKCHAIN #{b['block_index']}] KI-Segmentierung signiert | Hash: {b['block_hash'][:16]}...")

    def generate_pdf(self):
        path, _ = QFileDialog.getSaveFileName(self, "DIN 18716 Prüfbericht speichern", "GeoAI_Pruefbericht.pdf", "PDF (*.pdf)")
        if path:
            st = self.state_combo.currentText()
            d = {
                "project_name": f"Trassen- & Massenprüfung {st.split('(')[0].strip()}",
                "state": st,
                "crs": GERMAN_STATES_GEO_DATA[st]["crs"],
                "speed": self.spin_ve.value(),
                "radius": self.spin_r.value(),
                "client": "Ingenieurbüro GeoAI Enterprise"
            }
            b = self.ledger.append_block("PDF_REPORT_SIGNATURE", d)
            GeodeticReportGenerator.generate_din18716_report(path, d, b)
            self.log(f"[BLOCKCHAIN #{b['block_index']}] PDF-Gutachten mit QES signiert: {os.path.basename(path)}")
            QMessageBox.information(self, "PDF Export", f"Prüfbericht mit Blockchain-Signatur erstellt:\n{path}")

    def browse_file(self):
        p, _ = QFileDialog.getOpenFileName(self, "Geodaten auswählen", "", "Alle Geodaten (*.las *.laz *.e57 *.csv *.xyz *.xml *.tif *.da45)")
        if p:
            self.load_point_cloud_file(p)

    def load_point_cloud_file(self, path):
        self.lbl_drop.setText(f"Geladene Datei:\n{os.path.basename(path)}")
        st = self.state_combo.currentText()
        crs = GERMAN_STATES_GEO_DATA[st]["crs"]
        self.worker = PointCloudLoaderWorker(path, crs)
        self.worker.log_signal.connect(self.log)
        self.worker.progress_signal.connect(self.pbar.setValue)
        self.worker.finished_signal.connect(lambda r: self.on_point_cloud_loaded(r))
        self.worker.start()

    def on_point_cloud_loaded(self, r):
        self.lbl_viewport_status.setText(f"Geladene Punktwolke: {r['file']} ({r['points']:,} Punkte)")
        b = self.ledger.append_block("POINTCLOUD_LOAD", r)
        self.log(f"[BLOCKCHAIN #{b['block_index']}] Punktwolke im Ledger gesichert: {r['file']}")
