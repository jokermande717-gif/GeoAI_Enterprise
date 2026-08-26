import sys
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QStackedWidget, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
from PyQt5.QtCore import QUrl
from PyQt5.QtWebEngineWidgets import QWebEngineView

class GeoAIEnterpriseMaster(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GeoAI Overlord Enterprise 2026.1 - Dual-Workspace Master Suite")
        self.resize(1600, 950)

        # Main Widget & Layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Stacked Views (0: 3D Web Sandbox, 1: 2D GIS/CAD)
        self.stack = QStackedWidget()

        # View 1: 3D City Builder & Sandbox Web Engine
        self.web_view = QWebEngineView()
        current_dir = os.path.dirname(os.path.abspath(__file__))
        html_path = os.path.join(current_dir, "web", "index.html")
        if not os.path.exists(html_path):
            html_path = os.path.join(sys._MEIPASS, "web", "index.html")
        
        self.web_view.load(QUrl.fromLocalFile(html_path))
        self.stack.addWidget(self.web_view)

        main_layout.addWidget(self.stack)

def main():
    app = QApplication(sys.argv)
    window = GeoAIEnterpriseMaster()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
