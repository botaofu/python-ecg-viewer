# Python ECG Viewer Design

## 1. Purpose

Build a small but practically usable desktop ECG viewer. The application reads CSV files with pandas and displays one ECG channel at a time in an embedded Matplotlib canvas inside a PyQt6 window.

The first release is a viewing tool, not an analysis or diagnostic system. It does not perform filtering, peak detection, heart-rate estimation, annotation, or medical interpretation.

## 2. Scope and Success Criteria

The first release is successful when a user can:

1. Start the application from the documented command.
2. Open a CSV containing one or more numeric ECG channels.
3. Use an existing valid time column or enter a sample rate when no valid time column exists.
4. Select any discovered ECG channel.
5. Inspect the signal using Matplotlib zoom and pan controls.
6. Reset the plot to the full recording range.
7. See the selected channel's sample count, duration, minimum, and maximum.
8. Receive actionable error messages for invalid input without losing the previously loaded recording.

The repository will include sample data, automated tests, dependency metadata, and concise setup and usage documentation.

## 3. Technical Direction

- Python 3.10 or newer
- PyQt6 for the desktop interface
- pandas for CSV parsing and tabular data handling
- Matplotlib with the QtAgg backend for plotting and its native navigation toolbar
- NumPy for time-axis generation and numeric operations where useful
- pytest and pytest-qt for automated tests

The application uses a lightweight modular structure instead of a single large script or a full MVC framework.

## 4. Architecture

### 4.1 Data model

`ECGData` is a small immutable-style data object containing:

- `time`: one-dimensional floating-point values in seconds
- `channels`: mapping of channel name to one-dimensional numeric values
- `sample_rate`: optional floating-point value in hertz
- `source_path`: source CSV path
- `time_source`: either an identified CSV column or a generated time axis

This object is the contract between CSV loading and the UI. The plotting component does not read files or know how columns were inferred.

### 4.2 CSV loader

`ECGDataLoader` is responsible for:

- reading CSV data with pandas;
- rejecting empty or unreadable files;
- finding a valid time column;
- discovering numeric ECG channels;
- generating a time axis from a user-provided sample rate when needed; and
- returning `ECGData` or a domain-specific validation error.

Time-column matching is case-insensitive and considers common names such as `time`, `timestamp`, `seconds`, `second`, and `t`. A matched column is accepted only when it is numeric, contains no missing values, and is strictly increasing. If no candidate passes validation, the UI requests a sample rate rather than rejecting the file.

All remaining numeric columns are channel candidates. The chosen time column is excluded. Non-numeric columns are ignored. A file must contain at least one numeric ECG channel.

When the time axis is generated, sample `n` receives time `n / sample_rate`, beginning at zero. The sample rate must be finite and greater than zero.

### 4.3 Plot canvas

`ECGPlotCanvas` embeds a Matplotlib figure in Qt and exposes a focused interface:

- `plot_signal(time, values, channel_name)`
- `clear()`
- `reset_view()`

It labels time in seconds, labels amplitude generically because input units are not guaranteed, draws a light grid, and keeps the current full-data limits so reset works predictably. Matplotlib's standard Qt navigation toolbar supplies pan, zoom, and image saving.

### 4.4 Main window

`MainWindow` coordinates user actions and owns no CSV parsing logic. It contains:

- an Open CSV action;
- a Reset View action;
- the Matplotlib navigation toolbar;
- a channel selector;
- sample-rate information/input flow;
- a recording summary panel;
- the central ECG plot; and
- a status bar.

The window requests a file using `QFileDialog`. It first asks the loader to inspect the file. If a valid time column is unavailable, it uses a Qt numeric input dialog to obtain a positive sample rate and retries loading with that value. Cancelling either dialog cancels the load and leaves the current recording unchanged.

## 5. User Interface

The window uses a desktop viewer layout:

- Top: Open CSV, Reset View, and the Matplotlib navigation toolbar.
- Left sidebar: source filename, channel selector, sample-rate/time-source information, and basic data summary.
- Center: the ECG plot, which receives most of the available window area.
- Bottom: status messages such as load success, ignored columns, missing-value count, and errors that do not require a modal dialog.

The initial window has no loaded data, disables channel-specific actions, and explains how to open a CSV. After a successful load, the first discovered channel is selected and plotted automatically.

## 6. Data Flow

1. The user chooses a CSV file.
2. The main window calls the loader.
3. The loader reads the file and validates its structure.
4. If a valid time column exists, the loader returns `ECGData`.
5. Otherwise, the window requests a sample rate and calls the loader again with that value.
6. The window stores the returned `ECGData`, populates the channel selector, and selects the first channel.
7. Channel selection sends the shared time vector and selected values to the plot canvas.
8. The summary panel updates using pandas/NumPy statistics that ignore missing channel values.

## 7. Error Handling

- Missing, unreadable, empty, or malformed CSV files produce a modal error with a concise cause.
- A file with no usable numeric channel is rejected with guidance about the expected structure.
- A missing or invalid time column falls back to sample-rate input.
- A cancelled sample-rate dialog cancels the operation without changing current application state.
- Non-positive or non-finite sample rates are rejected.
- Missing values in a channel remain missing, producing visible gaps in the Matplotlib line. Summary statistics ignore them, and the status bar reports their count.
- Loader errors are converted into user-facing messages at the UI boundary; raw tracebacks are not shown in dialogs.
- A failed load never replaces the last successfully loaded recording.

The README states that the viewer is for visualization and does not provide medical diagnosis.

## 8. Proposed Project Structure

```text
python-ecg-viewer/
├── ecg_viewer/
│   ├── __init__.py
│   ├── __main__.py
│   ├── data.py
│   ├── plot.py
│   └── window.py
├── data/
│   └── sample_ecg.csv
├── tests/
│   ├── test_data.py
│   └── test_window.py
├── README.md
├── pyproject.toml
└── .gitignore
```

`data.py` contains the data object, loader, and validation errors. `plot.py` contains the Matplotlib canvas. `window.py` contains Qt widgets and orchestration. `__main__.py` is the application entry point.

## 9. Testing Strategy

Unit tests cover:

- valid named time-column recognition;
- rejection of non-numeric, missing, or non-increasing time candidates;
- generated time values from a sample rate;
- multi-channel discovery and time-column exclusion;
- ignored non-numeric metadata columns;
- empty input and input without a numeric ECG channel;
- invalid sample rates; and
- missing channel values.

pytest-qt tests run Qt in an offscreen-compatible mode and cover:

- main-window construction;
- initial disabled/empty state;
- successful data application to the channel selector and summary;
- channel switching triggering a plot refresh; and
- preservation of the current dataset when a later load fails.

Tests assert data and widget state, not rendered pixels. README steps provide a manual smoke test for opening the included sample, changing channels, zooming, panning, resetting the view, and closing the application.

## 10. Out of Scope

- WFDB or MIT-BIH file support
- Signal filtering or denoising
- R-peak detection and heart-rate estimation
- Annotations and result export
- Streaming or live acquisition
- Very-large-file paging or downsampling
- Packaging as a signed native installer
- Clinical interpretation or diagnostic output

These can be added later without changing the loader-to-data-to-view boundaries defined above.
