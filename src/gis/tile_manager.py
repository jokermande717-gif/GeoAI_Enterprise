import os
import math
from PySide6.QtCore import QObject, Signal, QUrl
from PySide6.QtGui import QPixmap
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply

APP_CACHE_DIR = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "GeoAI_Enterprise", "tile_cache")
os.makedirs(APP_CACHE_DIR, exist_ok=True)

class RealMapTileEngine(QObject):
    tile_received = Signal(int, int, int, QPixmap)

    BASEMAP_PROVIDERS = {
        "satellite": {
            "name": "Satellit (ESRI World Imagery)",
            "url": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
        },
        "topo": {
            "name": "Topographisch (OpenTopoMap)",
            "url": "https://tile.opentopomap.org/{z}/{x}/{y}.png"
        },
        "osm": {
            "name": "Straßen & Kataster (OpenStreetMap)",
            "url": "https://tile.openstreetmap.org/{z}/{x}/{y}.png"
        }
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.nam = QNetworkAccessManager(self)
        self.nam.finished.connect(self.on_reply_finished)
        self.memory_cache = {}
        self.active_provider = "satellite"

    def get_tile(self, x, y, z):
        key = (self.active_provider, z, x, y)
        if key in self.memory_cache:
            return self.memory_cache[key]

        disk_path = os.path.join(APP_CACHE_DIR, self.active_provider, str(z), str(x), f"{y}.png")
        if os.path.exists(disk_path):
            pix = QPixmap(disk_path)
            if not pix.isNull():
                self.memory_cache[key] = pix
                return pix

        if self.active_provider in self.BASEMAP_PROVIDERS:
            url_tmpl = self.BASEMAP_PROVIDERS[self.active_provider]["url"]
            url_str = url_tmpl.format(x=x, y=y, z=z)
            req = QNetworkRequest(QUrl(url_str))
            req.setRawHeader(b"User-Agent", b"GeoAI-Enterprise-Overlord/2026.1")
            req.setAttribute(QNetworkRequest.User, (self.active_provider, z, x, y, disk_path))
            self.nam.get(req)

        return None

    def on_reply_finished(self, reply):
        data = reply.attribute(QNetworkRequest.User)
        if not data:
            reply.deleteLater()
            return
        prov, z, x, y, disk_path = data

        if reply.error() == QNetworkReply.NoError:
            img_bytes = reply.readAll()
            pix = QPixmap()
            if pix.loadFromData(img_bytes):
                self.memory_cache[(prov, z, x, y)] = pix
                try:
                    os.makedirs(os.path.dirname(disk_path), exist_ok=True)
                    with open(disk_path, "wb") as f:
                        f.write(img_bytes.data())
                except Exception:
                    pass
                if prov == self.active_provider:
                    self.tile_received.emit(z, x, y, pix)
        reply.deleteLater()

    @staticmethod
    def lat_lon_to_utm(lat, lon):
        x = (lon - 9.0) * 111319.49 * math.cos(math.radians(lat)) + 500000.0
        y = lat * 110574.0
        return x, y
