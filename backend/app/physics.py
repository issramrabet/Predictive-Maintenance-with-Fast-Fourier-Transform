"""
Vibration diagnostics physics core.

All defect-frequency formulas and ISO 20816-3 severity thresholds used by the
simulator, the FFT engine and the API live here so there is exactly one
source of truth (mirrors the logic originally prototyped in the HTML mockup).
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Literal

FixationCode = Literal["B3", "B35", "B5", "B14", "V1", "V3", "V5", "V6"]

# IEC 60034-7 mounting code -> fixation family.
# "pattes" (feet) faults show up as radial/vertical 1xRPM growth.
# "bride" (flange) faults show up as axial 1x/2xRPM growth.
FIXATION_FAMILY: dict[str, str] = {
    "B3": "pattes", "B35": "pattes", "V5": "pattes", "V6": "pattes",
    "B5": "bride", "B14": "bride", "V1": "bride", "V3": "bride",
}

FIXATION_LABELS: dict[str, dict] = {
    "B3": {"name": "Feet", "orientation": "Horizontal", "desc": "Feet mounted on the floor, free shaft end opposite the coupling — the most common mounting."},
    "B35": {"name": "Feet + flange", "orientation": "Horizontal", "desc": "Combines both — feet on the floor AND a flange on the front face, for extra rigidity."},
    "B5": {"name": "Flange (large)", "orientation": "Horizontal", "desc": "No feet at all, motor suspended solely by the flange."},
    "B14": {"name": "Flange (small/reduced)", "orientation": "Horizontal", "desc": "Like B5 but with a smaller flange, for compact mounting on equipment."},
    "V1": {"name": "Flange", "orientation": "Vertical", "desc": "Vertical shaft, flange at top, free end pointing down."},
    "V3": {"name": "Flange", "orientation": "Vertical", "desc": "Vertical shaft, flange at bottom, free end pointing up."},
    "V5": {"name": "Feet", "orientation": "Vertical", "desc": "Vertical shaft, feet wall-mounted, free end pointing down."},
    "V6": {"name": "Feet", "orientation": "Vertical", "desc": "Vertical shaft, feet wall-mounted, free end pointing up."},
}


def fixation_family(code: str) -> str:
    return FIXATION_FAMILY.get(code, "pattes")


@dataclass
class MachineConfig:
    # Rotation
    N_rpm: float = 1500.0          # tr/min
    # Bearing geometry
    n_balls: int = 8
    Db_mm: float = 8.0             # ball diameter
    De_mm: float = 48.0            # outer race diameter
    Di_mm: float = 32.0            # inner race diameter
    phi_deg: float = 0.0           # contact angle
    # Mounting
    fixation: FixationCode = "B3"
    # Machine-specific
    f_secteur_hz: float = 50.0     # mains frequency
    slip_pct: float = 3.0          # asynchronous motor slip
    gear_teeth: int = 20           # Z, if gearbox present
    pump_vanes: int = 6            # Nb, pump impeller vanes
    # Severity (ISO 20816-3)
    power_kw: float = 75.0
    foundation: Literal["rigide", "souple"] = "rigide"

    @property
    def fr_hz(self) -> float:
        """Rotation frequency f_r = N/60."""
        return self.N_rpm / 60.0

    @property
    def pitch_diameter_mm(self) -> float:
        return (self.De_mm + self.Di_mm) / 2.0

    @property
    def ball_pitch_ratio(self) -> float:
        pd = self.pitch_diameter_mm
        return self.Db_mm / pd if pd else 0.0

    @property
    def phi_rad(self) -> float:
        return math.radians(self.phi_deg)


@dataclass
class DefectFrequencies:
    fr: float
    f2x: float
    f3x: float
    bpfo: float
    bpfi: float
    bsf: float
    ftf: float
    electrical_2x_mains: float
    rotor_bar_lower: float
    rotor_bar_upper: float
    gear_mesh: float
    blade_pass: float


def compute_defect_frequencies(cfg: MachineConfig) -> DefectFrequencies:
    fr = cfg.fr_hz
    ratio = cfg.ball_pitch_ratio
    phi = cfg.phi_rad
    pd = cfg.pitch_diameter_mm
    n = cfg.n_balls

    bpfo = (n / 2) * fr * (1 - ratio * math.cos(phi))
    bpfi = (n / 2) * fr * (1 + ratio * math.cos(phi))
    bsf = (pd / (2 * cfg.Db_mm)) * fr * (1 - (ratio ** 2) * (math.cos(phi) ** 2)) if cfg.Db_mm else float("nan")
    ftf = 0.5 * fr * (1 - ratio * math.cos(phi))
    s = cfg.slip_pct / 100.0

    return DefectFrequencies(
        fr=fr,
        f2x=2 * fr,
        f3x=3 * fr,
        bpfo=bpfo,
        bpfi=bpfi,
        bsf=bsf,
        ftf=ftf,
        electrical_2x_mains=2 * cfg.f_secteur_hz,
        rotor_bar_lower=fr * (1 - s),
        rotor_bar_upper=fr * (1 + s),
        gear_mesh=cfg.gear_teeth * fr,
        blade_pass=cfg.pump_vanes * fr,
    )


# ISO 20816-3 severity table: {group: {foundation: (v_normal, v_danger)}} in mm/s RMS
# Group 1 = P > 300 kW, Group 2 = P <= 300 kW
SEVERITY_TABLE = {
    1: {"rigide": (4.5, 7.1), "souple": (7.1, 11.0)},
    2: {"rigide": (2.8, 4.5), "souple": (4.5, 7.1)},
}


def severity_thresholds(cfg: MachineConfig) -> tuple[float, float]:
    group = 1 if cfg.power_kw > 300 else 2
    return SEVERITY_TABLE[group][cfg.foundation]


def amplitude_thresholds(freq_hz: float, v_normal: float, v_danger: float) -> tuple[float, float]:
    """Convert a velocity severity threshold (mm/s) to an acceleration amplitude
    threshold (mm/s^2) at a given defect frequency: a = 2*pi*f*v."""
    if freq_hz is None or freq_hz <= 0 or math.isnan(freq_hz):
        return (float("nan"), float("nan"))
    omega = 2 * math.pi * freq_hz
    return (omega * v_normal, omega * v_danger)


def classify_severity(value: float, v_normal: float, v_danger: float) -> Literal["ok", "warn", "danger"]:
    if value <= v_normal:
        return "ok"
    if value <= v_danger:
        return "warn"
    return "danger"


def compute_health_score(overall_v: float, v_normal: float, v_danger: float) -> float:
    """Formula-based composite health index (0-100), derived directly from the
    ISO 20816-3 velocity thresholds already in force for this machine — NOT a
    trained model. 100 = no measurable vibration, 70 = right at the B/C
    boundary, 30 = right at the C/D boundary, decaying to 0 by 1.5x the
    danger threshold. A learned RUL/health model (e.g. trained on MAFAULDA or
    the NASA/IMS bearing datasets) could replace or augment this later."""
    if v_normal <= 0 or v_danger <= 0:
        return 100.0
    if overall_v <= v_normal:
        score = 100 - 30 * (overall_v / v_normal)
    elif overall_v <= v_danger:
        score = 70 - 40 * ((overall_v - v_normal) / (v_danger - v_normal))
    else:
        decay_span = 0.5 * v_danger
        score = 30 - 30 * ((overall_v - v_danger) / decay_span) if decay_span > 0 else 0
    return round(max(0.0, min(100.0, score)), 1)


PEAK_CATALOG = [
    {"row": "1", "code": "1xRPM", "name": "Unbalance",
     "desc": "Unbalanced mass on the rotor — sharp peak at the exact rotation frequency.",
     "formula": "f = N / 60"},
    {"row": "2", "code": "2xRPM", "name": "Misalignment",
     "desc": "Motor/pump shafts misaligned — dominant peak at twice the rotation speed.",
     "formula": "f = 2 x (N / 60)"},
    {"row": "3", "code": "3xRPM+", "name": "Mechanical looseness",
     "desc": "Loose mounting — several successive harmonics of the rotation speed.",
     "formula": "f = k x (N/60), k=3,4,5..."},
    {"row": "4", "code": "BPFO", "name": "Outer race defect",
     "desc": "Spalling or pitting on the bearing's outer raceway.",
     "formula": "f = (n/2)(N/60)[1 - (2Db/(De+Di))cos(phi)]"},
    {"row": "5", "code": "BPFI", "name": "Inner race defect",
     "desc": "Spalling on the inner raceway, often accompanied by sidebands at 1xRPM.",
     "formula": "f = (n/2)(N/60)[1 + (2Db/(De+Di))cos(phi)]"},
    {"row": "6", "code": "BSF", "name": "Rolling element defect",
     "desc": "Localized defect on a ball or roller of the bearing.",
     "formula": "f = ((De+Di)/4Db)(N/60)[1-(2Db/(De+Di))^2 cos^2(phi)]"},
    {"row": "7", "code": "FTF", "name": "Cage defect",
     "desc": "Bearing cage wear or crack — low, sub-synchronous frequency.",
     "formula": "f = 0.5(N/60)[1 - (2Db/(De+Di))cos(phi)]"},
    {"row": "8", "code": "HF-NOISE", "name": "Lubrication deficiency",
     "desc": "Insufficient lubricant — raises the broadband noise floor before a sharp peak appears.",
     "formula": "global HF RMS indicator"},
    {"row": "9", "code": "2xMAINS", "name": "Electrical / stator fault",
     "desc": "Air-gap issue, shorted turns, or loose stator core.",
     "formula": "f = 2 x f_mains"},
    {"row": "10", "code": "RPMxSLIP", "name": "Broken rotor bars",
     "desc": "Sidebands around the rotation speed, caused by a broken rotor bar.",
     "formula": "f = (N/60)(1 +/- s)"},
    {"row": "11", "code": "GMF", "name": "Gear defect",
     "desc": "Worn or broken gear tooth (if a gearbox is present).",
     "formula": "f = Z x (N/60)"},
    {"row": "12", "code": "BPF", "name": "Cavitation / hydraulic fault",
     "desc": "Turbulence or cavitation at the pump impeller.",
     "formula": "f = Nb x (N/60)"},
    {"row": "13", "code": "FEET", "name": "Loose / cracked feet",
     "desc": "Play at the foot mounting — accentuated radial/vertical vibration at 1xRPM.",
     "formula": "directional indicator"},
    {"row": "14", "code": "FLANGE", "name": "Loose flange / flange bolts",
     "desc": "Play at the flange bolts — accentuated axial vibration.",
     "formula": "directional indicator"},
]
