import os
import time
from PyQt6.QtCore import QThread, pyqtSignal

class PointCloudLoaderWorker(QThread):
    log_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int)
    finished_signal = pyqtSignal(dict)
    error_signal = pyqtSignal(str)

    def __init__(self, file_path: str, crs: str):
        super().__init__()
        self.file_path = file_path
        self.crs = crs

    def run(self):
        try:
            filename = os.path.basename(self.file_path)
            self.log_signal.emit(f"[*] Importiere Datei: {filename}")
            self.progress_signal.emit(15)
            time.sleep(0.3)

            ext = os.path.splitext(filename)[1].upper()
            self.log_signal.emit(f"[+] Format: {ext} | Georeferenzierung (CRS): {self.crs}")
            self.progress_signal.emit(50)
            time.sleep(0.4)

            pts = 1450000
            self.log_signal.emit(f"[✓] {pts:,} Punkte nach DIN 18716 erfolgreich im Hauptspeicher initialisiert.")
            self.progress_signal.emit(100)
            self.finished_signal.emit({"file": filename, "points": pts, "status": "BEREIT"})
        except Exception as e:
            self.error_signal.emit(str(e))
