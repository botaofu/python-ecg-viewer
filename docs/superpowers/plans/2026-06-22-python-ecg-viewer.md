# Python ECG Viewer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a small PyQt6 desktop application that loads ECG CSV files with pandas and displays selectable channels in an interactive Matplotlib plot.

**Architecture:** A data module converts CSV input into a validated `ECGData` contract. A focused Matplotlib canvas renders that contract, while a PyQt6 main window owns user interaction and coordinates loading without embedding parsing logic. Errors cross the data/UI boundary as domain exceptions and become concise dialogs.

**Tech Stack:** Python 3.10+, PyQt6, pandas, NumPy, Matplotlib QtAgg, pytest, pytest-qt

---

## File Map

- `pyproject.toml`: runtime/dev dependencies, pytest settings, and console entry point.
- `ecg_viewer/__init__.py`: package version and public package metadata.
- `ecg_viewer/__main__.py`: `QApplication` startup and process exit.
- `ecg_viewer/data.py`: `ECGData`, `ECGDataLoader`, time-column inference, and validation errors.
- `ecg_viewer/plot.py`: embedded Matplotlib canvas and navigation toolbar integration.
- `ecg_viewer/window.py`: widgets, dialogs, load orchestration, channel selection, and summaries.
- `tests/conftest.py`: force the Qt offscreen platform for automated tests.
- `tests/test_data.py`: data-loading and validation tests.
- `tests/test_plot.py`: canvas plotting and reset behavior tests.
- `tests/test_window.py`: Qt state and load-flow tests.
- `data/sample_ecg.csv`: a small two-channel example recording.
- `README.md`: beginner-friendly setup, usage, CSV format, and troubleshooting.

### Task 1: Create an installable package skeleton

**Files:**
- Create: `pyproject.toml`
- Create: `README.md`
- Create: `ecg_viewer/__init__.py`
- Create: `ecg_viewer/__main__.py`
- Create: `tests/conftest.py`
- Create: `tests/test_package.py`

- [ ] **Step 1: Write the failing package test**

```python
from ecg_viewer import __version__


def test_package_exposes_version():
    assert __version__ == "0.1.0"
```

- [ ] **Step 2: Run the package test and verify failure**

Run: `python -m pytest tests/test_package.py -v`

Expected: FAIL because `ecg_viewer` does not exist yet.

- [ ] **Step 3: Add package metadata and entry point**

Create `pyproject.toml`:

```toml
[build-system]
requires = ["setuptools>=69"]
build-backend = "setuptools.build_meta"

[project]
name = "python-ecg-viewer"
version = "0.1.0"
description = "A lightweight CSV ECG viewer built with pandas, Matplotlib, and PyQt6"
readme = "README.md"
requires-python = ">=3.10"
dependencies = [
  "matplotlib>=3.8",
  "numpy>=1.26",
  "pandas>=2.1",
  "PyQt6>=6.6",
]

[project.optional-dependencies]
dev = [
  "pytest>=8.0",
  "pytest-qt>=4.4",
]

[project.scripts]
ecg-viewer = "ecg_viewer.__main__:main"

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-ra"
```

Create `ecg_viewer/__init__.py`:

```python
"""Lightweight desktop ECG viewer."""

__version__ = "0.1.0"
```

Create `ecg_viewer/__main__.py`:

```python
import sys

from PyQt6.QtWidgets import QApplication

from ecg_viewer.window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
```

Create `tests/conftest.py`:

```python
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
```

Create the initial `README.md` so package metadata can be installed before the full usage guide is written:

```markdown
# Python ECG Viewer

A lightweight desktop viewer for ECG data stored in CSV files.
```

- [ ] **Step 4: Install the project with development dependencies**

Run: `python -m pip install -e '.[dev]'`

Expected: package and dependencies install successfully.

- [ ] **Step 5: Run the package test**

Run: `python -m pytest tests/test_package.py -v`

Expected: PASS.

