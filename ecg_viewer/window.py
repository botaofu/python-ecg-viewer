from pathlib import Path

import numpy as np
from PyQt6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ecg_viewer.data import ECGData, ECGDataError, ECGDataLoader
from ecg_viewer.plot import ECGNavigationToolbar, ECGPlotCanvas


class MainWindow(QMainWindow):
    def __init__(self, loader: ECGDataLoader | None = None):
        super().__init__()
        self.loader = loader or ECGDataLoader()
        self.data: ECGData | None = None
        self.setWindowTitle("ECG Viewer")
        self.resize(1100, 700)

        self.open_button = QPushButton("Open CSV")
        self.open_button.setObjectName("primaryButton")
        self.reset_button = QPushButton("Reset View")
        self.channel_combo = QComboBox()
        self.file_label = QLabel("No file loaded")
        self.time_source_label = QLabel("—")
        self.sample_rate_label = QLabel("—")
        self.duration_label = QLabel("—")
        self.sample_count_label = QLabel("0")
        self.minimum_label = QLabel("—")
        self.maximum_label = QLabel("—")
        self.missing_label = QLabel("0")
        self.plot_canvas = ECGPlotCanvas(self)
        self.navigation_toolbar = ECGNavigationToolbar(self.plot_canvas, self)

        self.channel_combo.setEnabled(False)
        self.reset_button.setEnabled(False)
        self._build_layout()
        self._apply_styles()
        self.open_button.clicked.connect(self.open_csv)
        self.reset_button.clicked.connect(self.plot_canvas.reset_view)
        self.channel_combo.currentTextChanged.connect(self.update_channel)
        self.statusBar().showMessage("Open a CSV file to begin.")

    def _build_layout(self) -> None:
        top = QHBoxLayout()
        top.setContentsMargins(14, 10, 14, 10)
        top.setSpacing(10)
        top.addWidget(self.open_button)
        top.addWidget(self.reset_button)
        top.addWidget(self.navigation_toolbar)
        top.addStretch()

        heading = QLabel("Recording")
        heading.setObjectName("sectionHeading")
        form = QFormLayout()
        form.setContentsMargins(16, 8, 16, 16)
        form.setSpacing(12)
        form.addRow("File", self.file_label)
        form.addRow("Channel", self.channel_combo)
        form.addRow("Time source", self.time_source_label)
        form.addRow("Sample rate", self.sample_rate_label)
        form.addRow("Duration", self.duration_label)
        form.addRow("Samples", self.sample_count_label)
        form.addRow("Minimum", self.minimum_label)
        form.addRow("Maximum", self.maximum_label)
        form.addRow("Missing", self.missing_label)

        sidebar_layout = QVBoxLayout()
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.addWidget(heading)
        sidebar_layout.addLayout(form)
        sidebar_layout.addStretch()
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setLayout(sidebar_layout)
        sidebar.setMaximumWidth(280)

        content = QHBoxLayout()
        content.setContentsMargins(14, 0, 14, 14)
        content.setSpacing(14)
        content.addWidget(sidebar)
        content.addWidget(self.plot_canvas, stretch=1)

        root = QVBoxLayout()
        root.setContentsMargins(0, 0, 0, 0)
        root.addLayout(top)
        root.addLayout(content, stretch=1)
        central = QWidget()
        central.setLayout(root)
        self.setCentralWidget(central)

    def _apply_styles(self) -> None:
        self.setStyleSheet(
            """
            QMainWindow, QWidget { background: #f5f7fa; color: #243142; }
            QPushButton {
                background: #ffffff;
                border: 1px solid #c7d0dc;
                border-radius: 6px;
                padding: 7px 12px;
            }
            QPushButton:hover { border-color: #2f6feb; }
            QPushButton:disabled { color: #9aa5b1; background: #edf0f3; }
            QPushButton#primaryButton {
                color: #ffffff;
                background: #2f6feb;
                border-color: #2f6feb;
                font-weight: 600;
            }
            QComboBox {
                background: #ffffff;
                border: 1px solid #c7d0dc;
                border-radius: 5px;
                padding: 5px 8px;
                min-width: 120px;
            }
            QFrame#sidebar {
                background: #ffffff;
                border: 1px solid #dce2ea;
                border-radius: 8px;
            }
            QLabel#sectionHeading {
                background: #eef3f9;
                border: none;
                padding: 12px 16px;
                font-size: 14px;
                font-weight: 700;
            }
            QStatusBar { background: #ffffff; border-top: 1px solid #dce2ea; }
            """
        )

    def apply_data(self, data: ECGData) -> None:
        self.data = data
        self.file_label.setText(data.source_path.name)
        self.file_label.setToolTip(str(data.source_path))
        self.time_source_label.setText(data.time_source)
        self.sample_rate_label.setText(
            "—" if data.sample_rate is None else f"{data.sample_rate:g} Hz"
        )
        self.duration_label.setText(f"{data.duration:.3f} s")
        self.sample_count_label.setText(str(data.sample_count))
        self.channel_combo.blockSignals(True)
        self.channel_combo.clear()
        self.channel_combo.addItems(list(data.channels))
        self.channel_combo.blockSignals(False)
        self.channel_combo.setEnabled(True)
        self.reset_button.setEnabled(True)
        self.update_channel(self.channel_combo.currentText())

    def update_channel(self, channel_name: str) -> None:
        if self.data is None or channel_name not in self.data.channels:
            return
        values = self.data.channels[channel_name]
        finite = values[np.isfinite(values)]
        self.minimum_label.setText(
            "—" if not len(finite) else f"{float(finite.min()):.6g}"
        )
        self.maximum_label.setText(
            "—" if not len(finite) else f"{float(finite.max()):.6g}"
        )
        missing = int(np.isnan(values).sum())
        self.missing_label.setText(str(missing))
        self.plot_canvas.plot_signal(self.data.time, values, channel_name)
        self.statusBar().showMessage(
            f"Loaded {self.data.sample_count:,} samples · "
            f"{missing} missing value(s) in {channel_name}"
        )

    def open_csv(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Open ECG CSV",
            "",
            "CSV files (*.csv);;All files (*)",
        )
        if not path:
            return
        self.load_path(Path(path))

    def load_path(self, path: Path) -> bool:
        try:
            data = self.loader.load(path)
        except ECGDataError as exc:
            if not str(exc).startswith("SAMPLE_RATE_REQUIRED"):
                self._show_error(str(exc))
                return False
            rate, accepted = QInputDialog.getDouble(
                self,
                "Sample rate required",
                "Sample rate (Hz)",
                250.0,
                0.001,
                1_000_000.0,
                3,
            )
            if not accepted:
                return False
            try:
                data = self.loader.load(path, sample_rate=rate)
            except ECGDataError as retry_exc:
                self._show_error(str(retry_exc))
                return False
        self.apply_data(data)
        return True

    def _show_error(self, message: str) -> None:
        QMessageBox.critical(self, "Could not load ECG data", message)
