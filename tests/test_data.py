from pathlib import Path

import numpy as np
import pandas as pd
import pytest


def write_csv(tmp_path: Path, values: dict) -> Path:
    path = tmp_path / "recording.csv"
    pd.DataFrame(values).to_csv(path, index=False)
    return path


def test_loads_named_time_column_and_multiple_channels(tmp_path):
    from ecg_viewer.data import ECGDataLoader

    path = write_csv(
        tmp_path,
        {
            "time": [0.0, 0.5, 1.0],
            "Lead I": [0.1, 0.2, 0.3],
            "Lead II": [0.4, 0.5, 0.6],
        },
    )

    data = ECGDataLoader().load(path)

    np.testing.assert_allclose(data.time, [0.0, 0.5, 1.0])
    assert list(data.channels) == ["Lead I", "Lead II"]
    assert data.time_source == "time"
    assert data.sample_rate == pytest.approx(2.0)
    assert data.sample_count == 3
    assert data.duration == pytest.approx(1.0)


def test_time_column_matching_is_case_insensitive(tmp_path):
    from ecg_viewer.data import ECGDataLoader

    path = write_csv(tmp_path, {"Seconds": [0.0, 0.1], "ECG": [1.0, 2.0]})

    data = ECGDataLoader().load(path)

    assert data.time_source == "Seconds"
    assert list(data.channels) == ["ECG"]


def test_generates_time_when_sample_rate_is_supplied(tmp_path):
    from ecg_viewer.data import ECGDataLoader

    path = write_csv(tmp_path, {"Lead II": [0.2, 0.4, 0.6]})

    data = ECGDataLoader().load(path, sample_rate=250.0)

    np.testing.assert_allclose(data.time, [0.0, 0.004, 0.008])
    assert data.time_source == "generated from 250 Hz"
    assert data.sample_rate == 250.0


@pytest.mark.parametrize("sample_rate", [0, -1, float("inf"), float("nan")])
def test_rejects_invalid_sample_rate(tmp_path, sample_rate):
    from ecg_viewer.data import ECGDataError, ECGDataLoader

    path = write_csv(tmp_path, {"Lead II": [0.2, 0.4]})

    with pytest.raises(ECGDataError, match="Sample rate"):
        ECGDataLoader().load(path, sample_rate=sample_rate)


def test_requires_sample_rate_when_time_is_missing(tmp_path):
    from ecg_viewer.data import ECGDataError, ECGDataLoader

    path = write_csv(tmp_path, {"Lead II": [0.2, 0.4]})

    with pytest.raises(ECGDataError, match="SAMPLE_RATE_REQUIRED"):
        ECGDataLoader().load(path)


def test_invalid_time_candidate_falls_back_to_sample_rate(tmp_path):
    from ecg_viewer.data import ECGDataLoader

    path = write_csv(
        tmp_path,
        {"time": [0.0, 0.0, 1.0], "Lead II": [0.2, 0.4, 0.3]},
    )

    data = ECGDataLoader().load(path, sample_rate=100.0)

    assert list(data.channels) == ["time", "Lead II"]
    np.testing.assert_allclose(data.time, [0.0, 0.01, 0.02])


def test_ignores_text_metadata_but_preserves_channel_nan(tmp_path):
    from ecg_viewer.data import ECGDataLoader

    path = write_csv(
        tmp_path,
        {
            "seconds": [0.0, 0.1, 0.2],
            "patient": ["A", "A", "A"],
            "ECG": [1.0, None, 3.0],
        },
    )

    data = ECGDataLoader().load(path)

    assert list(data.channels) == ["ECG"]
    assert np.isnan(data.channels["ECG"][1])


def test_rejects_file_without_numeric_channel(tmp_path):
    from ecg_viewer.data import ECGDataError, ECGDataLoader

    path = write_csv(tmp_path, {"time": [0.0, 1.0], "note": ["a", "b"]})

    with pytest.raises(ECGDataError, match="numeric ECG channel"):
        ECGDataLoader().load(path)


def test_rejects_empty_csv(tmp_path):
    from ecg_viewer.data import ECGDataError, ECGDataLoader

    path = tmp_path / "empty.csv"
    path.write_text("")

    with pytest.raises(ECGDataError, match="empty"):
        ECGDataLoader().load(path)


def test_bundled_sample_ecg_loads():
    from ecg_viewer.data import ECGDataLoader

    path = Path(__file__).parents[1] / "data" / "sample_ecg.csv"

    data = ECGDataLoader().load(path)

    assert data.sample_count == 400
    assert list(data.channels) == ["Lead I", "Lead II"]
    assert data.duration == pytest.approx(3.99)