- [ ] **Step 6: Commit the package skeleton**

```bash
git add pyproject.toml README.md ecg_viewer/__init__.py ecg_viewer/__main__.py tests/conftest.py tests/test_package.py
git commit -m "chore: scaffold ECG viewer package"
```

### Task 2: Implement validated CSV loading

**Files:**
- Create: `ecg_viewer/data.py`
- Create: `tests/test_data.py`

- [ ] **Step 1: Write failing loader tests**

```python
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from ecg_viewer.data import ECGDataError, ECGDataLoader


def write_csv(tmp_path: Path, values: dict) -> Path:
    path = tmp_path / "recording.csv"
    pd.DataFrame(values).to_csv(path, index=False)
    return path


def test_loads_named_time_column_and_multiple_channels(tmp_path):
    path = write_csv(
        tmp_path,
        {"time": [0.0, 0.5, 1.0], "Lead I": [0.1, 0.2, 0.3], "Lead II": [0.4, 0.5, 0.6]},
    )

    data = ECGDataLoader().load(path)

    np.testing.assert_allclose(data.time, [0.0, 0.5, 1.0])
    assert list(data.channels) == ["Lead I", "Lead II"]
    assert data.time_source == "time"
    assert data.sample_rate == pytest.approx(2.0)


def test_generates_time_when_sample_rate_is_supplied(tmp_path):
    path = write_csv(tmp_path, {"Lead II": [0.2, 0.4, 0.6]})

    data = ECGDataLoader().load(path, sample_rate=250.0)

    np.testing.assert_allclose(data.time, [0.0, 0.004, 0.008])
    assert data.time_source == "generated from 250 Hz"


@pytest.mark.parametrize("sample_rate", [0, -1, float("inf"), float("nan")])
def test_rejects_invalid_sample_rate(tmp_path, sample_rate):
    path = write_csv(tmp_path, {"Lead II": [0.2, 0.4]})

    with pytest.raises(ECGDataError, match="Sample rate"):
        ECGDataLoader().load(path, sample_rate=sample_rate)


def test_requires_sample_rate_when_time_is_missing(tmp_path):
    path = write_csv(tmp_path, {"Lead II": [0.2, 0.4]})

    with pytest.raises(ECGDataError, match="SAMPLE_RATE_REQUIRED"):
        ECGDataLoader().load(path)


def test_invalid_time_candidate_falls_back_to_sample_rate(tmp_path):
    path = write_csv(tmp_path, {"time": [0.0, 0.0, 1.0], "Lead II": [0.2, 0.4, 0.3]})

    data = ECGDataLoader().load(path, sample_rate=100.0)

    assert list(data.channels) == ["time", "Lead II"]
    np.testing.assert_allclose(data.time, [0.0, 0.01, 0.02])


def test_ignores_text_metadata_but_preserves_channel_nan(tmp_path):
    path = write_csv(
        tmp_path,
        {"seconds": [0.0, 0.1, 0.2], "patient": ["A", "A", "A"], "ECG": [1.0, None, 3.0]},
    )

    data = ECGDataLoader().load(path)

    assert list(data.channels) == ["ECG"]
    assert np.isnan(data.channels["ECG"][1])


def test_rejects_file_without_numeric_channel(tmp_path):
    path = write_csv(tmp_path, {"time": [0.0, 1.0], "note": ["a", "b"]})

    with pytest.raises(ECGDataError, match="numeric ECG channel"):
        ECGDataLoader().load(path)
```

- [ ] **Step 2: Run loader tests and verify failure**

Run: `python -m pytest tests/test_data.py -v`

Expected: FAIL because `ecg_viewer.data` does not exist.

- [ ] **Step 3: Implement the loader and data contract**

Create `ecg_viewer/data.py`:

