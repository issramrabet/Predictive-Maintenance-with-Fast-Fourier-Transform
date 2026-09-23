from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import MachineConfigRow
from ..fft_engine import analyze_frame
from ..tasks import sensor_source, _load_machine_config
from ..security import require_api_key
from ..physics import severity_thresholds

router = APIRouter(prefix="/api/status", tags=["status"], dependencies=[Depends(require_api_key)])


@router.get("")
def get_status(db: Session = Depends(get_db)):
    """One-shot current reading — useful for the config page to preview
    thresholds/frequencies without waiting on the websocket, and as an HTTP
    fallback if WebSocket is unavailable behind a restrictive proxy."""
    cfg = _load_machine_config(db)
    frame = sensor_source.read_frame(cfg)
    result = analyze_frame(frame, cfg)
    v_normal, v_danger = severity_thresholds(cfg)
    return {
        "temperature_c": result.temperature_c,
        "rms_velocity_mm_s": result.rms_velocity_mm_s,
        "peak_accel_g": result.peak_accel_g,
        "crest_factor": result.crest_factor,
        "kurtosis": result.kurtosis,
        "health_score": result.health_score,
        "overall_severity": result.overall_severity,
        "v_normal": v_normal,
        "v_danger": v_danger,
        "active_fault": result.active_fault,
        "fixation_family": result.fixation_family,
    }
