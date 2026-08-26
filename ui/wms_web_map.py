import webbrowser
from PyQt6.QtCore import QUrl
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

# محاولة تحميل QtWebEngineWidgets مع معالجة خطأ DLL
try:
    from PyQt6.QtWebEngineWidgets import QWebEngineView

    HAS_WEBENGINE = True
except ImportError:
    HAS_WEBENGINE = False


class WMSTimOnlineMap(QWidget):
    """QWebEngineView-Komponente zur Anzeige interaktiver 2D-Geokarten.

    Integriert Leaflet.js mit Unterstützung für OpenStreetMap und Geobasis-WMS-Dienste
    aus Nordrhein-Westfalen (z.B. TIM-online NRW).
    """

    LEAFLET_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TIM-online NRW Geokarte</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <style>
        html, body, #map {
            width: 100%;
            height: 100%;
            margin: 0;
            padding: 0;
            background-color: #0f172a;
        }
    </style>
</head>
<body>
    <div id="map"></div>
    <script>
        var map = L.map('map').setView([51.4818, 7.2162], 13);

        var osmLayer = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            maxZoom: 19,
            attribution: '&copy; OpenStreetMap-Mitwirkende'
        }).addTo(map);

        var nrwWmsLayer = L.tileLayer.wms('https://www.wms.nrw.de/geobasis/wms_nw_dtk', {
            layers: 'nw_dtk_col',
            format: 'image/png',
            transparent: true,
            attribution: '&copy; Geobasis NRW'
        });

        var baseMaps = {
            "OpenStreetMap": osmLayer
        };
        var overlayMaps = {
            "Topographische Karte NRW (WMS)": nrwWmsLayer
        };
        L.control.layers(baseMaps, overlayMaps).addTo(map);

        function addGeoMarker(lat, lng, popupText) {
            L.marker([lat, lng]).addTo(map)
                .bindPopup(popupText)
                .openPopup();
        }
    </script>
</body>
</html>
"""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.current_lat = 51.4818
        self.current_lng = 7.2162
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        if HAS_WEBENGINE:
            self.web_view = QWebEngineView(self)
            layout.addWidget(self.web_view)
            self.web_view.setHtml(
                self.LEAFLET_HTML_TEMPLATE, QUrl("https://localhost/")
            )
        else:
            # واجهة احتياطية في حال تعذر تحميل WebEngine DLL
            fallback_box = QWidget()
            fb_layout = QVBoxLayout(fallback_box)

            lbl_info = QLabel(
                "🗺️ TIM-online / WMS NRW Karte\n(QtWebEngine Standby Mode)"
            )
            lbl_info.setStyleSheet(
                "color: #38bdf8; font-size: 14px; font-weight: bold; text-align: center;"
            )

            btn_open_browser = QPushButton("الخريطة في المتصفح External Browser")
            btn_open_browser.clicked.connect(self._open_in_browser)

            fb_layout.addWidget(lbl_info)
            fb_layout.addWidget(btn_open_browser)
            layout.addWidget(fallback_box)

    def set_center(self, lat: float, lng: float, zoom: int = 15) -> None:
        self.current_lat = lat
        self.current_lng = lng
        if HAS_WEBENGINE and hasattr(self, "web_view"):
            js_code = f"map.setView([{lat}, {lng}], {zoom});"
            self.web_view.page().runJavaScript(js_code)

    def add_marker(
        self, lat: float, lng: float, popup_text: str = "Messpunkt"
    ) -> None:
        self.current_lat = lat
        self.current_lng = lng
        if HAS_WEBENGINE and hasattr(self, "web_view"):
            clean_text = popup_text.replace("'", "\\'")
            js_code = f"addGeoMarker({lat}, {lng}, '{clean_text}');"
            self.web_view.page().runJavaScript(js_code)

    def _open_in_browser(self) -> None:
        url = f"https://www.openstreetmap.org/?mlat={self.current_lat}&mlon={self.current_lng}#map=15/{self.current_lat}/{self.current_lng}"
        webbrowser.open(url)