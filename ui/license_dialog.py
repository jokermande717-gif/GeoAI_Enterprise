"""
ui/license_dialog.py
--------------------
واجهة المستخدم لطلب التفعيل وعرض معرّف الجهاز (Machine ID).
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QTextEdit, QLineEdit, QPushButton, QMessageBox, QHBoxLayout
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt
from core.license_manager import LicenseManager


class LicenseActivationDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("GeoAI Overlord - Produktaktivierung & Lizenzierung")
        self.resize(550, 320)
        self.setStyleSheet("background-color: #0f172a; color: #f8fafc; font-family: 'Segoe UI';")
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        title = QLabel("Software-Aktivierung erforderlich")
        title.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        title.setStyleSheet("color: #38bdf8;")
        layout.addWidget(title)

        info_lbl = QLabel("Bitte übermitteln Sie Ihre Hardware-ID an den Support, um einen Lizenzschlüssel zu erhalten:")
        info_lbl.setWordWrap(True)
        layout.addWidget(info_lbl)

        # عرض Machine ID
        hw_layout = QHBoxLayout()
        self.hw_id_edit = QLineEdit(LicenseManager.get_machine_id())
        self.hw_id_edit.setReadOnly(True)
        self.hw_id_edit.setStyleSheet("background-color: #020617; border: 1px solid #334155; padding: 6px; color: #facc15; font-weight: bold;")
        
        btn_copy = QPushButton("Kopieren")
        btn_copy.setStyleSheet("background-color: #1e293b; border: 1px solid #3b82f6; padding: 6px 12px; font-weight: bold;")
        btn_copy.clicked.connect(self._copy_machine_id)
        
        hw_layout.addWidget(self.hw_id_edit)
        hw_layout.addWidget(btn_copy)
        layout.addLayout(hw_layout)

        layout.addWidget(QLabel("Lizenzschlüssel (Serial-Key) hier einfügen:"))
        self.serial_edit = QTextEdit()
        self.serial_edit.setStyleSheet("background-color: #020617; border: 1px solid #334155; color: #38bdf8; font-family: monospace;")
        layout.addWidget(self.serial_edit)

        # أزرار التفعيل والخروج
        btn_layout = QHBoxLayout()
        self.btn_activate = QPushButton("Aktivieren")
        self.btn_activate.setStyleSheet("background-color: #2563eb; color: white; padding: 10px; font-weight: bold; border-radius: 4px;")
        self.btn_activate.clicked.connect(self._slot_activate)

        self.btn_cancel = QPushButton("Beenden")
        self.btn_cancel.setStyleSheet("background-color: #1e293b; color: #94a3b8; padding: 10px; border-radius: 4px;")
        self.btn_cancel.clicked.connect(self.reject)

        btn_layout.addWidget(self.btn_activate)
        btn_layout.addWidget(self.btn_cancel)
        layout.addLayout(btn_layout)

    def _copy_machine_id(self):
        from PyQt6.QtWidgets import QApplication
        QApplication.clipboard().setText(self.hw_id_edit.text())
        QMessageBox.information(self, "Kopiert", "Hardware-ID in die Zwischenablage kopiert.")

    def _slot_activate(self):
        serial = self.serial_edit.toPlainText().strip()
        if not serial:
            QMessageBox.warning(self, "Fehler", "Bitte Lizenzschlüssel eingeben.")
            return

        is_valid, msg = LicenseManager.verify_license_string(serial)
        if is_valid:
            LicenseManager.save_license(serial)
            QMessageBox.information(self, "Erfolg", f"Aktivierung erfolgreich!\n{msg}")
            self.accept()
        else:
            QMessageBox.critical(self, "Aktivierungsfehler", msg)