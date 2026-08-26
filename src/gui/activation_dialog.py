import sys
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QFrame, QApplication
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor
from src.core.licensing_engine import SovereignLicenseEngine

class CommercialActivationDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("GeoAI Overlord // Enterprise License Activation")
        self.setFixedSize(540, 360)
        self.setStyleSheet("background-color: #030712; color: #f8fafc;")
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        self.hwid = SovereignLicenseEngine.get_hardware_fingerprint()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)

        # Title
        lbl_t = QLabel("🔒 GeoAI OVERLORD // LIZENZAKTIVIERUNG")
        lbl_t.setStyleSheet("font-family: Consolas; font-size: 15px; font-weight: 900; color: #00d2ff;")
        layout.addWidget(lbl_t)

        lbl_desc = QLabel("Dieses System ist an Ihre Hardware gebunden (Node-Locked DIN 18716).\nBitte geben Sie Ihren autorisierten Unternehmens-Lizenzschlüssel ein.")
        lbl_desc.setStyleSheet("font-size: 11px; color: #94a3b8; line-height: 1.4;")
        layout.addWidget(lbl_desc)

        # HWID Display Frame
        hwid_box = QFrame()
        hwid_box.setStyleSheet("background: #060e1d; border: 1px solid #1e293b; border-radius: 6px; padding: 8px;")
        hb_layout = QHBoxLayout(hwid_box)
        hb_layout.addWidget(QLabel("Hardware Enclave ID (HWID):"))
        self.txt_hwid = QLineEdit(self.hwid)
        self.txt_hwid.setReadOnly(True)
        self.txt_hwid.setStyleSheet("background: #030712; color: #f59e0b; font-family: Consolas; font-weight: bold; border: 1px solid #334155; padding: 4px;")
        hb_layout.addWidget(self.txt_hwid)
        
        btn_copy = QPushButton("Kopieren")
        btn_copy.setStyleSheet("background: #1e293b; color: #38bdf8; font-weight: bold; padding: 4px 10px;")
        btn_copy.clicked.connect(self.copy_hwid)
        hb_layout.addWidget(btn_copy)
        layout.addWidget(hwid_box)

        # License Key Input
        layout.addWidget(QLabel("Unternehmens-Lizenzschlüssel:"))
        self.txt_key = QLineEdit()
        self.txt_key.setPlaceholderText("GEOAI-XXXX-XXXX-XXXX-XXXX-XXXX")
        self.txt_key.setStyleSheet("background: #060e1d; color: #10b981; font-family: Consolas; font-weight: bold; font-size: 12px; border: 1.5px solid #00d2ff; padding: 8px; border-radius: 6px;")
        layout.addWidget(self.txt_key)

        # Action Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        btn_activate = QPushButton("🔑 Lizenz Aktivieren")
        btn_activate.setStyleSheet("background: #0284c7; color: white; font-weight: 900; padding: 9px 18px; border-radius: 6px;")
        btn_activate.clicked.connect(self.action_activate)
        btn_layout.addWidget(btn_activate)

        btn_exit = QPushButton("Beenden")
        btn_exit.setStyleSheet("background: #1e293b; color: #94a3b8; padding: 9px 18px; border-radius: 6px;")
        btn_exit.clicked.connect(self.reject)
        btn_layout.addWidget(btn_exit)

        layout.addLayout(btn_layout)

    def copy_hwid(self):
        QApplication.clipboard().setText(self.hwid)
        QMessageBox.information(self, "Kopiert", "✓ HWID in die Zwischenablage kopiert.\nSenden Sie diesen Code an Ihren Administrator/Vertrieb.")

    def action_activate(self):
        key = self.txt_key.text().strip()
        if SovereignLicenseEngine.activate_system(key):
            QMessageBox.information(self, "Aktivierung Erfolgreich", "✓ GeoAI Overlord wurde erfolgreich verifiziert und dauerhaft lizenziert!")
            self.accept()
        else:
            QMessageBox.critical(self, "Ungültige Lizenz", "❌ Der eingegebene Lizenzschlüssel ist ungültig oder passt nicht zu dieser Hardware-ID.")
