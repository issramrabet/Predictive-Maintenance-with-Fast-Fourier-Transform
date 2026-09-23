from __future__ import annotations

from typing import Literal, Optional
from pydantic import BaseModel, Field


class MachineConfigIn(BaseModel):
    N_rpm: float = Field(1500.0, gt=0, description="Vitesse de rotation, tr/min")
    n_balls: int = Field(8, gt=0)
    Db_mm: float = Field(8.0, gt=0)
    De_mm: float = Field(48.0, gt=0)
    Di_mm: float = Field(32.0, gt=0)
    phi_deg: float = 0.0
    fixation: Literal["B3", "B35", "B5", "B14", "V1", "V3", "V5", "V6"] = "B3"
    f_secteur_hz: float = Field(50.0, gt=0)
    slip_pct: float = Field(3.0, ge=0, le=100)
    gear_teeth: int = Field(20, ge=0)
    pump_vanes: int = Field(6, ge=0)
    power_kw: float = Field(75.0, gt=0)
    foundation: Literal["rigide", "souple"] = "rigide"


class MachineConfigOut(MachineConfigIn):
    fr_hz: float


class DemoFaultIn(BaseModel):
    fault: Optional[str] = Field(None, description="Peak row id ('1'..'14') to inject, or null for healthy")


class SnapshotOut(BaseModel):
    id: int
    timestamp: str
    rms_x: float
    rms_y: float
    rms_z: float
    temperature_c: float
    overall_severity: str
    active_fault: Optional[str]

    class Config:
        from_attributes = True


class AlertOut(BaseModel):
    id: int
    timestamp: str
    severity: str
    message: str
    rms_velocity_mm_s: float

    class Config:
        from_attributes = True