```python
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd


TIME_COLUMN_NAMES = ("time", "timestamp", "seconds", "second", "t")


class ECGDataError(ValueError):
    """Raised when a CSV cannot be converted into displayable ECG data."""


@dataclass(frozen=True)
class ECGData:
    time: np.ndarray
    channels: dict[str, np.ndarray]
    sample_rate: float | None
    source_path: Path
    time_source: str

    @property
    def sample_count(self) -> int:
        return len(self.time)

    @property
    def duration(self) -> float:
        if self.sample_count < 2:
            return 0.0
        return float(self.time[-1] - self.time[0])


class ECGDataLoader:
    def load(self, path: str | Path, sample_rate: float | None = None) -> ECGData:
        source_path = Path(path)
        try:
            frame = pd.read_csv(source_path)
        except (OSError, pd.errors.ParserError, UnicodeError) as exc:
            raise ECGDataError(f"Could not read CSV: {exc}") from exc

        if frame.empty or len(frame.columns) == 0:
            raise ECGDataError("The CSV file is empty.")

        time_name = self._find_time_column(frame)
        if time_name is None:
            if sample_rate is None:
                raise ECGDataError("SAMPLE_RATE_REQUIRED: no valid time column was found.")
            self._validate_sample_rate(sample_rate)
            time = np.arange(len(frame), dtype=float) / float(sample_rate)
            inferred_rate = float(sample_rate)
            time_source = f"generated from {float(sample_rate):g} Hz"
        else:
            time = frame[time_name].to_numpy(dtype=float)
            inferred_rate = self._infer_sample_rate(time)
            time_source = time_name

        numeric_names = list(frame.select_dtypes(include="number").columns)
        if time_name in numeric_names:
            numeric_names.remove(time_name)
        channels = {name: frame[name].to_numpy(dtype=float) for name in numeric_names}
        if not channels:
            raise ECGDataError("The CSV must contain at least one numeric ECG channel.")

        return ECGData(
            time=time,
            channels=channels,
            sample_rate=inferred_rate,
            source_path=source_path,
            time_source=time_source,
        )

    @staticmethod
    def _find_time_column(frame: pd.DataFrame) -> str | None:
        names = {str(name).strip().lower(): name for name in frame.columns}
        for candidate in TIME_COLUMN_NAMES:
            actual = names.get(candidate)
            if actual is None or not pd.api.types.is_numeric_dtype(frame[actual]):
                continue
            values = frame[actual].to_numpy(dtype=float)
            if np.isfinite(values).all() and len(values) > 0 and np.all(np.diff(values) > 0):
                return actual
        return None

    @staticmethod
    def _validate_sample_rate(sample_rate: float) -> None:
        if not np.isfinite(sample_rate) or sample_rate <= 0:
            raise ECGDataError("Sample rate must be a finite number greater than zero.")

    @staticmethod
    def _infer_sample_rate(time: np.ndarray) -> float | None:
        if len(time) < 2:
            return None
        step = float(np.median(np.diff(time)))
        return 1.0 / step if step > 0 else None
```

- [ ] **Step 4: Run loader tests**

Run: `python -m pytest tests/test_data.py -v`

Expected: all loader tests PASS.

- [ ] **Step 5: Commit the loader**

```bash
git add ecg_viewer/data.py tests/test_data.py
git commit -m "feat: load and validate ECG CSV data"
```

### Task 3: Embed an interactive Matplotlib ECG canvas

**Files:**
- Create: `ecg_viewer/plot.py`
- Create: `tests/test_plot.py`

- [ ] **Step 1: Write failing canvas tests**

