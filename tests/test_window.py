from pathlib import Path

import numpy as np
from PyQt6.QtWidgets import QInputDialog

from ecg_viewer.data import ECGData, ECGDataError


def make_data() -> ECGData:
    return ECGData(
        time=np.array([0.0, 0.5, 1.0]),
        channels={
            "Lead I": np.array([0.1, np.nan, 0.3]),
            "Lead II": np.array([0.4, 0.5, 0.6]),
        },
        sample_rate=2.0,
        source_path=Path("recording.csv"),
        time_source="time",
    )


def test_window_starts_without_channel_actions(qtbot):
    from ecg_viewer.window import MainWindow

    window = MainWindow()
    qtbot.addWidget(window)

    assert window.channel_combo.count() == 0
    assert not window.channel_combo.isEnabled()
    assert not window.reset_button.isEnabled()
    assert window.file_label.text() == "No file loaded"


def test_applying_data_populates_sidebar_and_plots_first_channel(qtbot):
    from ecg_viewer.window import MainWindow

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
    from ecg_viewer.window import MainWindow

    window = MainWindow()
    qtbot.addWidget(window)
    window.apply_data(make_data())

    window.channel_combo.setCurrentText("Lead II")

    assert window.plot_canvas.axes.get_title() == "Lead II"
    assert window.missing_label.text() == "0"
    assert window.minimum_label.text() == "0.4"
    assert window.maximum_label.text() == "0.6"


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
    from ecg_viewer.window import MainWindow

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
    from ecg_viewer.window import MainWindow

    data = make_data()

    class RetryLoader:
        def __init__(self):
            self.calls = []

        def load(self, path, sample_rate=None):
            self.calls.append(sample_rate)
            if sample_rate is None:
                raise ECGDataError(
                    "SAMPLE_RATE_REQUIRED: no valid time column was found."
                )
            return data

    loader = RetryLoader()
    window = MainWindow(loader=loader)
    qtbot.addWidget(window)
    monkeypatch.setattr(
        QInputDialog,
        "getDouble",
        lambda *args, **kwargs: (360.0, True),
    )

    assert window.load_path(Path("recording.csv"))
    assert loader.calls == [None, 360.0]
    assert window.data is data


def test_cancelled_sample_rate_keeps_current_data(qtbot, monkeypatch):
    from ecg_viewer.window import MainWindow

    loader = LoaderStub(
        error=ECGDataError(
            "SAMPLE_RATE_REQUIRED: no valid time column was found."
        )
    )
    window = MainWindow(loader=loader)
    qtbot.addWidget(window)
    current = make_data()
    window.apply_data(current)
    monkeypatch.setattr(
        QInputDialog,
        "getDouble",
        lambda *args, **kwargs: (250.0, False),
    )

    assert not window.load_path(Path("recording.csv"))
    assert window.data is current
