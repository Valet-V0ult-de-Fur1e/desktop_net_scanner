from datetime import datetime

from PyQt6.QtWidgets import (
    QHBoxLayout,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class TraceWindow(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Request Trace")
        self.resize(720, 420)

        self._log = QTextEdit()
        self._log.setReadOnly(True)

        self._clear_button = QPushButton("Clear")
        self._clear_button.clicked.connect(self._log.clear)

        top = QHBoxLayout()
        top.addStretch(1)
        top.addWidget(self._clear_button)

        layout = QVBoxLayout(self)
        layout.addLayout(top)
        layout.addWidget(self._log)

    def append_line(self, text: str) -> None:
        now = datetime.now().strftime("%H:%M:%S")
        self._log.append(f"[{now}] {text}")
