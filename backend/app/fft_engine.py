"""
FFT computation and peak-matching against the defect frequency catalog.

Takes a raw time-domain window from the sensor source and returns:
  - the windowed acceleration spectrum (H-FFT, 0..f_max Hz)
  - the overall RMS velocity (mm/s) used against ISO 20816 thresholds
  - amplitude at each catalogued defect frequency, matched to the nearest FFT bin
"""
from __future__ import annotations

import math
from dataclasses import dataclass, asdict

import numpy as np

from .physics import (
    MachineConfig,
    DefectFrequencies,
    compute_defect_frequencies,
    severity_thresholds,
    amplitude_thresholds,
    classify_severity,
    fixation_family,
    compute_health_score,
)
from .simulator import SensorFrame, SAMPLE_RATE_HZ


@dataclass
class SpectrumPoint:
    freq: float
    amplitude: float


@dataclass
class PeakReading:
    row: str
    label: str
    freq: float
    amplitude: float
    v_normal: float
    v_danger: float
    severity: str


@dataclass
class AnalysisResult:
    timestamp: float
    temperature_c: float
    rms_velocity_mm_s: dict          # per axis {x,y,z}
    overall_severity: str
    spectrum: list                   # SpectrumPoint list (axis chosen for display, x)
    peaks: list                      # PeakReading list
    defect_frequencies: dict
    fixation_family: str
    active_fault: str | None
    peak_accel_g: dict               # per axis {x,y,z}, mm/s^2 peak converted to g
    crest_factor: dict               # per axis {x,y,z} = peak / rms (dimensionless, unitless health indicator)
    kurtosis: dict                   # per axis {x,y,z} — 4th statistical moment, flags impulsive bearing faults
    health_score: float              # 0-100 composite index, formula-based (see physics.compute_health_score)


def _windowed_fft(samples: list[float]) -> tuple[np.ndarray, np.ndarray]:
    x = np.asarray(samples, dtype=float)
    n = len(x)
    window = np.hanning(n)
    xw = x * window
    spectrum = np.fft.rfft(xw)
    freqs = np.fft.rfftfreq(n, d=1.0 / SAMPLE_RATE_HZ)
    # scale factor to approximate single-sided amplitude, correcting for window loss
    amp = (np.abs(spectrum) / (n / 2)) / (window.sum() / n)
    return freqs, amp


def _velocity_rms_mm_s(samples: list[float]) -> float:
    """Approximate RMS velocity from acceleration by integrating in the
    frequency domain (v = a / omega), which is the standard vibration-analysis
    approach and avoids drift from naive time-domain integration."""
    x = np.asarray(samples, dtype=float)
    n = len(x)
    window = np.hanning(n)
    spectrum = np.fft.rfft(x * window)
    freqs = np.fft.rfftfreq(n, d=1.0 / SAMPLE_RATE_HZ)
    velocity_spec = np.zeros_like(spectrum)
    nonzero = freqs > 0.5  # avoid divide-by-near-zero on DC/very-low bins
    omega = 2 * np.pi * freqs[nonzero]
    # acceleration is in mm/s^2 already -> velocity in mm/s
    velocity_spec[nonzero] = spectrum[nonzero] / (1j * omega)
    v_time = np.fft.irfft(velocity_spec, n=n)
    return float(np.sqrt(np.mean(v_time ** 2)))


def _nearest_bin_amplitude(freqs: np.ndarray, amps: np.ndarray, target_hz: float, tol_hz: float = 2.0) -> float:
    if target_hz is None or math.isnan(target_hz) or target_hz <= 0:
        return 0.0
    idx = np.argmin(np.abs(freqs - target_hz))
    if abs(freqs[idx] - target_hz) > max(tol_hz, freqs[1] - freqs[0] if len(freqs) > 1 else tol_hz):
        # still return nearest, just flag isn't needed for now
        pass
    # take local max in a small window around idx to be tolerant of leakage
    lo = max(0, idx - 3)
    hi = min(len(amps), idx + 4)
    return float(np.max(amps[lo:hi])) if hi > lo else float(amps[idx])


def _peak_accel_g(samples: list[float]) -> float:
    """Peak acceleration in g (samples are already mm/s^2)."""
    x = np.asarray(samples, dtype=float)
    return float(np.max(np.abs(x)) / 9806.65)


def _kurtosis(samples: list[float]) -> float:
    """Standard (Fisher, non-excess) kurtosis of the raw acceleration signal.
    A healthy sinusoidal/random signal sits near 3; bearing impacts are
    highly impulsive and push kurtosis well above that — often the earliest
    numerical indicator of a developing bearing fault, ahead of RMS energy."""
    x = np.asarray(samples, dtype=float)
    std = float(np.std(x))
    if std == 0:
        return 3.0
    return float(np.mean(((x - np.mean(x)) / std) ** 4))


def _crest_factor(samples: list[float]) -> float:
    """Peak / RMS of the raw acceleration signal — a classic early-fault
    indicator: a healthy sinusoidal signal sits near 1.4 (sqrt(2)); sharp
    bearing impacts push it well above that even before RMS energy rises."""
    x = np.asarray(samples, dtype=float)
    rms = float(np.sqrt(np.mean(x ** 2)))
    if rms == 0:
        return 0.0
    return float(np.max(np.abs(x)) / rms)


