import sys
import os
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtGui import QIcon
from src.gui.main_window import MainWindow
from src.core.licensing_engine import SovereignLicenseEngine
from src.gui.activation_dialog import CommercialActivationDialog

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # فحص التفعيل المشفر على هذا الجهاز
    if not SovereignLicenseEngine.is_system_activated():
        dlg = CommercialActivationDialog()
        if dlg.exec() != CommercialActivationDialog.Accepted:
            sys.exit(0)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