```python
import numpy as np

from ecg_viewer.plot import ECGPlotCanvas


def test_plot_signal_sets_data_labels_and_full_limits(qtbot):
    canvas = ECGPlotCanvas()
    qtbot.addWidget(canvas)

    canvas.plot_signal(np.array([0.0, 1.0, 2.0]), np.array([0.1, 0.5, -0.2]), "Lead II")

    assert len(canvas.axes.lines) == 1
    assert canvas.axes.get_title() == "Lead II"
    assert canvas.axes.get_xlabel() == "Time (s)"
    assert canvas.axes.get_ylabel() == "Amplitude"
    assert canvas.full_xlim == (0.0, 2.0)


def test_reset_view_restores_full_limits(qtbot):
    canvas = ECGPlotCanvas()
    qtbot.addWidget(canvas)
    canvas.plot_signal(np.array([0.0, 1.0, 2.0]), np.array([0.1, 0.5, -0.2]), "ECG")
    canvas.axes.set_xlim(0.5, 1.0)

    canvas.reset_view()

    assert canvas.axes.get_xlim() == (0.0, 2.0)
```

- [ ] **Step 2: Run canvas tests and verify failure**

Run: `python -m pytest tests/test_plot.py -v`

Expected: FAIL because `ecg_viewer.plot` does not exist.

- [ ] **Step 3: Implement the canvas**

Create `ecg_viewer/plot.py`:

```python
import numpy as np
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.figure import Figure


class ECGPlotCanvas(FigureCanvasQTAgg):
    def __init__(self, parent=None):
        self.figure = Figure(figsize=(10, 5), tight_layout=True)
        self.axes = self.figure.add_subplot(111)
        super().__init__(self.figure)
        self.setParent(parent)
        self.full_xlim: tuple[float, float] | None = None
        self._style_empty_axes()

    def _style_empty_axes(self) -> None:
        self.axes.set_xlabel("Time (s)")
        self.axes.set_ylabel("Amplitude")
        self.axes.grid(True, color="#e5b8b8", linewidth=0.6, alpha=0.6)

    def plot_signal(self, time: np.ndarray, values: np.ndarray, channel_name: str) -> None:
        self.axes.clear()
        self.axes.plot(time, values, color="#c62828", linewidth=1.0)
        self.axes.set_title(channel_name)
        self._style_empty_axes()
        if len(time):
            left = float(time[0])
            right = float(time[-1])
            if left == right:
                right = left + 1.0
            self.full_xlim = (left, right)
            self.axes.set_xlim(self.full_xlim)
        else:
            self.full_xlim = None
        self.draw_idle()

    def clear(self) -> None:
        self.axes.clear()
        self.full_xlim = None
        self._style_empty_axes()
        self.draw_idle()

    def reset_view(self) -> None:
        if self.full_xlim is not None:
            self.axes.set_xlim(self.full_xlim)
            self.axes.relim()
            self.axes.autoscale_view(scalex=False, scaley=True)
            self.draw_idle()


class ECGNavigationToolbar(NavigationToolbar2QT):
    toolitems = tuple(item for item in NavigationToolbar2QT.toolitems if item[0] in {"Home", "Pan", "Zoom", "Save"})
```

- [ ] **Step 4: Run canvas tests**

Run: `python -m pytest tests/test_plot.py -v`

Expected: both tests PASS.

- [ ] **Step 5: Commit the canvas**

```bash
git add ecg_viewer/plot.py tests/test_plot.py
git commit -m "feat: add interactive ECG plot canvas"
```

### Task 4: Build the main window and channel interaction

**Files:**
- Create: `ecg_viewer/window.py`
- Create: `tests/test_window.py`

- [ ] **Step 1: Write failing main-window state tests**

```python
from pathlib import Path

import numpy as np

from ecg_viewer.data import ECGData
from ecg_viewer.window import MainWindow


def make_data() -> ECGData:
    return ECGData(
        time=np.array([0.0, 0.5, 1.0]),
        channels={"Lead I": np.array([0.1, np.nan, 0.3]), "Lead II": np.array([0.4, 0.5, 0.6])},
        sample_rate=2.0,
        source_path=Path("recording.csv"),
        time_source="time",
    )


def test_window_starts_without_channel_actions(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)

    assert window.channel_combo.count() == 0
    assert not window.channel_combo.isEnabled()
    assert not window.reset_button.isEnabled()


def test_applying_data_populates_sidebar_and_plots_first_channel(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)

    window.apply_data(make_data())

    assert window.channel_combo.count() == 2
    assert window.channel_combo.currentText() == "Lead I"
    assert window.file_label.text() == "recording.csv"
    assert window.sample_count_label.text() == "3"
    assert window.missing_label.text() == "1"
    assert window.plot_canvas.axes.get_title() == "Lead I"


def test_switching_channel_refreshes_plot_and_summary(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    window.apply_data(make_data())

    window.channel_combo.setCurrentText("Lead II")

    assert window.plot_canvas.axes.get_title() == "Lead II"
    assert window.missing_label.text() == "0"
```