def analyze_frame(frame: SensorFrame, cfg: MachineConfig) -> AnalysisResult:
    freqs, amp_x = _windowed_fft(frame.axis_x)
    _, amp_y = _windowed_fft(frame.axis_y)
    _, amp_z = _windowed_fft(frame.axis_z)

    v_normal, v_danger = severity_thresholds(cfg)
    rms = {
        "x": round(_velocity_rms_mm_s(frame.axis_x), 4),
        "y": round(_velocity_rms_mm_s(frame.axis_y), 4),
        "z": round(_velocity_rms_mm_s(frame.axis_z), 4),
    }
    overall_v = max(rms.values())
    overall_severity = classify_severity(overall_v, v_normal, v_danger)

    df = compute_defect_frequencies(cfg)

    peak_defs = [
        ("1", "1xRPM — Unbalance", df.fr),
        ("2", "2xRPM — Misalignment", df.f2x),
        ("3", "3xRPM — Mechanical looseness", df.f3x),
        ("4", "BPFO — Outer race defect", df.bpfo),
        ("5", "BPFI — Inner race defect", df.bpfi),
        ("6", "BSF — Rolling element defect", df.bsf),
        ("7", "FTF — Cage defect", df.ftf),
        ("9", "2x Mains — Electrical/stator fault", df.electrical_2x_mains),
        ("10", "1xRPM ± slip — Broken rotor bars", df.rotor_bar_lower),
        ("11", "GMF — Gear defect", df.gear_mesh),
        ("12", "BPF — Cavitation", df.blade_pass),
    ]

    peaks: list[PeakReading] = []
    for row, label, f in peak_defs:
        a = _nearest_bin_amplitude(freqs, amp_x, f)
        an, ad = amplitude_thresholds(f, v_normal, v_danger)
        sev = classify_severity(a, an, ad) if not math.isnan(an) else "ok"
        peaks.append(PeakReading(row=row, label=label, freq=round(f, 2) if f == f else 0.0,
                                  amplitude=round(a, 3), v_normal=round(an, 1) if an == an else 0.0,
                                  v_danger=round(ad, 1) if ad == ad else 0.0, severity=sev))

    # Fixation-family directional indicator (13 = feet / 14 = flange), no dedicated frequency,
    # judged from x (radial) vs z (axial) RMS growth relative to y (vertical reference).
    fam = fixation_family(cfg.fixation)
    if fam == "pattes":
        a13 = _nearest_bin_amplitude(freqs, amp_x, df.fr)
        an, ad = amplitude_thresholds(df.fr, v_normal, v_danger)
        peaks.append(PeakReading(row="13", label="1xRPM radial — Loose feet", freq=round(df.fr, 2),
                                  amplitude=round(a13, 3), v_normal=round(an, 1), v_danger=round(ad, 1),
                                  severity=classify_severity(a13, an, ad)))
    else:
        a14 = _nearest_bin_amplitude(freqs, amp_z, df.f2x)
        an, ad = amplitude_thresholds(df.f2x, v_normal, v_danger)
        peaks.append(PeakReading(row="14", label="2xRPM axial — Loose flange", freq=round(df.f2x, 2),
                                  amplitude=round(a14, 3), v_normal=round(an, 1), v_danger=round(ad, 1),
                                  severity=classify_severity(a14, an, ad)))

    # Downsample the spectrum for transport (frontend charts don't need every raw bin)
    max_points = 400
    fmax_display = max(500.0, df.gear_mesh * 1.15, df.blade_pass * 1.15, df.bpfi * 1.15)
    mask = freqs <= fmax_display
    f_disp = freqs[mask]
    a_disp = amp_x[mask]
    if len(f_disp) > max_points:
        step = len(f_disp) // max_points
        f_disp = f_disp[::step]
        a_disp = a_disp[::step]
    spectrum = [SpectrumPoint(freq=round(float(f), 2), amplitude=round(float(a), 4)) for f, a in zip(f_disp, a_disp)]

    peak_accel_g = {
        "x": round(_peak_accel_g(frame.axis_x), 4),
        "y": round(_peak_accel_g(frame.axis_y), 4),
        "z": round(_peak_accel_g(frame.axis_z), 4),
    }
    crest_factor = {
        "x": round(_crest_factor(frame.axis_x), 2),
        "y": round(_crest_factor(frame.axis_y), 2),
        "z": round(_crest_factor(frame.axis_z), 2),
    }
    kurtosis = {
        "x": round(_kurtosis(frame.axis_x), 2),
        "y": round(_kurtosis(frame.axis_y), 2),
        "z": round(_kurtosis(frame.axis_z), 2),
    }
    health_score = compute_health_score(overall_v, v_normal, v_danger)

    return AnalysisResult(
        timestamp=frame.timestamp,
        temperature_c=frame.temperature_c,
        rms_velocity_mm_s=rms,
        overall_severity=overall_severity,
        spectrum=[asdict(p) for p in spectrum],
        peaks=[asdict(p) for p in peaks],
        defect_frequencies=asdict(df),
        fixation_family=fam,
        active_fault=frame.active_fault,
        peak_accel_g=peak_accel_g,
        crest_factor=crest_factor,
        kurtosis=kurtosis,
        health_score=health_score,
    )
