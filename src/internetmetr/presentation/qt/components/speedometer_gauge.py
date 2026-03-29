from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont, QPainter, QPen
from PyQt6.QtWidgets import QWidget


class SpeedometerGauge(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._value = 0.0
        self._minimum = 0.0
        self._maximum = 100.0
        self._unit = "Mbps"
        self._title = "Ready"
        self._is_dark = False
        self.setMinimumHeight(250)

    def set_theme(self, is_dark: bool) -> None:
        self._is_dark = is_dark
        self.update()

    def set_range(self, minimum: float, maximum: float, unit: str, title: str) -> None:
        self._minimum = minimum
        self._maximum = max(minimum + 1e-6, maximum)
        self._unit = unit
        self._title = title
        self._value = minimum
        self.update()

    def set_value(self, value: float) -> None:
        self._value = min(self._maximum, max(self._minimum, value))
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        size = min(w, h) - 24
        cx = w // 2
        cy = h // 2 + 18
        radius = size // 2

        background = QColor("#0B1018") if self._is_dark else QColor("#F8FBFF")
        ring_bg = QColor("#1B2534") if self._is_dark else QColor("#DCE7F7")
        ring_fg = QColor("#38BDF8") if self._is_dark else QColor("#2563EB")
        text_main = QColor("#E6EFFA") if self._is_dark else QColor("#0F172A")
        text_secondary = QColor("#99ADC7") if self._is_dark else QColor("#475569")

        painter.fillRect(self.rect(), background)

        rect = (cx - radius, cy - radius, radius * 2, radius * 2)

        start_angle = 210 * 16
        span_total = -240 * 16

        pen_bg = QPen(ring_bg, 16)
        pen_bg.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen_bg)
        painter.drawArc(*rect, start_angle, span_total)

        ratio = (self._value - self._minimum) / (self._maximum - self._minimum)
        ratio = min(1.0, max(0.0, ratio))
        span_value = int(span_total * ratio)

        pen_fg = QPen(ring_fg, 16)
        pen_fg.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen_fg)
        painter.drawArc(*rect, start_angle, span_value)

        title_font = QFont()
        title_font.setPointSize(11)
        title_font.setBold(True)
        painter.setFont(title_font)
        painter.setPen(text_secondary)
        painter.drawText(0, cy - 52, w, 24, Qt.AlignmentFlag.AlignCenter, self._title)

        value_font = QFont()
        value_font.setPointSize(24)
        value_font.setBold(True)
        painter.setFont(value_font)
        painter.setPen(text_main)
        painter.drawText(0, cy - 14, w, 40, Qt.AlignmentFlag.AlignCenter, f"{self._value:.2f}")

        unit_font = QFont()
        unit_font.setPointSize(11)
        painter.setFont(unit_font)
        painter.setPen(text_secondary)
        painter.drawText(0, cy + 24, w, 24, Qt.AlignmentFlag.AlignCenter, self._unit)

        scale_font = QFont()
        scale_font.setPointSize(9)
        painter.setFont(scale_font)
        painter.setPen(text_secondary)
        painter.drawText(cx - radius + 2, cy + radius - 2, 60, 20, Qt.AlignmentFlag.AlignLeft, f"{self._minimum:.0f}")
        painter.drawText(cx + radius - 62, cy + radius - 2, 60, 20, Qt.AlignmentFlag.AlignRight, f"{self._maximum:.0f}")