- [ ] **Step 2: Run window tests and verify failure**

Run: `python -m pytest tests/test_window.py -v`

Expected: FAIL because `ecg_viewer.window` does not exist.

- [ ] **Step 3: Implement the layout and data application**

Create `ecg_viewer/window.py` with these widgets and methods:

```python
from pathlib import Path

import numpy as np
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFormLayout,
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
        self.open_button.clicked.connect(self.open_csv)
        self.reset_button.clicked.connect(self.plot_canvas.reset_view)
        self.channel_combo.currentTextChanged.connect(self.update_channel)
        self.statusBar().showMessage("Open a CSV file to begin.")

    def _build_layout(self) -> None:
        top = QHBoxLayout()
        top.addWidget(self.open_button)
        top.addWidget(self.reset_button)
        top.addWidget(self.navigation_toolbar)
        top.addStretch()

        form = QFormLayout()
        form.addRow("File", self.file_label)
        form.addRow("Channel", self.channel_combo)
        form.addRow("Time source", self.time_source_label)
        form.addRow("Sample rate", self.sample_rate_label)
        form.addRow("Duration", self.duration_label)
        form.addRow("Samples", self.sample_count_label)
        form.addRow("Minimum", self.minimum_label)
        form.addRow("Maximum", self.maximum_label)
        form.addRow("Missing", self.missing_label)

        sidebar = QWidget()
        sidebar.setLayout(form)
        sidebar.setMaximumWidth(260)

        content = QHBoxLayout()
        content.addWidget(sidebar)
        content.addWidget(self.plot_canvas, stretch=1)

        root = QVBoxLayout()
        root.addLayout(top)
        root.addLayout(content, stretch=1)
        central = QWidget()
        central.setLayout(root)
        self.setCentralWidget(central)

    def apply_data(self, data: ECGData) -> None:
        self.data = data
        self.file_label.setText(data.source_path.name)
        self.time_source_label.setText(data.time_source)
        self.sample_rate_label.setText("—" if data.sample_rate is None else f"{data.sample_rate:g} Hz")
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
        self.minimum_label.setText("—" if not len(finite) else f"{float(finite.min()):.6g}")
        self.maximum_label.setText("—" if not len(finite) else f"{float(finite.max()):.6g}")
        missing = int(np.isnan(values).sum())
        self.missing_label.setText(str(missing))
        self.plot_canvas.plot_signal(self.data.time, values, channel_name)
        self.statusBar().showMessage(
            f"Loaded {self.data.sample_count:,} samples · {missing} missing value(s) in {channel_name}"
        )

    def open_csv(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Open ECG CSV", "", "CSV files (*.csv);;All files (*)")
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
                self, "Sample rate required", "Sample rate (Hz)", 250.0, 0.001, 1_000_000.0, 3
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
```

- [ ] **Step 4: Run window state tests**

Run: `python -m pytest tests/test_window.py -v`

Expected: all three tests PASS.

- [ ] **Step 5: Commit the main window**

```bash
git add ecg_viewer/window.py tests/test_window.py
git commit -m "feat: add ECG viewer main window"
```

### Task 5: Verify file-dialog fallback and state preservation

**Files:**
- Modify: `tests/test_window.py`
- Modify: `ecg_viewer/window.py`

- [ ] **Step 1: Add failing orchestration tests**

Append to `tests/test_window.py`:

