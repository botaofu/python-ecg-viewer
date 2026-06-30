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

    def plot_signal(
        self,
        time: np.ndarray,
        values: np.ndarray,
        channel_name: str,
    ) -> None:
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
    toolitems = tuple(
        item
        for item in NavigationToolbar2QT.toolitems
        if item[0] in {"Home", "Pan", "Zoom", "Save"}
    )
