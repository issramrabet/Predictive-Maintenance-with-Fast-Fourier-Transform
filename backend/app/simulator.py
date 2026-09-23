"""
Simulated HS-173HT sensor source.

The real HS-173HT is a triaxial 100 mV/g accelerometer + 10 mV/degC analog
output; a physical deployment would read it through a DAQ/ADC (see
`SensorSource` below for the swap point). Until that hardware is wired up,
`SimulatedSensorSource` generates physically-plausible triaxial vibration
waveforms (with real defect signatures keyed off the same catalog the H-FFT
page displays) plus a slowly drifting bearing temperature.
"""
from __future__ import annotations

import math
import random
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass

from .physics import MachineConfig, fixation_family, compute_defect_frequencies, DefectFrequencies

SAMPLE_RATE_HZ = 2048          # samples/sec per axis, matches typical low-cost DAQ
WINDOW_SECONDS = 1.0           # one FFT window per broadcast tick
N_SAMPLES = int(SAMPLE_RATE_HZ * WINDOW_SECONDS)


@dataclass
class SensorFrame:
    timestamp: float
    axis_x: list  # raw acceleration samples, mm/s^2
    axis_y: list
    axis_z: list
    temperature_c: float
    active_fault: str | None  # which defect the simulator is currently injecting (demo control)


def _pseudo_noise(t: float) -> float:
    return (
        0.5 * math.sin(53.3 * t + 1.0)
        + 0.3 * math.sin(97.7 * t + 2.4)
        + 0.2 * math.sin(133.1 * t + 0.7)
        + 0.15 * math.sin(211.9 * t + 3.1)
    )


def _period_from_freq(freq: float, fallback_period: float) -> float:
    """Convert a defect frequency (Hz) into an impact repetition period
    (seconds), so the simulator's injected fault energy actually lands at
    the same frequency physics.py computes for the peak table — instead of
    firing at a fixed, config-independent rate. Falls back to the original
    hardcoded demo period if the frequency is missing/non-finite (e.g. an
    edge-case bearing geometry with Db=0) or implausibly high for the
    simulator's sample rate."""
    if freq is None or not math.isfinite(freq) or freq <= 0.5:
        return fallback_period
    if freq > SAMPLE_RATE_HZ / 4:  # avoid aliasing artifacts at extreme geometries
        return fallback_period
    return 1.0 / freq


class SensorSource(ABC):
    """Abstraction over where samples come from. Swap this out for a real
    DAQ/Modbus/serial reader when the HS-173HT is wired to hardware — nothing
    downstream (FFT engine, API, frontend) needs to change."""

    @abstractmethod
    def read_frame(self, cfg: MachineConfig) -> SensorFrame:
        ...


