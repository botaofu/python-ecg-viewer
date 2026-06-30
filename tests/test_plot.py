import numpy as np


def test_plot_signal_sets_data_labels_and_full_limits(qtbot):
    from ecg_viewer.plot import ECGPlotCanvas

    canvas = ECGPlotCanvas()
    qtbot.addWidget(canvas)

    canvas.plot_signal(
        np.array([0.0, 1.0, 2.0]),
        np.array([0.1, 0.5, -0.2]),
        "Lead II",
    )

    assert len(canvas.axes.lines) == 1
    assert canvas.axes.get_title() == "Lead II"
    assert canvas.axes.get_xlabel() == "Time (s)"
    assert canvas.axes.get_ylabel() == "Amplitude"
    assert canvas.full_xlim == (0.0, 2.0)


def test_reset_view_restores_full_limits(qtbot):
    from ecg_viewer.plot import ECGPlotCanvas

    canvas = ECGPlotCanvas()
    qtbot.addWidget(canvas)
    canvas.plot_signal(
        np.array([0.0, 1.0, 2.0]),
        np.array([0.1, 0.5, -0.2]),
        "ECG",
    )
    canvas.axes.set_xlim(0.5, 1.0)

    canvas.reset_view()

    assert canvas.axes.get_xlim() == (0.0, 2.0)


def test_clear_removes_signal_and_limits(qtbot):
    from ecg_viewer.plot import ECGPlotCanvas

    canvas = ECGPlotCanvas()
    qtbot.addWidget(canvas)
    canvas.plot_signal(np.array([0.0, 1.0]), np.array([0.1, 0.2]), "ECG")

    canvas.clear()

    assert len(canvas.axes.lines) == 0
    assert canvas.full_xlim is None
