"""
Loads the RUL model trained by ml/train_rul_model.py, if one has been
trained yet. If backend/app/ml_models/model.joblib doesn't exist (i.e. the
training pipeline in ml/ hasn't been run), predict_rul() returns None and
the API reports model_available: false — no fabricated numbers are ever
returned.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

MODEL_DIR = Path(__file__).resolve().parent / "ml_models"
MODEL_PATH = MODEL_DIR / "model.joblib"
META_PATH = MODEL_DIR / "feature_names.json"

_model = None
_meta: Optional[dict] = None
_load_attempted = False


def _load():
    global _model, _meta, _load_attempted
    if _load_attempted:
        return
    _load_attempted = True
    if not MODEL_PATH.exists():
        return
    try:
        import joblib  # imported lazily so the backend doesn't hard-require
        # scikit-learn/joblib until a model actually exists to load
        _model = joblib.load(MODEL_PATH)
        if META_PATH.exists():
            with open(META_PATH) as f:
                _meta = json.load(f)
    except Exception as exc:  # noqa: BLE001 — log and degrade gracefully
        print(f"[rul_model] failed to load {MODEL_PATH}: {exc}")
        _model = None


def is_available() -> bool:
    _load()
    return _model is not None


def get_metadata() -> Optional[dict]:
    _load()
    return _meta


def predict_rul(features: dict) -> Optional[float]:
    """features must contain the keys listed in feature_names.json (same
    order not required — we reindex by name). Returns predicted remaining
    days, or None if no model has been trained yet."""
    _load()
    if _model is None:
        return None
    feature_names = (_meta or {}).get("feature_names") or list(features.keys())
    row = [[features[name] for name in feature_names]]
    prediction = _model.predict(row)[0]
    return float(max(0.0, prediction))
