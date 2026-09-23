from __future__ import annotations

import asyncio
import datetime

from sqlalchemy.orm import Session

from .config import settings
from .database import SessionLocal
from .fft_engine import analyze_frame
from .models import Snapshot, AlertLog, MachineConfigRow
from .physics import MachineConfig
from .simulator import SimulatedSensorSource
from .ws_manager import manager

sensor_source = SimulatedSensorSource()
_frame_counter = 0
_last_severity: str | None = None


def _load_machine_config(db: Session) -> MachineConfig:
    row = db.query(MachineConfigRow).filter(MachineConfigRow.id == 1).first()
    if row is None:
        return MachineConfig()
    return MachineConfig(
        N_rpm=row.N_rpm, n_balls=row.n_balls, Db_mm=row.Db_mm, De_mm=row.De_mm, Di_mm=row.Di_mm,
        phi_deg=row.phi_deg, fixation=row.fixation, f_secteur_hz=row.f_secteur_hz, slip_pct=row.slip_pct,
        gear_teeth=row.gear_teeth, pump_vanes=row.pump_vanes, power_kw=row.power_kw, foundation=row.foundation,
    )


async def acquisition_loop() -> None:
    """Runs for the lifetime of the app: reads a frame, analyzes it, persists a
    snapshot every N frames, records alert transitions, and broadcasts to all
    connected dashboard clients over WebSocket."""
    global _frame_counter, _last_severity
    period = 1.0 / max(settings.broadcast_hz, 0.1)

    while True:
        db = SessionLocal()
        try:
            cfg = _load_machine_config(db)
            frame = sensor_source.read_frame(cfg)
            result = analyze_frame(frame, cfg)

            _frame_counter += 1
            if _frame_counter % settings.snapshot_every_n_frames == 0:
                snap = Snapshot(
                    rms_x=result.rms_velocity_mm_s["x"],
                    rms_y=result.rms_velocity_mm_s["y"],
                    rms_z=result.rms_velocity_mm_s["z"],
                    temperature_c=result.temperature_c,
                    overall_severity=result.overall_severity,
                    active_fault=result.active_fault,
                    peak_accel_g_x=result.peak_accel_g["x"],
                    crest_factor_x=result.crest_factor["x"],
                    kurtosis_x=result.kurtosis["x"],
                    health_score=result.health_score,
                    peaks=result.peaks,
                )
                db.add(snap)
                db.commit()

            if result.overall_severity != "ok" and result.overall_severity != _last_severity:
                sev_label = "WARNING" if result.overall_severity == "warn" else "DANGER"
                db.add(AlertLog(
                    severity=result.overall_severity,
                    message=f"Severity moved to {sev_label} "
                            f"(max RMS velocity {max(result.rms_velocity_mm_s.values()):.2f} mm/s, "
                            f"health score {result.health_score:.0f}/100)",
                    rms_velocity_mm_s=max(result.rms_velocity_mm_s.values()),
                ))
                db.commit()
            _last_severity = result.overall_severity

            await manager.broadcast({
                "type": "live_frame",
                "timestamp": datetime.datetime.utcnow().isoformat(),
                "temperature_c": result.temperature_c,
                "rms_velocity_mm_s": result.rms_velocity_mm_s,
                "peak_accel_g": result.peak_accel_g,
                "crest_factor": result.crest_factor,
                "kurtosis": result.kurtosis,
                "health_score": result.health_score,
                "overall_severity": result.overall_severity,
                "spectrum": result.spectrum,
                "peaks": result.peaks,
                "defect_frequencies": result.defect_frequencies,
                "fixation_family": result.fixation_family,
                "active_fault": result.active_fault,
                "raw_waveform_x": frame.axis_x[:400],  # trimmed for transport; enough to draw a waveform
            })
        except Exception as exc:  # keep the loop alive even if a tick fails
            print(f"[acquisition_loop] error: {exc}")
        finally:
            db.close()

        await asyncio.sleep(period)