```python
from ecg_viewer.data import ECGDataError
from PyQt6.QtWidgets import QInputDialog


class LoaderStub:
    def __init__(self, result=None, error=None):
        self.result = result
        self.error = error
        self.calls = []

    def load(self, path, sample_rate=None):
        self.calls.append((Path(path), sample_rate))
        if self.error is not None:
            raise self.error
        return self.result


def test_failed_load_keeps_current_data(qtbot, monkeypatch):
    loader = LoaderStub(error=ECGDataError("broken CSV"))
    window = MainWindow(loader=loader)
    qtbot.addWidget(window)
    current = make_data()
    window.apply_data(current)
    messages = []
    monkeypatch.setattr(window, "_show_error", messages.append)

    assert not window.load_path(Path("broken.csv"))

    assert window.data is current
    assert messages == ["broken CSV"]


def test_missing_time_requests_sample_rate_and_retries(qtbot, monkeypatch):
    data = make_data()

    class RetryLoader:
        def __init__(self):
            self.calls = []

        def load(self, path, sample_rate=None):
            self.calls.append(sample_rate)
            if sample_rate is None:
                raise ECGDataError("SAMPLE_RATE_REQUIRED: no valid time column was found.")
            return data

    loader = RetryLoader()
    window = MainWindow(loader=loader)
    qtbot.addWidget(window)
    monkeypatch.setattr(QInputDialog, "getDouble", lambda *args, **kwargs: (360.0, True))

    assert window.load_path(Path("recording.csv"))
    assert loader.calls == [None, 360.0]
    assert window.data is data
```

- [ ] **Step 2: Run orchestration tests**

Run: `python -m pytest tests/test_window.py -v`

Expected: tests PASS if Task 4's load flow is complete; otherwise FAIL at the missing behavior.

- [ ] **Step 3: If Task 4's method is incomplete, replace it with the exact load flow**

Use this complete method body:

```python
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
```

- [ ] **Step 4: Run the complete window test module**

Run: `python -m pytest tests/test_window.py -v`

Expected: all window tests PASS.

- [ ] **Step 5: Commit the completed load flow**

```bash
git add ecg_viewer/window.py tests/test_window.py
git commit -m "test: cover ECG file loading flow"
```

### Task 6: Add sample ECG data and beginner documentation

**Files:**
- Create: `data/sample_ecg.csv`
- Modify: `README.md`

- [ ] **Step 1: Add deterministic sample data**

Create `data/sample_ecg.csv` with headers `time,Lead I,Lead II` and at least 200 rows sampled at 100 Hz. Generate values deterministically with:

```python
import numpy as np
import pandas as pd

time = np.arange(0.0, 4.0, 0.01)
phase = np.mod(time, 0.8)
qrs = 1.2 * np.exp(-((phase - 0.10) / 0.018) ** 2)
t_wave = 0.25 * np.exp(-((phase - 0.32) / 0.08) ** 2)
baseline = 0.04 * np.sin(2 * np.pi * 0.33 * time)
frame = pd.DataFrame(
    {
        "time": time,
        "Lead I": baseline + 0.75 * qrs + 0.8 * t_wave,
        "Lead II": baseline + qrs + t_wave,
    }
)
frame.to_csv("data/sample_ecg.csv", index=False, float_format="%.6f")
```

- [ ] **Step 2: Write a beginner-friendly README**

The README must contain these exact workflows:

