from __future__ import annotations

from sqlalchemy import Column, Integer, Float, String, DateTime, JSON
from sqlalchemy.sql import func

from .database import Base


class MachineConfigRow(Base):
    """Single-row table holding the current machine configuration (id=1)."""
    __tablename__ = "machine_config"

    id = Column(Integer, primary_key=True, default=1)
    N_rpm = Column(Float, default=1500.0)
    n_balls = Column(Integer, default=8)
    Db_mm = Column(Float, default=8.0)
    De_mm = Column(Float, default=48.0)
    Di_mm = Column(Float, default=32.0)
    phi_deg = Column(Float, default=0.0)
    fixation = Column(String, default="B3")
    f_secteur_hz = Column(Float, default=50.0)
    slip_pct = Column(Float, default=3.0)
    gear_teeth = Column(Integer, default=20)
    pump_vanes = Column(Integer, default=6)
    power_kw = Column(Float, default=75.0)
    foundation = Column(String, default="rigide")
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())


class Snapshot(Base):
    """Periodic persisted reading: RMS velocities, temperature, severity, active fault."""
    __tablename__ = "snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    rms_x = Column(Float)
    rms_y = Column(Float)
    rms_z = Column(Float)
    temperature_c = Column(Float)
    overall_severity = Column(String)
    active_fault = Column(String, nullable=True)
    peak_accel_g_x = Column(Float, nullable=True)
    crest_factor_x = Column(Float, nullable=True)
    kurtosis_x = Column(Float, nullable=True)
    health_score = Column(Float, nullable=True)
    peaks = Column(JSON)  # list of {row, label, freq, amplitude, severity}


class AlertLog(Base):
    """Recorded whenever overall severity transitions into warn/danger."""
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    severity = Column(String)
    message = Column(String)
    rms_velocity_mm_s = Column(Float)
