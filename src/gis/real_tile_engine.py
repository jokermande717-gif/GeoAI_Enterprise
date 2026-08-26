import os
import math
import urllib.request
from PySide6.QtCore import QObject, Signal, QThread
from PySide6.QtGui import QPixmap, QImage

CACHE_DIR = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "GeoAI_Enterprise", "cache_tiles")
os.makedirs(CACHE_DIR, exist_ok=True)

class TileWorker(QThread):
    tile_loaded = Signal(int, int, int, str, QPixmap)

    def __init__(self, z, x, y, provider="satellite"):
        super().__init__()
        self.z = z
        self.x = x
        self.y = y
        self.provider = provider

    def run(self):
        disk_path = os.path.join(CACHE_DIR, self.provider, str(self.z), str(self.x), f"{self.y}.png")
        if os.path.exists(disk_path):
            pix = QPixmap(disk_path)
            if not pix.isNull():
                self.tile_loaded.emit(self.z, self.x, self.y, self.provider, pix)
                return

        # URL Providers
        if self.provider == "satellite":
            url = f"https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{self.z}/{self.y}/{self.x}"
        elif self.provider == "topo":
            url = f"https://tile.opentopomap.org/{self.z}/{self.x}/{self.y}.png"
        else:
            url = f"https://tile.openstreetmap.org/{self.z}/{self.x}/{self.y}.png"

        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'GeoAI-Overlord-2026/Enterprise (Desktop CAD)'})
            with urllib.request.urlopen(req, timeout=3.5) as response:
                img_data = response.read()
                pix = QPixmap()
                if pix.loadFromData(img_data):
                    os.makedirs(os.path.dirname(disk_path), exist_ok=True)
                    with open(disk_path, "wb") as f:
                        f.write(img_data)
                    self.tile_loaded.emit(self.z, self.x, self.y, self.provider, pix)
        except Exception:
            pass

class LiveMapManager(QObject):
    update_viewport = Signal()

    def __init__(self):
        super().__init__()
        self.tile_cache = {}
        self.active_workers = []

    def get_tile(self, z, x, y, provider="satellite"):
        key = (provider, z, x, y)
        if key in self.tile_cache:
            return self.tile_cache[key]

        disk_path = os.path.join(CACHE_DIR, provider, str(z), str(x), f"{y}.png")
        if os.path.exists(disk_path):
            pix = QPixmap(disk_path)
            if not pix.isNull():
                self.tile_cache[key] = pix
                return pix

        # Asynchronous fetch
        if len(self.active_workers) < 12:
            worker = TileWorker(z, x, y, provider)
            worker.tile_loaded.connect(self.on_tile_loaded)
            self.active_workers.append(worker)
            worker.finished.connect(lambda: self.cleanup_worker(worker))
            worker.start()

        return None

    def on_tile_loaded(self, z, x, y, provider, pix):
        self.tile_cache[(provider, z, x, y)] = pix
        self.update_viewport.emit()

    def cleanup_worker(self, worker):
        if worker in self.active_workers:
            self.active_workers.remove(worker)

GLOBAL_MAP_MANAGER = LiveMapManager()