```markdown
# Python ECG Viewer

A lightweight desktop viewer for ECG data stored in CSV files. It uses pandas for loading data, Matplotlib for interactive plotting, and PyQt6 for the desktop interface.

> This project visualizes signals only. It does not provide medical diagnosis.

## Quick start

1. Open Terminal in this project folder.
2. Create an environment: `python3 -m venv .venv`
3. Activate it on macOS/Linux: `source .venv/bin/activate`
4. Install the project: `python -m pip install -e '.[dev]'`
5. Start the viewer: `python -m ecg_viewer`
6. Click **Open CSV** and choose `data/sample_ecg.csv`.

## CSV format

- Include one or more numeric ECG columns.
- A numeric, strictly increasing time column named `time`, `timestamp`, `seconds`, `second`, or `t` is detected automatically.
- If no valid time column exists, the application asks for the sample rate in hertz.
- Text metadata columns are ignored.
- Missing ECG values appear as gaps in the plot.

## Controls

- Choose a channel from the left sidebar.
- Use Pan and Zoom in the Matplotlib toolbar.
- Use Reset View to return to the full recording.
- Use Save in the Matplotlib toolbar to export the current plot as an image.

## Tests

Run `python -m pytest -v`.

## Troubleshooting

- If `python3` is missing, install Python 3.10 or newer from python.org.
- If the Qt window does not appear, confirm that PyQt6 installed inside the active virtual environment.
- If a file is rejected, check that it is a comma-separated CSV with at least one numeric ECG column.
```

- [ ] **Step 3: Verify the bundled sample loads**

Run:

```bash
python -c "from ecg_viewer.data import ECGDataLoader; d=ECGDataLoader().load('data/sample_ecg.csv'); print(d.sample_count, list(d.channels), round(d.duration, 2))"
```

Expected: `400 ['Lead I', 'Lead II'] 3.99`.

- [ ] **Step 4: Commit data and documentation**

```bash
git add data/sample_ecg.csv README.md
git commit -m "docs: add sample ECG and usage guide"
```

### Task 7: Perform final verification

**Files:**
- Modify only files implicated by verification failures.

- [ ] **Step 1: Run all automated tests**

Run: `QT_QPA_PLATFORM=offscreen python -m pytest -v`

Expected: all tests PASS with no collection errors or unhandled warnings from application code.

- [ ] **Step 2: Verify the package entry point imports**

Run: `python -c "from ecg_viewer.__main__ import main; print(callable(main))"`

Expected: `True`.

- [ ] **Step 3: Launch a manual smoke test**

Run: `python -m ecg_viewer`

Verify:

1. The empty window opens with channel actions disabled.
2. `data/sample_ecg.csv` loads without asking for a sample rate.
3. Both channels can be selected.
4. Pan, zoom, reset, and save controls respond.
5. Closing the window exits the process cleanly.

- [ ] **Step 4: Inspect the final diff and status**

Run:

```bash
git status --short
git diff --check
```

Expected: only intended project files are present and `git diff --check` reports no whitespace errors.

- [ ] **Step 5: Commit any verification-only corrections**

```bash
git add ecg_viewer tests data README.md pyproject.toml .gitignore
git commit -m "fix: finalize ECG viewer verification"
```

Skip this commit if verification required no code changes.

### Task 8: Publish to GitHub

**Files:**
- No source changes expected.

- [ ] **Step 1: Resolve the local Git blocker**

The current machine reports an unaccepted Xcode license when invoking `/usr/bin/git`. The user must accept that system license in Terminal before local Git operations can run:

```bash
sudo xcodebuild -license
```

Expected: `/usr/bin/git --version` prints a Git version afterward.

- [ ] **Step 2: Create or select the destination repository**

The connected GitHub account is `botaofu` and currently exposes no repositories. Create a repository named `python-ecg-viewer` after confirming whether it should be public or private.

- [ ] **Step 3: Initialize and connect the local repository if needed**

```bash
git init
git branch -M main
git remote add origin https://github.com/botaofu/python-ecg-viewer.git
```

- [ ] **Step 4: Commit the complete verified project if earlier commits were blocked**

```bash
git add .gitignore README.md pyproject.toml ecg_viewer tests data docs
git commit -m "feat: build Python ECG viewer"
```

- [ ] **Step 5: Push the project**

```bash
git push -u origin main
```

Expected: GitHub shows the source, tests, sample data, README, design, and implementation plan under `botaofu/python-ecg-viewer`.