class SimulatedSensorSource(SensorSource):
    """Deterministic-but-drifting synthetic signal generator.

    `active_fault` can be set by the API (demo/training mode) to force a
    specific defect signature onto the waveform so the dashboard and H-FFT
    page can be exercised without physical hardware.
    """

    def __init__(self) -> None:
        self.active_fault: str | None = None
        self._t0 = time.time()
        self._temp_base = 42.0
        self._rng = random.Random(1234)

    def set_active_fault(self, fault: str | None) -> None:
        self.active_fault = fault

    def _signature(self, t: float, fr: float, fault: str | None, df: DefectFrequencies | None = None) -> float:
        """Return a unit-scale time-domain sample for the currently selected
        defect signature. Mirrors the per-defect waveform shapes from the
        original prototype. `df` (the current MachineConfig's computed
        defect frequencies) is used to make BPFO/BPFI/BSF/FTF impact rates
        track whatever bearing geometry is currently configured, instead of
        firing at a hardcoded demo rate — this keeps the H-FFT peak table
        and the RUL model's amplitude features consistent with the signal
        actually being generated. See physics.py for the frequency math."""
        f0 = fr if fr > 0 else 25.0

        if fault is None or fault == "healthy":
            y = 0.35 * math.sin(2 * math.pi * f0 * t)
            tt = t % 0.5
            if tt < 0.02:
                y -= 0.15 * math.exp(-tt * 400) * math.sin(2 * math.pi * 90 * tt)
            return y

        if fault == "1":  # unbalance
            return 0.55 * math.sin(2 * math.pi * f0 * t)

        if fault == "2":  # misalignment
            return 0.25 * math.sin(2 * math.pi * f0 * t) + 0.5 * math.sin(2 * math.pi * 2 * f0 * t)

        if fault == "3":  # looseness
            y = (0.35 * math.sin(2 * math.pi * f0 * t) + 0.3 * math.sin(2 * math.pi * 2 * f0 * t)
                 + 0.25 * math.sin(2 * math.pi * 3 * f0 * t) + 0.15 * math.sin(2 * math.pi * 4 * f0 * t))
            return max(-0.7, min(0.7, y * 1.3))

        if fault == "4":  # BPFO — impact rate now tracks the configured bearing's actual BPFO
            y = 0.12 * math.sin(2 * math.pi * f0 * t)
            period = _period_from_freq(df.bpfo if df else None, fallback_period=0.22)
            tt = t % period
            if tt < min(0.05, period * 0.4):
                y -= 0.95 * math.exp(-tt * 130) * math.sin(2 * math.pi * 180 * tt)
            return y

        if fault == "5":  # BPFI (amplitude-modulated by 1xRPM) — impact rate tracks the configured BPFI
            y = 0.12 * math.sin(2 * math.pi * f0 * t)
            envelope = 0.5 + 0.5 * math.sin(2 * math.pi * f0 * t - math.pi / 2)
            period = _period_from_freq(df.bpfi if df else None, fallback_period=0.18)
            tt = t % period
            if tt < min(0.045, period * 0.4):
                y -= envelope * 0.9 * math.exp(-tt * 140) * math.sin(2 * math.pi * 220 * tt)
            return y

        if fault == "6":  # BSF — impact rate tracks the configured BSF; envelope modulates at cage speed (FTF)
            y = 0.10 * math.sin(2 * math.pi * f0 * t)
            cage_freq = df.ftf if df and df.ftf and math.isfinite(df.ftf) and df.ftf > 0 else f0 * 0.38
            envelope = 0.4 + 0.6 * math.sin(2 * math.pi * cage_freq * t)
            period = _period_from_freq(df.bsf if df else None, fallback_period=0.27)
            tt = t % period
            if tt < min(0.04, period * 0.4):
                y -= max(0.15, envelope) * 0.8 * math.exp(-tt * 150) * math.sin(2 * math.pi * 160 * tt)
            return y

        if fault == "7":  # FTF — smooth sub-synchronous modulation at the configured cage frequency
            cage_freq = df.ftf if df and df.ftf and math.isfinite(df.ftf) and df.ftf > 0 else f0 * 0.35
            return 0.5 * math.sin(2 * math.pi * cage_freq * t) * (0.6 + 0.4 * math.sin(2 * math.pi * f0 * 0.05 * t))

        if fault == "8":  # lubrication / broadband noise
            return 0.15 * math.sin(2 * math.pi * f0 * t) + 0.4 * _pseudo_noise(t)

        if fault == "9":  # electrical / stator
            return 0.3 * math.sin(2 * math.pi * (f0 * 3) * t) + 0.25 * math.sin(2 * math.pi * (f0 * 3.15) * t)

        if fault == "10":  # broken rotor bars
            return (0.5 + 0.4 * math.sin(2 * math.pi * (f0 * 0.12) * t)) * math.sin(2 * math.pi * f0 * t)

        if fault == "11":  # gear mesh
            return (0.5 + 0.35 * math.sin(2 * math.pi * f0 * t)) * math.sin(2 * math.pi * (f0 * 4) * t)

        if fault == "12":  # cavitation
            return 0.2 * math.sin(2 * math.pi * f0 * t) + 0.5 * _pseudo_noise(t * 1.7) * (0.5 + 0.5 * math.sin(2 * math.pi * 0.7 * t))

        if fault == "13":  # loose feet
            y = 0.5 * math.sin(2 * math.pi * f0 * t) + 0.18 * math.sin(2 * math.pi * 2 * f0 * t)
            return y if y > 0 else y * 1.35

        if fault == "14":  # loose flange
            y = 0.35 * math.sin(2 * math.pi * f0 * t) + 0.35 * math.sin(2 * math.pi * 2 * f0 * t)
            return max(-0.35, y)

        return 0.35 * math.sin(2 * math.pi * f0 * t)

    def read_frame(self, cfg: MachineConfig) -> SensorFrame:
        now = time.time()
        elapsed = now - self._t0
        fr = cfg.fr_hz
        fault = self.active_fault
        df = compute_defect_frequencies(cfg)  # single source of truth, shared with the peak table and RUL features

        amp_g_to_mm_s2 = 9806.65  # 1 g in mm/s^2, HS-173HT outputs are g-referenced
        base_scale = 0.18 * amp_g_to_mm_s2 / 1000.0  # keep values in a readable mm/s^2 band

        axis_x, axis_y, axis_z = [], [], []
        for i in range(N_SAMPLES):
            t = elapsed + i / SAMPLE_RATE_HZ
            core = self._signature(t, fr, fault, df)
            micro_noise = 0.03 * _pseudo_noise(t * 2.3)

            # Fixation-family faults primarily load the radial (x) or axial (z) axis.
            fam = fixation_family(cfg.fixation)
            fixation_bias_x = 0.0
            fixation_bias_z = 0.0
            if fault == "13" and fam == "pattes":
                fixation_bias_x = 0.25 * core
            if fault == "14" and fam == "bride":
                fixation_bias_z = 0.3 * core

            axis_x.append((core + micro_noise + fixation_bias_x) * base_scale * 1000)
            axis_y.append((0.7 * core + micro_noise * 1.1) * base_scale * 1000)
            axis_z.append((0.5 * core + micro_noise * 0.8 + fixation_bias_z) * base_scale * 1000)

        # Slow thermal drift + small periodic ripple + noise, degC, mirrors 10 mV/degC channel
        drift = 3.5 * math.sin(elapsed / 240.0)
        load_bump = 6.0 if fault in {"4", "5", "6", "8"} else 0.0  # bearing distress runs hotter
        temperature = self._temp_base + drift + load_bump + self._rng.uniform(-0.15, 0.15)

        return SensorFrame(
            timestamp=now,
            axis_x=axis_x,
            axis_y=axis_y,
            axis_z=axis_z,
            temperature_c=round(temperature, 2),
            active_fault=fault,
        )
