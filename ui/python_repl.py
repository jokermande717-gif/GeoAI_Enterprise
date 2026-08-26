from typing import Any, Dict, Optional
from PyQt6.QtWidgets import QVBoxLayout, QWidget
from qtconsole.inprocess import QtInProcessKernelManager
from qtconsole.rich_jupyter_widget import RichJupyterWidget


class JupyterConsoleWidget(QWidget):
    """In-Process Jupyter Python REPL Konsole für Entwickler und Prüfingenieure.

    Ermöglicht die interaktive Skriptausführung mit direktem Zugriff auf alle
    interne Instanzen (Datenbanken, Geodäsie-Engines, Audit-Log) zur Laufzeit.
    """

    def __init__(
        self,
        custom_vars: Optional[Dict[str, Any]] = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.custom_vars = custom_vars or {}
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.kernel_manager = QtInProcessKernelManager()
        self.kernel_manager.start_kernel()
        self.kernel = self.kernel_manager.kernel
        self.kernel.gui = "qt"

        self.kernel_client = self.kernel_manager.client()
        self.kernel_client.start_channels()

        self.jupyter_widget = RichJupyterWidget(self)
        self.jupyter_widget.kernel_manager = self.kernel_manager
        self.jupyter_widget.kernel_client = self.kernel_client

        self.jupyter_widget.style_sheet = """
            QPlainTextEdit {
                background-color: #0f172a;
                color: #f8fafc;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 13px;
            }
        """
        self.jupyter_widget.syntax_style = "monokai"

        layout.addWidget(self.jupyter_widget)

        self.push_variables(self.custom_vars)

    def push_variables(self, var_dict: Dict[str, Any]) -> None:
        if var_dict and hasattr(self.kernel, "shell"):
            self.kernel.shell.push(var_dict)

    def closeEvent(self, event: Any) -> None:
        self.kernel_client.stop_channels()
        self.kernel_manager.shutdown_kernel()
        super().closeEvent(event)