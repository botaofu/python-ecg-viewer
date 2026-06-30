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
        except pd.errors.EmptyDataError as exc:
            raise ECGDataError("The CSV file is empty.") from exc
        except (OSError, pd.errors.ParserError, UnicodeError) as exc:
            raise ECGDataError(f"Could not read CSV: {exc}") from exc

        if frame.empty or len(frame.columns) == 0:
            raise ECGDataError("The CSV file is empty.")

        time_name = self._find_time_column(frame)
        if time_name is None:
            if sample_rate is None:
                raise ECGDataError(
                    "SAMPLE_RATE_REQUIRED: no valid time column was found."
                )
            self._validate_sample_rate(sample_rate)
            time = np.arange(len(frame), dtype=float) / float(sample_rate)
            inferred_rate = float(sample_rate)
            time_source = f"generated from {float(sample_rate):g} Hz"
        else:
            time = frame[time_name].to_numpy(dtype=float)
            inferred_rate = self._infer_sample_rate(time)
            time_source = str(time_name)

        numeric_names = list(frame.select_dtypes(include="number").columns)
        if time_name in numeric_names:
            numeric_names.remove(time_name)
        channels = {
            str(name): frame[name].to_numpy(dtype=float) for name in numeric_names
        }
        if not channels:
            raise ECGDataError(
                "The CSV must contain at least one numeric ECG channel."
            )

        return ECGData(
            time=time,
            channels=channels,
            sample_rate=inferred_rate,
            source_path=source_path,
            time_source=time_source,
        )

    @staticmethod
    def _find_time_column(frame: pd.DataFrame) -> object | None:
        names = {str(name).strip().lower(): name for name in frame.columns}
        for candidate in TIME_COLUMN_NAMES:
            actual = names.get(candidate)
            if actual is None or not pd.api.types.is_numeric_dtype(frame[actual]):
                continue
            values = frame[actual].to_numpy(dtype=float)
            if (
                np.isfinite(values).all()
                and len(values) > 0
                and np.all(np.diff(values) > 0)
            ):
                return actual
        return None

    @staticmethod
    def _validate_sample_rate(sample_rate: float) -> None:
        if not np.isfinite(sample_rate) or sample_rate <= 0:
            raise ECGDataError(
                "Sample rate must be a finite number greater than zero."
            )

    @staticmethod
    def _infer_sample_rate(time: np.ndarray) -> float | None:
        if len(time) < 2:
            return None
        step = float(np.median(np.diff(time)))
        return 1.0 / step if step > 0 else None
