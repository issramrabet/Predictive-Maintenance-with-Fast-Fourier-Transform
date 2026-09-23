from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..fft_engine import analyze_frame
from ..rul_model import predict_rul, is_available, get_metadata
from ..security import require_api_key
from ..tasks import sensor_source, _load_machine_config

router = APIRouter(prefix="/api/status", tags=["rul"], dependencies=[Depends(require_api_key)])


@router.get("/rul")
def get_rul(db: Session = Depends(get_db)):
    """Predicted remaining useful life, in days, from the trained model in
    backend/app/ml_models/ (see ml/README.md to train one). Returns
    model_available: false with no prediction if nothing has been trained
    yet — this endpoint never fabricates a number."""
    if not is_available():
        return {"model_available": False, "remaining_days": None, "metadata": None}

    cfg = _load_machine_config(db)
    frame = sensor_source.read_frame(cfg)
    result = analyze_frame(frame, cfg)

    # Map the live analysis result onto the same feature names the model
    # was trained on (see ml/features.py FEATURE_NAMES).
    bpfo = bpfi = bsf = ftf = 0.0
    for p in result.peaks:
        if p["row"] == "4":
            bpfo = p["amplitude"]
        elif p["row"] == "5":
            bpfi = p["amplitude"]
        elif p["row"] == "6":
            bsf = p["amplitude"]
        elif p["row"] == "7":
            ftf = p["amplitude"]

    features = {
        "rms": result.rms_velocity_mm_s["x"],
        "crest_factor": result.crest_factor["x"],
        "kurtosis": result.kurtosis["x"],
        "peak_accel_g": result.peak_accel_g["x"],
        "bpfo_amp": bpfo,
        "bpfi_amp": bpfi,
        "bsf_amp": bsf,
        "ftf_amp": ftf,
    }

    remaining_days = predict_rul(features)
    return {
        "model_available": True,
        "remaining_days": remaining_days,
        "metadata": get_metadata(),
    }
