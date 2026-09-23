
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

_BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from app.physics import MachineConfig, compute_defect_frequencies  # noqa: E402
from ims_loader import (  # noqa: E402
    IMS_SAMPLE_RATE_HZ,
    IMS_RPM,
    IMS_N_BALLS,
    IMS_BALL_DIAMETER_MM,
    IMS_PITCH_DIAMETER_MM,
    IMS_CONTACT_ANGLE_DEG,
)


FEATURE_NAMES = [
    "rms", "crest_factor", "kurtosis", "peak_accel_g",
    "bpfo_amp", "bpfi_amp", "bsf_amp", "ftf_amp",
]


def ims_machine_config() -> MachineConfig:
    """MachineConfig describing the IMS test rig, for computing defect
    frequencies with the same physics.py formulas the live app uses."""
    de = IMS_PITCH_DIAMETER_MM + IMS_BALL_DIAMETER_MM
    di = IMS_PITCH_DIAMETER_MM - IMS_BALL_DIAMETER_MM
    return MachineConfig(
        N_rpm=IMS_RPM,
        n_balls=IMS_N_BALLS,
        Db_mm=IMS_BALL_DIAMETER_MM,
        De_mm=de,
        Di_mm=di,
        phi_deg=IMS_CONTACT_ANGLE_DEG,
    )


def _windowed_fft(samples: np.ndarray, sample_rate: float) -> tuple[np.ndarray, np.ndarray]:
    n = len(samples)
    window = np.hanning(n)
    spectrum = np.fft.rfft(samples * window)
    freqs = np.fft.rfftfreq(n, d=1.0 / sample_rate)
    amp = (np.abs(spectrum) / (n / 2)) / (window.sum() / n)
    return freqs, amp


def _nearest_bin_amplitude(freqs: np.ndarray, amps: np.ndarray, target_hz: float) -> float:
    if target_hz is None or target_hz <= 0 or np.isnan(target_hz):
        return 0.0
    idx = int(np.argmin(np.abs(freqs - target_hz)))
    lo, hi = max(0, idx - 3), min(len(amps), idx + 4)
    return float(np.max(amps[lo:hi])) if hi > lo else float(amps[idx])


def _velocity_rms(samples: np.ndarray, sample_rate: float) -> float:
    """Same frequency-domain integration approach as fft_engine._velocity_rms_mm_s."""
    n = len(samples)
    window = np.hanning(n)
    spectrum = np.fft.rfft(samples * window)
    freqs = np.fft.rfftfreq(n, d=1.0 / sample_rate)
    velocity_spec = np.zeros_like(spectrum)
    nonzero = freqs > 0.5
    omega = 2 * np.pi * freqs[nonzero]
    velocity_spec[nonzero] = spectrum[nonzero] / (1j * omega)
    v_time = np.fft.irfft(velocity_spec, n=n)
    return float(np.sqrt(np.mean(v_time ** 2)))


def _crest_factor(samples: np.ndarray) -> float:
    rms = float(np.sqrt(np.mean(samples ** 2)))
    return float(np.max(np.abs(samples)) / rms) if rms else 0.0


def _kurtosis(samples: np.ndarray) -> float:
    std = float(np.std(samples))
    if std == 0:
        return 3.0
    return float(np.mean(((samples - np.mean(samples)) / std) ** 4))


def extract_features(samples: np.ndarray, sample_rate: float = IMS_SAMPLE_RATE_HZ) -> dict:
    """Compute the same feature set the live backend exposes, for one raw
    single-channel window of samples."""
    samples = np.asarray(samples, dtype=float)
    freqs, amp = _windowed_fft(samples, sample_rate)

    df = compute_defect_frequencies(ims_machine_config())

    return {
        "rms": _velocity_rms(samples, sample_rate),
        "crest_factor": _crest_factor(samples),
        "kurtosis": _kurtosis(samples),
        "peak_accel_g": float(np.max(np.abs(samples))),  # raw units — see note in ims_loader.py
        "bpfo_amp": _nearest_bin_amplitude(freqs, amp, df.bpfo),
        "bpfi_amp": _nearest_bin_amplitude(freqs, amp, df.bpfi),
        "bsf_amp": _nearest_bin_amplitude(freqs, amp, df.bsf),
        "ftf_amp": _nearest_bin_amplitude(freqs, amp, df.ftf),
    }
