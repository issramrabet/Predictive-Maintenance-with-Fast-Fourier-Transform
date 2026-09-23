"""
Loader for the NASA IMS Bearing Dataset raw files.

Dataset layout (as distributed, e.g. via the Kaggle mirror
https://www.kaggle.com/vinayak123tyagi/bearing-dataset): three "test" runs,
each a folder of plain-text files. Each file is one short recording snapshot
(20480 samples per channel, one row per sample, tab-separated), and the
filename itself is the timestamp it was recorded at, e.g.
"2003.10.22.12.06.24" = 2003-10-22 12:06:24.

- Test set 1: 8 columns = 4 bearings x 2 channels (x, y) each.
- Test sets 2 and 3: 4 columns = 4 bearings x 1 channel each.

Each test run ends when a bearing actually failed — the last file's
timestamp in a run is the ground-truth failure time, which is what makes
this dataset usable for "days until failure" labeling (see build_dataset.py).

IMPORTANT: verify the bearing geometry / rig constants below against the
`Readme Document for Bearing Data Set` that ships with the dataset itself
before trusting the computed BPFO/BPFI/BSF/FTF features — these are the
commonly-cited values for the dataset's Rexnord ZA-2115 bearings, but you
should confirm them from the source documentation, not from this comment.
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import numpy as np

FILENAME_RE = re.compile(r"^\d{4}\.\d{2}\.\d{2}\.\d{2}\.\d{2}\.\d{2}$")

# Commonly-cited rig parameters for the IMS test stand — VERIFY against the
# dataset's own Readme before relying on them for real analysis.
IMS_SAMPLE_RATE_HZ = 20_000
IMS_RPM = 2000.0          # constant shaft speed used across all three test runs
IMS_N_BALLS = 16
IMS_BALL_DIAMETER_MM = 8.4
IMS_PITCH_DIAMETER_MM = 71.5
IMS_CONTACT_ANGLE_DEG = 15.17


@dataclass
class IMSFile:
    path: Path
    timestamp: datetime


def list_ims_files(test_dir: str | Path) -> list[IMSFile]:
    """Return every snapshot file in a test-run folder, sorted chronologically."""
    test_dir = Path(test_dir)
    files = []
    for name in os.listdir(test_dir):
        if FILENAME_RE.match(name):
            ts = datetime.strptime(name, "%Y.%m.%d.%H.%M.%S")
            files.append(IMSFile(path=test_dir / name, timestamp=ts))
    files.sort(key=lambda f: f.timestamp)
    return files


def detect_channel_count(file_path: str | Path) -> int:
    with open(file_path, "r") as f:
        first_line = f.readline()
    return len(first_line.strip().split())


def channel_index(n_columns: int, bearing_index: int, axis: str = "x") -> int:
    """Map (bearing 0-3, axis) to a column index, for either the 1-channel-
    per-bearing (test 2/3) or 2-channel-per-bearing (test 1) file layout."""
    if n_columns == 4:
        return bearing_index
    if n_columns == 8:
        return bearing_index * 2 + (0 if axis == "x" else 1)
    raise ValueError(f"Unexpected column count {n_columns} — this doesn't look like an IMS file")


def load_ims_samples(file_path: str | Path, bearing_index: int, axis: str = "x") -> np.ndarray:
    """Load one bearing's channel from a single IMS snapshot file as a 1-D
    array of raw samples (dimensionless sensor units, per the dataset)."""
    data = np.loadtxt(file_path)
    if data.ndim == 1:
        data = data.reshape(-1, 1)
    col = channel_index(data.shape[1], bearing_index, axis)
    return data[:, col]
