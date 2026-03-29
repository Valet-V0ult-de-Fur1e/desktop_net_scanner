from collections import deque
from pathlib import Path

from PyQt6.QtCore import QEasingCurve, QPropertyAnimation, QSize, QThread, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QIcon, QPalette
from PyQt6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from internetmetr.presentation.qt.components.speedometer_gauge import SpeedometerGauge
from internetmetr.presentation.qt.components.trace_window import TraceWindow
from internetmetr.presentation.qt.components.interface_table import InterfaceTable
from internetmetr.presentation.qt.components.metric_card import MetricCard
from internetmetr.presentation.qt.viewmodels.main_view_model import MainViewModel


class SpeedTestWorker(QThread):
    finished_ok = pyqtSignal(float, float, float, str)
    progress_stage = pyqtSignal(int)
    trace_line = pyqtSignal(str)
    stage_label = pyqtSignal(str)
    failed = pyqtSignal(str)

    def __init__(self, view_model: MainViewModel) -> None:
        super().__init__()
        self._view_model = view_model

    def _trace(self, line: str) -> None:
        self.trace_line.emit(line)

        lower_line = line.lower()
        if "initializing" in lower_line:
            self.progress_stage.emit(10)
            self.stage_label.emit("Initializing speed test")
        elif "nearest test server" in lower_line:
            self.progress_stage.emit(25)
            self.stage_label.emit("Selecting nearest server")
        elif "download throughput" in lower_line:
            self.progress_stage.emit(45)
            self.stage_label.emit("Measuring download")
        elif "upload throughput" in lower_line:
            self.progress_stage.emit(75)
            self.stage_label.emit("Measuring upload")
        elif "final report" in lower_line:
            self.progress_stage.emit(92)
            self.stage_label.emit("Finalizing statistics")

    def run(self) -> None:
        try:
            self.progress_stage.emit(5)
            self.trace_line.emit("Speed test task started")
            result = self._view_model.run_speed_test(trace=self._trace)
            self.progress_stage.emit(100)
            self.trace_line.emit("Speed test task finished")
            self.finished_ok.emit(
                float(result.download_mbps),
                float(result.upload_mbps),
                float(result.ping_ms),
                str(result.server_name),
            )
        except Exception as exc:  # noqa: BLE001
            self.failed.emit(str(exc))


