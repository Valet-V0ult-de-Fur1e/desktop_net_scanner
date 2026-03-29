from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import QFrame, QLabel, QVBoxLayout


class MetricCard(QFrame):
    def __init__(self, title: str, value: str = "-") -> None:
        super().__init__()
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setObjectName("metricCard")
        self._is_dark = False
        self._base_color = QColor("#FFFFFF")
        self._highlight_color = QColor("#EAF3FF")
        self._border_color = "#E2E8F0"
        self._title_color = "#475569"
        self._value_color = "#0F172A"
        self._pulse_timer = QTimer(self)
        self._pulse_timer.setSingleShot(True)
        self._pulse_timer.setInterval(140)
        self._pulse_timer.timeout.connect(self._reset_to_base_style)

        self._title_label = QLabel(title)
        self._title_label.setObjectName("metricCardTitle")
        self._title_label.setAlignment(Qt.AlignmentFlag.AlignLeft)

        self._value_label = QLabel(value)
        self._value_label.setObjectName("metricCardValue")
        value_font = QFont()
        value_font.setPointSize(14)
        value_font.setBold(True)
        self._value_label.setFont(value_font)

        layout = QVBoxLayout(self)
        layout.addWidget(self._title_label)
        layout.addWidget(self._value_label)

        self._apply_style(self._base_color)

    def set_dark_mode(self, is_dark: bool) -> None:
        self._is_dark = is_dark
        self._pulse_timer.stop()
        if is_dark:
            self._base_color = QColor("#11151C")
            self._highlight_color = QColor("#162236")
            self._border_color = "#263244"
            self._title_color = "#9FB1C8"
            self._value_color = "#F3F7FF"
        else:
            self._base_color = QColor("#FFFFFF")
            self._highlight_color = QColor("#EAF3FF")
            self._border_color = "#E2E8F0"
            self._title_color = "#475569"
            self._value_color = "#0F172A"

        self._apply_style(self._base_color)

    def set_value(self, value: str, animate: bool = True) -> None:
        self._value_label.setText(value)
        if not animate:
            self._pulse_timer.stop()
            self._apply_style(self._base_color)
            return

        self._pulse_timer.stop()
        self._apply_style(self._highlight_color)
        self._pulse_timer.start()

    def _reset_to_base_style(self) -> None:
        self._apply_style(self._base_color)

    def _apply_style(self, background_color: QColor) -> None:
        self.setStyleSheet(
            f"""
            QFrame#metricCard {{
                background: {background_color.name()};
                border: 1px solid {self._border_color};
                border-radius: 16px;
                padding: 10px;
            }}
            QFrame#metricCard QLabel {{
                color: {self._title_color};
            }}
            QFrame#metricCard QLabel#metricCardValue {{
                color: {self._value_color};
            }}
            """
        )
