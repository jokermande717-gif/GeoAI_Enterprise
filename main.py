import sys
from PyQt6.QtWidgets import QApplication
from ui.main_window import GeoAIMainWindow
from core.embedded_server import EmbeddedServerThread

def main():
    # تشغيل السيرفر تلقائياً في الخلفية
    server_daemon = EmbeddedServerThread(host="127.0.0.1", port=8000)
    server_daemon.start()

    app = QApplication(sys.argv)
    window = GeoAIMainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