class MainWindow(QMainWindow):
    def __init__(self, view_model: MainViewModel) -> None:
        super().__init__()
        self._view_model = view_model
        self._speed_worker: SpeedTestWorker | None = None
        self._trace_window = TraceWindow()
        self._is_dark_theme = False
        self._previous_score: int | None = None
        self._download_history: deque[float] = deque(maxlen=50)
        self._upload_history: deque[float] = deque(maxlen=50)
        self._ping_history: deque[float] = deque(maxlen=50)
        self._current_scan_stage = "idle"
        self._scan_tick = 0

        self.setWindowTitle("InternetMetr - Windows")
        self.resize(1280, 860)

        self._set_window_icon()

        root = QWidget()
        root.setObjectName("appRoot")
        scroll = QScrollArea()
        scroll.setObjectName("appScroll")
        scroll.setWidgetResizable(True)
        scroll.setWidget(root)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        self.setCentralWidget(scroll)

        self._hostname_card = MetricCard("Hostname")
        self._local_ip_card = MetricCard("Local IPv4")
        self._public_ip_card = MetricCard("Public IP")
        self._download_card = MetricCard("Download")
        self._upload_card = MetricCard("Upload")
        self._ping_card = MetricCard("Ping")
        self._quality_card = MetricCard("Quality")
        self._gauge = SpeedometerGauge()
        self._gauge.set_range(0, 500, "Mbps", "Download speed")

        self._table = InterfaceTable()
        self._status_label = QLabel("Ready")
        self._comparison_label = QLabel("Comparison with previous test: no data yet")
        self._comparison_label.setObjectName("comparisonLabel")
        self._stage_label = QLabel("Press Start research to begin network diagnostics")
        self._stage_label.setObjectName("stageLabel")

        self._progress_label = QLabel("Speed test progress")
        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 100)
        self._progress_bar.setValue(0)
        self._progress_bar.setTextVisible(True)

        self._stats_panel = QWidget()
        self._stats_grid = QGridLayout(self._stats_panel)
        self._stats_values: dict[tuple[str, str], QLabel] = {}
        self._build_stats_panel()

        self._refresh_button = QPushButton("")
        self._refresh_button.setIcon(self._resolve_icon("view-refresh", "refresh.svg"))
        self._speed_button = QPushButton("")
        self._speed_button.setObjectName("startResearchButton")
        self._trace_button = QPushButton("")
        self._trace_button.setIcon(self._resolve_icon("document-preview", "app_icon.svg"))
        self._theme_button = QPushButton("")
        self._theme_button.setCheckable(True)
        self._configure_icon_buttons()
        self._theme_icon_animation = QPropertyAnimation(self._theme_button, b"iconSize", self)
        self._theme_icon_animation.setDuration(180)
        self._theme_icon_animation.setStartValue(QSize(18, 18))
        self._theme_icon_animation.setKeyValueAt(0.5, QSize(24, 24))
        self._theme_icon_animation.setEndValue(QSize(20, 20))
        self._update_theme_button_icon(False)

        card_row_1 = QHBoxLayout()
        card_row_1.addWidget(self._hostname_card)
        card_row_1.addWidget(self._local_ip_card)
        card_row_1.addWidget(self._public_ip_card)

        card_row_2 = QHBoxLayout()
        card_row_2.addWidget(self._download_card)
        card_row_2.addWidget(self._upload_card)
        card_row_2.addWidget(self._ping_card)
        card_row_2.addWidget(self._quality_card)

        top_bar = QHBoxLayout()
        top_bar.addWidget(self._refresh_button)
        top_bar.addStretch(1)
        top_bar.addWidget(self._trace_button)
        top_bar.addWidget(self._theme_button)

        start_row = QHBoxLayout()
        start_row.addStretch(1)
        start_row.addWidget(self._speed_button)
        start_row.addStretch(1)

        layout = QVBoxLayout(root)
        layout.addLayout(top_bar)
        layout.addWidget(self._gauge)
        layout.addLayout(start_row)
        layout.addWidget(self._progress_label)
        layout.addWidget(self._progress_bar)
        layout.addWidget(self._stage_label)
        layout.addLayout(card_row_1)
        layout.addLayout(card_row_2)
        layout.addWidget(self._comparison_label)
        layout.addWidget(self._stats_panel)
        layout.addWidget(self._table)
        layout.addWidget(self._status_label)

        self._refresh_button.clicked.connect(self.refresh_network_data)
        self._speed_button.clicked.connect(self.start_speed_test)
        self._trace_button.clicked.connect(self._toggle_trace_window)
        self._theme_button.toggled.connect(self._on_theme_toggled)

        self._apply_theme(is_dark=False)

        self._refresh_timer = QTimer(self)
        self._refresh_timer.setInterval(5000)
        self._refresh_timer.timeout.connect(self.refresh_network_data)
        self._refresh_timer.start()

        self._progress_timer = QTimer(self)
        self._progress_timer.setInterval(240)
        self._progress_timer.timeout.connect(self._advance_progress_while_running)

        self._scan_gauge_timer = QTimer(self)
        self._scan_gauge_timer.setInterval(140)
        self._scan_gauge_timer.timeout.connect(self._animate_live_gauge)

        self.setWindowOpacity(0.0)
        self._fade_animation = QPropertyAnimation(self, b"windowOpacity", self)
        self._fade_animation.setDuration(560)
        self._fade_animation.setStartValue(0.0)
        self._fade_animation.setEndValue(1.0)
        self._fade_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._fade_animation.start()

        self.refresh_network_data()

    def _set_window_icon(self) -> None:
        icon_path = Path(__file__).resolve().parent / "assets" / "app_icon.svg"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
            self._trace_window.setWindowIcon(QIcon(str(icon_path)))

    def _build_stats_panel(self) -> None:
        headers = ["Metric", "Current", "Average", "Minimum", "Maximum"]
        for column, title in enumerate(headers):
            header = QLabel(title)
            header.setObjectName("statsHeader")
            self._stats_grid.addWidget(header, 0, column)

        metrics = ["Download (Mbps)", "Upload (Mbps)", "Ping (ms)"]
        fields = ["current", "avg", "min", "max"]

        for row, metric in enumerate(metrics, start=1):
            metric_label = QLabel(metric)
            metric_label.setObjectName("statsMetric")
            self._stats_grid.addWidget(metric_label, row, 0)

            for column, field in enumerate(fields, start=1):
                value_label = QLabel("-")
                value_label.setObjectName("statsValue")
                self._stats_grid.addWidget(value_label, row, column)
                self._stats_values[(metric, field)] = value_label

    def _configure_icon_buttons(self) -> None:
        self._refresh_button.setToolTip("Refresh network data")
        self._trace_button.setToolTip("Open or hide trace window")
        self._theme_button.setToolTip("Toggle dark and light theme")
        self._speed_button.setToolTip("Start network research")

        for button in [self._refresh_button, self._trace_button, self._theme_button]:
            button.setFixedSize(42, 42)
            button.setIconSize(QSize(20, 20))

        self._speed_button.setFixedSize(72, 72)
        self._speed_button.setIconSize(QSize(30, 30))
        self._speed_button.setIcon(self._resolve_icon("media-playback-start", "play.svg"))

    def _apply_theme(self, is_dark: bool) -> None:
        self._is_dark_theme = is_dark
        palette = self.palette()

        if is_dark:
            palette.setColor(QPalette.ColorRole.Window, QColor("#070A0F"))
            palette.setColor(QPalette.ColorRole.Base, QColor("#0C1118"))
            palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#0A0F16"))
            palette.setColor(QPalette.ColorRole.Text, QColor("#EAF2FF"))
            self.setStyleSheet(
                """
                QMainWindow { background: #070A0F; }
                QScrollArea#appScroll { background: #070A0F; border: none; }
                QScrollArea#appScroll > QWidget > QWidget#appRoot { background: #070A0F; }
                QLabel { color: #C7D5E7; font-size: 12px; }
                QFrame#metricCard {
                    border: 1px solid #263244;
                    border-radius: 16px;
                    padding: 10px;
                }
                QPushButton {
                    background: #1345A2;
                    color: #FFFFFF;
                    border: none;
                    border-radius: 10px;
                    padding: 8px 14px;
                    font-weight: 600;
                }
                QPushButton:hover { background: #1B56C8; }
                QPushButton:checked { background: #0E7490; }
                QPushButton:disabled { background: #2C3A4D; color: #8DA1BA; }
                QPushButton#startResearchButton {
                    min-width: 72px;
                    min-height: 72px;
                    max-width: 72px;
                    max-height: 72px;
                    border-radius: 36px;
                    background: qlineargradient(
                        x1: 0, y1: 0, x2: 1, y2: 0,
                        stop: 0 #0EA5E9,
                        stop: 1 #2563EB
                    );
                }
                QLabel#stageLabel {
                    color: #8FB3DE;
                    font-size: 13px;
                    font-weight: 600;
                }
                QTableWidget {
                    background: #0C1118;
                    border: 1px solid #263244;
                    border-radius: 14px;
                    gridline-color: #223044;
                    selection-background-color: #1B56C8;
                    selection-color: #F8FBFF;
                    color: #EAF2FF;
                }
                QHeaderView::section {
                    background: #0A0F16;
                    color: #AFC6E4;
                    border: none;
                    border-bottom: 1px solid #263244;
                    padding: 8px;
                    font-weight: 700;
                }
                QProgressBar {
                    background: #0C1118;
                    border: 1px solid #263244;
                    border-radius: 8px;
                    text-align: center;
                    color: #D6E6FA;
                    min-height: 18px;
                }
                QProgressBar::chunk {
                    background: qlineargradient(
                        x1: 0, y1: 0, x2: 1, y2: 0,
                        stop: 0 #0EA5E9,
                        stop: 1 #2563EB
                    );
                    border-radius: 7px;
                }
                QLabel#statsHeader { color: #8FB3DE; font-weight: 700; }
                QLabel#statsMetric { color: #E2ECFA; font-weight: 600; }
                QLabel#statsValue { color: #BBD0EA; }
                QLabel#comparisonLabel { color: #FCD34D; font-size: 13px; font-weight: 600; }
                """
            )
        else:
            palette.setColor(QPalette.ColorRole.Window, QColor("#F5F7FB"))
            palette.setColor(QPalette.ColorRole.Base, QColor("#FFFFFF"))
            palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#EEF2F7"))
            palette.setColor(QPalette.ColorRole.Text, QColor("#101828"))
            self.setStyleSheet(
                """
                QMainWindow {
                    background: #F5F7FB;
                }
                QScrollArea#appScroll {
                    background: #F5F7FB;
                    border: none;
                }
                QScrollArea#appScroll > QWidget > QWidget#appRoot {
                    background: #F5F7FB;
                }
                QLabel {
                    color: #334155;
                    font-size: 12px;
                }
                QFrame#metricCard {
                    border: 1px solid #E2E8F0;
                    border-radius: 16px;
                    padding: 10px;
                }
                QPushButton {
                    background: #0F6CBD;
                    color: #FFFFFF;
                    border: none;
                    border-radius: 10px;
                    padding: 8px 14px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background: #115EA3;
                }
                QPushButton:checked {
                    background: #0B5CAD;
                }
                QPushButton:disabled {
                    background: #94A3B8;
                    color: #E2E8F0;
                }
                QPushButton#startResearchButton {
                    min-width: 72px;
                    min-height: 72px;
                    max-width: 72px;
                    max-height: 72px;
                    border-radius: 36px;
                    background: qlineargradient(
                        x1: 0, y1: 0, x2: 1, y2: 0,
                        stop: 0 #3B82F6,
                        stop: 1 #06B6D4
                    );
                }
                QLabel#stageLabel {
                    color: #075985;
                    font-size: 13px;
                    font-weight: 600;
                }
                QTableWidget {
                    background: #FFFFFF;
                    border: 1px solid #D7DEEA;
                    border-radius: 14px;
                    gridline-color: #E2E8F0;
                    selection-background-color: #DCEBFF;
                    selection-color: #0F172A;
                    font-size: 12px;
                }
                QHeaderView::section {
                    background: #EFF4FA;
                    color: #334155;
                    border: none;
                    border-bottom: 1px solid #D7DEEA;
                    padding: 8px;
                    font-weight: 700;
                }
                QProgressBar {
                    background: #EAF0F7;
                    border: 1px solid #D7DEEA;
                    border-radius: 8px;
                    text-align: center;
                    color: #334155;
                    min-height: 18px;
                }
                QProgressBar::chunk {
                    background: qlineargradient(
                        x1: 0, y1: 0, x2: 1, y2: 0,
                        stop: 0 #3B82F6,
                        stop: 1 #06B6D4
                    );
                    border-radius: 7px;
                }
                QLabel#statsHeader { color: #1D4ED8; font-weight: 700; }
                QLabel#statsMetric { color: #1E293B; font-weight: 600; }
                QLabel#statsValue { color: #334155; }
                QLabel#comparisonLabel { color: #075985; font-size: 13px; font-weight: 600; }
                """
            )

        self.setPalette(palette)

        card_names = [
            "_hostname_card",
            "_local_ip_card",
            "_public_ip_card",
            "_download_card",
            "_upload_card",
            "_ping_card",
            "_quality_card",
        ]
        for card_name in card_names:
            card = getattr(self, card_name, None)
            if card is not None:
                card.set_dark_mode(is_dark)

        self._gauge.set_theme(is_dark)

    def _on_theme_toggled(self, checked: bool) -> None:
        self._update_theme_button_icon(checked)
        self._theme_icon_animation.stop()
        self._theme_icon_animation.start()
        self._apply_theme(is_dark=checked)
        # Force immediate refresh to avoid delayed style propagation on some Qt repaint cycles.
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()

    def _update_theme_button_icon(self, is_dark_enabled: bool) -> None:
        icon_name = "weather-clear-night" if is_dark_enabled else "weather-clear"
        file_name = "moon.svg" if is_dark_enabled else "sun.svg"
        icon = self._resolve_icon(icon_name, file_name)
        self._theme_button.setIcon(icon)
        self._theme_button.setToolTip("Switch to light theme" if is_dark_enabled else "Switch to dark theme")

    def _resolve_icon(self, theme_name: str, asset_name: str) -> QIcon:
        icon = QIcon.fromTheme(theme_name)
        if not icon.isNull():
            return icon

        icon_path = Path(__file__).resolve().parent / "assets" / asset_name
        if icon_path.exists():
            return QIcon(str(icon_path))

        return QIcon()

    def _toggle_trace_window(self) -> None:
        if self._trace_window.isVisible():
            self._trace_window.hide()
            self._trace_button.setToolTip("Open trace window")
        else:
            self._trace_window.show()
            self._trace_button.setToolTip("Hide trace window")

    def _append_trace_line(self, text: str) -> None:
        self._trace_window.append_line(text)

    def _advance_progress_while_running(self) -> None:
        if not (self._speed_worker and self._speed_worker.isRunning()):
            self._progress_timer.stop()
            return

        current = self._progress_bar.value()
        if current < 88:
            next_value = current + 1
            self._progress_bar.setValue(next_value)

    def _on_scan_stage_changed(self, text: str) -> None:
        self._stage_label.setText(text)

        lowered = text.lower()
        if "download" in lowered:
            self._current_scan_stage = "download"
        elif "upload" in lowered:
            self._current_scan_stage = "upload"
        elif "server" in lowered:
            self._current_scan_stage = "server"
        elif "final" in lowered:
            self._current_scan_stage = "finalizing"
        else:
            self._current_scan_stage = "initializing"

    def _animate_live_gauge(self) -> None:
        if not (self._speed_worker and self._speed_worker.isRunning()):
            self._scan_gauge_timer.stop()
            return

        self._scan_tick += 1
        stage = self._current_scan_stage

        if stage == "download":
            value = min(450.0, 20.0 + (self._scan_tick % 50) * 8.5)
            if value > 430:
                self._scan_tick = 0
        elif stage == "upload":
            value = 25.0 + (self._scan_tick % 20) * 2.2
        elif stage == "server":
            value = 8.0 + (self._scan_tick % 10) * 1.1
        elif stage == "finalizing":
            value = 12.0 + (self._scan_tick % 8) * 0.8
        else:
            value = 5.0 + (self._scan_tick % 8) * 0.9

        self._gauge.set_value(value)

    def refresh_network_data(self) -> None:
        try:
            state = self._view_model.load_network_state()
            self._hostname_card.set_value(state.hostname, animate=False)
            self._local_ip_card.set_value(state.local_ip, animate=False)
            self._public_ip_card.set_value(state.public_ip, animate=False)
            self._table.set_interfaces(state.interfaces)
            self._status_label.setText("Network data refreshed")
        except Exception as exc:  # noqa: BLE001
            self._status_label.setText(f"Refresh failed: {exc}")

    def start_speed_test(self) -> None:
        if self._speed_worker and self._speed_worker.isRunning():
            return

        self._speed_button.setEnabled(False)
        self._refresh_button.setEnabled(False)
        self._theme_button.setEnabled(False)
        self._status_label.setText("Running full network research workflow...")
        self._stage_label.setText("Preparing diagnostics")
        self._append_trace_line("Running new speed test")
        self._download_card.set_value("Calculating...", animate=False)
        self._upload_card.set_value("Calculating...", animate=False)
        self._ping_card.set_value("Calculating...", animate=False)
        self._quality_card.set_value("Calculating...", animate=False)
        self._progress_bar.setValue(0)
        self._gauge.set_range(0, 500, "Mbps", "Download speed")
        self._gauge.set_value(0)
        self._current_scan_stage = "initializing"
        self._scan_tick = 0
        self._refresh_timer.stop()
        self._progress_timer.start()
        self._scan_gauge_timer.start()

        self._speed_worker = SpeedTestWorker(self._view_model)
        self._speed_worker.progress_stage.connect(self._progress_bar.setValue)
        self._speed_worker.stage_label.connect(self._on_scan_stage_changed)
        self._speed_worker.trace_line.connect(self._append_trace_line)
        self._speed_worker.finished_ok.connect(self._on_speed_test_finished)
        self._speed_worker.failed.connect(self._on_speed_test_failed)
        self._speed_worker.finished.connect(lambda: self._speed_button.setEnabled(True))
        self._speed_worker.finished.connect(lambda: self._refresh_button.setEnabled(True))
        self._speed_worker.finished.connect(lambda: self._theme_button.setEnabled(True))
        self._speed_worker.finished.connect(self._refresh_timer.start)
        self._speed_worker.finished.connect(self._progress_timer.stop)
        self._speed_worker.finished.connect(self._scan_gauge_timer.stop)
        self._speed_worker.start()

    def _update_stats(self, metric: str, values: deque[float], current: float) -> None:
        values.append(current)
        avg = sum(values) / len(values)

        self._stats_values[(metric, "current")].setText(f"{current:.2f}")
        self._stats_values[(metric, "avg")].setText(f"{avg:.2f}")
        self._stats_values[(metric, "min")].setText(f"{min(values):.2f}")
        self._stats_values[(metric, "max")].setText(f"{max(values):.2f}")

    def _update_comparison(self, score: int) -> None:
        if self._previous_score is None:
            self._comparison_label.setText("Comparison with previous test: this is the first result")
            self._previous_score = score
            return

        delta = score - self._previous_score
        if delta > 0:
            text = f"Comparison with previous test: improved by +{delta} score"
        elif delta < 0:
            text = f"Comparison with previous test: degraded by {delta} score"
        else:
            text = "Comparison with previous test: no meaningful change"

        self._comparison_label.setText(text)
        self._previous_score = score

    def _on_speed_test_finished(
        self,
        download_mbps: float,
        upload_mbps: float,
        ping_ms: float,
        server_name: str,
    ) -> None:
        self._progress_bar.setValue(100)
        self._gauge.set_range(0, max(1.0, download_mbps * 1.25), "Mbps", "Download result")
        self._gauge.set_value(download_mbps)
        self._stage_label.setText("Download/Upload/Ping measurement completed")
        self._download_card.set_value(f"{download_mbps:.2f} Mbps", animate=False)
        self._upload_card.set_value(f"{upload_mbps:.2f} Mbps", animate=False)
        self._ping_card.set_value(f"{ping_ms:.2f} ms", animate=False)

        self._update_stats("Download (Mbps)", self._download_history, download_mbps)
        self._update_stats("Upload (Mbps)", self._upload_history, upload_mbps)
        self._update_stats("Ping (ms)", self._ping_history, ping_ms)

        quality_score, quality_label = self._view_model.evaluate_quality_score(
            download_mbps=download_mbps,
            upload_mbps=upload_mbps,
            ping_ms=ping_ms,
        )
        self._quality_card.set_value(f"{quality_score}/10 {quality_label}", animate=False)
        self._update_comparison(quality_score)

        self._append_trace_line(
            f"Completed: down={download_mbps:.2f} Mbps, up={upload_mbps:.2f} Mbps, ping={ping_ms:.2f} ms"
        )
        self._status_label.setText(f"Speed test complete via {server_name}")

    def _on_speed_test_failed(self, error_text: str) -> None:
        self._progress_bar.setValue(0)
        self._gauge.set_range(0, 100, "%", "Research failed")
        self._gauge.set_value(0)
        self._stage_label.setText("Research failed. Check trace details.")
        self._status_label.setText("Speed test failed")
        self._download_card.set_value("-", animate=False)
        self._upload_card.set_value("-", animate=False)
        self._ping_card.set_value("-", animate=False)
        self._quality_card.set_value("-", animate=False)
        self._append_trace_line(f"Speed test failed: {error_text}")
        QMessageBox.critical(self, "Speed Test Error", error_text)
