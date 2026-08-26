import sys
import os
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QStackedWidget, QButtonGroup
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon

from src.gui.sandbox_widget import SandboxWorkspaceWidget
from src.gui.pro_cad_widget import ProCADWorkspaceWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GeoAI Overlord Enterprise 2026.1 - Dual-Workspace Master Suite")
        self.resize(1640, 980)
        self.setMinimumSize(1300, 840)
        self.apply_master_styling()
        self.build_ui()

    def apply_master_styling(self):
        self.setStyleSheet("""
            QMainWindow { background-color: #020408; }
            QWidget { color: #f8fafc; font-family: 'Segoe UI', system-ui, sans-serif; }
            
            /* أزرار التبديل العلوية في الهيدر بتصميم ساطع وبارز جداً */
            QPushButton#mode_sandbox, QPushButton#mode_pro {
                background: #081426;
                color: #38bdf8;
                font-weight: 900;
                font-size: 12px;
                padding: 7px 18px;
                border-radius: 6px;
                border: 1px solid #0284c7;
                font-family: 'Segoe UI', sans-serif;
            }
            QPushButton#mode_sandbox:hover, QPushButton#mode_pro:hover {
                background: #0284c7;
                color: #ffffff;
                border-color: #00d2ff;
            }
            QPushButton#mode_sandbox:checked, QPushButton#mode_pro:checked {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #00d2ff, stop:1 #0284c7);
                color: #020408;
                font-weight: 900;
                border: 1.5px solid #ffffff;
            }
            
            /* أزرار العمليات العامة */
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #0284c7, stop:1 #0369a1);
                color: #ffffff; font-weight: 900; font-size: 11.5px; padding: 8px 14px; border-radius: 6px;
                border: 1px solid #38bdf8; font-family: 'Segoe UI', sans-serif;
            }
            QPushButton:hover { background: #00d2ff; color: #020408; }
            
            /* زر الأداة المفعّلة: أخضر نيون فسفوري واضح جداً */
            QPushButton:checked {
                background: #10b981;
                color: #020408;
                font-weight: 900;
                border: 2px solid #34d399;
            }
            
            QComboBox {
                background: #03060a; border: 1px solid #151e2e; border-radius: 6px; padding: 6px 10px;
                color: #f8fafc; font-family: 'Consolas', monospace; font-size: 11.5px;
            }
            QTableWidget, QTreeWidget {
                background: #03060a; border: 1px solid #151e2e; border-radius: 6px; color: #cbd5e1;
                font-family: 'Consolas', monospace; font-size: 11.5px; gridline-color: #0e1624;
            }
            QHeaderView::section { background: #080d16; color: #00d2ff; font-weight: bold; padding: 6px; border: 1px solid #151e2e; font-size: 11.5px; }
            QGroupBox {
                border: 1px solid #151e2e; border-radius: 8px; margin-top: 14px; padding-top: 14px;
                font-weight: 900; font-family: 'Consolas', monospace; font-size: 11.5px; color: #00d2ff; background: #04070d;
            }
            QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 8px; background: #04070d; }
        """)

    def build_ui(self):
        root_widget = QWidget()
        self.setCentralWidget(root_widget)
        root_layout = QVBoxLayout(root_widget)
        root_layout.setContentsMargins(14, 10, 14, 10)
        root_layout.setSpacing(10)

        # Master Header Bar with Dual-Workspace Switcher
        top_header = QFrame()
        top_header.setStyleSheet("background: #060a12; border: 1px solid #151e2e; border-radius: 8px; padding: 6px 14px;")
        th_layout = QHBoxLayout(top_header)
        th_layout.setContentsMargins(0, 0, 0, 0)

        lbl_brand = QLabel("◬ GeoAI OVERLORD // ENTERPRISE 2026.1")
        lbl_brand.setStyleSheet("font-size: 15px; font-weight: 900; color: #00d2ff; font-family: 'Consolas', monospace;")
        th_layout.addWidget(lbl_brand)
        th_layout.addSpacing(25)

        # Top Mode Switcher Buttons with Explicit ObjectNames
        self.mode_group = QButtonGroup(self)
        self.mode_group.setExclusive(True)

        self.btn_mode_sandbox = QPushButton("🌍 MODE 1: 3D World Sandbox")
        self.btn_mode_sandbox.setObjectName("mode_sandbox")
        self.btn_mode_sandbox.setCheckable(True)
        self.btn_mode_sandbox.setChecked(True)
        self.btn_mode_sandbox.clicked.connect(lambda: self.switch_mode(0))
        self.mode_group.addButton(self.btn_mode_sandbox)
        th_layout.addWidget(self.btn_mode_sandbox)

        self.btn_mode_pro = QPushButton("⚙️ MODE 2: Professional Geodesy CAD")
        self.btn_mode_pro.setObjectName("mode_pro")
        self.btn_mode_pro.setCheckable(True)
        self.btn_mode_pro.clicked.connect(lambda: self.switch_mode(1))
        self.mode_group.addButton(self.btn_mode_pro)
        th_layout.addWidget(self.btn_mode_pro)

        th_layout.addStretch()

        lbl_status = QLabel("[ DUAL-WORKSPACE ACTIVE ]  [ AIR-GAP: VERIFIED ]")
        lbl_status.setStyleSheet("font-size: 11px; font-weight: bold; color: #10b981; font-family: 'Consolas', monospace;")
        th_layout.addWidget(lbl_status)
        root_layout.addWidget(top_header)

        # Stacked Workspaces (Mode 1 & Mode 2)
        self.stack = QStackedWidget()
        self.sandbox_view = SandboxWorkspaceWidget(self)
        self.pro_cad_view = ProCADWorkspaceWidget(self)

        self.stack.addWidget(self.sandbox_view)  # Index 0: Mode 1
        self.stack.addWidget(self.pro_cad_view)  # Index 1: Mode 2
        root_layout.addWidget(self.stack, 1)

    def switch_mode(self, idx):
        self.stack.setCurrentIndex(idx)
        if idx == 0:
            self.btn_mode_sandbox.setChecked(True)
        else:
            self.btn_mode_pro.setChecked(True)
