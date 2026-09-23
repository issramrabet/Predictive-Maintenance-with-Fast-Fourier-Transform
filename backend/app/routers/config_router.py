from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import MachineConfigRow
from ..schemas import MachineConfigIn, MachineConfigOut
from ..security import require_api_key
from ..physics import (
    MachineConfig, FIXATION_LABELS, fixation_family, compute_defect_frequencies,
    severity_thresholds, amplitude_thresholds, PEAK_CATALOG,
)

router = APIRouter(prefix="/api/config", tags=["config"], dependencies=[Depends(require_api_key)])


def _row_to_cfg(row: MachineConfigRow) -> MachineConfig:
    return MachineConfig(
        N_rpm=row.N_rpm, n_balls=row.n_balls, Db_mm=row.Db_mm, De_mm=row.De_mm, Di_mm=row.Di_mm,
        phi_deg=row.phi_deg, fixation=row.fixation, f_secteur_hz=row.f_secteur_hz, slip_pct=row.slip_pct,
        gear_teeth=row.gear_teeth, pump_vanes=row.pump_vanes, power_kw=row.power_kw, foundation=row.foundation,
    )


def _get_or_create_row(db: Session) -> MachineConfigRow:
    row = db.query(MachineConfigRow).filter(MachineConfigRow.id == 1).first()
    if row is None:
        row = MachineConfigRow(id=1)
        db.add(row)
        db.commit()
        db.refresh(row)
    return row


@router.get("", response_model=MachineConfigOut)
def get_config(db: Session = Depends(get_db)):
    row = _get_or_create_row(db)
    cfg = _row_to_cfg(row)
    return MachineConfigOut(**cfg.__dict__, fr_hz=cfg.fr_hz)


@router.put("", response_model=MachineConfigOut)
def update_config(payload: MachineConfigIn, db: Session = Depends(get_db)):
    row = _get_or_create_row(db)
    for field, value in payload.model_dump().items():
        setattr(row, field, value)
    db.commit()
    db.refresh(row)
    cfg = _row_to_cfg(row)
    return MachineConfigOut(**cfg.__dict__, fr_hz=cfg.fr_hz)


@router.get("/fixation-codes")
def get_fixation_codes():
    return [
        {"code": code, **meta, "family": fixation_family(code)}
        for code, meta in FIXATION_LABELS.items()
    ]


@router.get("/defect-frequencies")
def get_defect_frequencies(db: Session = Depends(get_db)):
    """Preview computed defect frequencies + amplitude thresholds for the
    current machine config, same numbers the H-FFT page reads."""
    row = _get_or_create_row(db)
    cfg = _row_to_cfg(row)
    df = compute_defect_frequencies(cfg)
    v_normal, v_danger = severity_thresholds(cfg)
    out = []
    freq_map = {
        "1": df.fr, "2": df.f2x, "3": df.f3x, "4": df.bpfo, "5": df.bpfi, "6": df.bsf, "7": df.ftf,
        "9": df.electrical_2x_mains, "10": df.rotor_bar_lower, "11": df.gear_mesh, "12": df.blade_pass,
    }
    for entry in PEAK_CATALOG:
        f = freq_map.get(entry["row"])
        an, ad = amplitude_thresholds(f, v_normal, v_danger) if f is not None else (float("nan"), float("nan"))
        out.append({**entry, "freq_hz": round(f, 2) if f is not None and f == f else None,
                    "amp_normal": round(an, 1) if an == an else None,
                    "amp_danger": round(ad, 1) if ad == ad else None})
    return {"peaks": out, "v_normal": v_normal, "v_danger": v_danger, "fr_hz": cfg.fr_hz}
