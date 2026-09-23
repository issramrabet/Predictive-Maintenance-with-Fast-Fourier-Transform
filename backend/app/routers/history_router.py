from __future__ import annotations

import datetime
from collections import Counter

from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Snapshot, AlertLog
from ..security import require_api_key

router = APIRouter(prefix="/api/history", tags=["history"], dependencies=[Depends(require_api_key)])


@router.get("/snapshots")
def get_snapshots(
    limit: int = Query(200, le=2000),
    since_minutes: int | None = Query(None, description="Only return snapshots from the last N minutes"),
    db: Session = Depends(get_db),
):
    q = db.query(Snapshot)
    if since_minutes:
        cutoff = datetime.datetime.utcnow() - datetime.timedelta(minutes=since_minutes)
        q = q.filter(Snapshot.timestamp >= cutoff)
    rows = q.order_by(desc(Snapshot.timestamp)).limit(limit).all()
    rows.reverse()
    return [
        {
            "id": r.id,
            "timestamp": r.timestamp.isoformat() if r.timestamp else None,
            "rms_x": r.rms_x, "rms_y": r.rms_y, "rms_z": r.rms_z,
            "temperature_c": r.temperature_c,
            "overall_severity": r.overall_severity,
            "active_fault": r.active_fault,
            "peak_accel_g_x": r.peak_accel_g_x,
            "crest_factor_x": r.crest_factor_x,
            "kurtosis_x": r.kurtosis_x,
            "health_score": r.health_score,
        }
        for r in rows
    ]


@router.get("/severity-summary")
def get_severity_summary(since_minutes: int | None = Query(None), db: Session = Depends(get_db)):
    """Counts of snapshots per severity bucket — feeds the severity
    distribution donut chart."""
    q = db.query(Snapshot)
    if since_minutes:
        cutoff = datetime.datetime.utcnow() - datetime.timedelta(minutes=since_minutes)
        q = q.filter(Snapshot.timestamp >= cutoff)
    counts = Counter(r.overall_severity for r in q.all())
    return {
        "ok": counts.get("ok", 0),
        "warn": counts.get("warn", 0),
        "danger": counts.get("danger", 0),
    }


@router.get("/alerts")
def get_alerts(limit: int = Query(50, le=500), db: Session = Depends(get_db)):
    rows = db.query(AlertLog).order_by(desc(AlertLog.timestamp)).limit(limit).all()
    return [
        {
            "id": r.id,
            "timestamp": r.timestamp.isoformat() if r.timestamp else None,
            "severity": r.severity,
            "message": r.message,
            "rms_velocity_mm_s": r.rms_velocity_mm_s,
        }
        for r in rows
    ]
