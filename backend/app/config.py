from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    api_key: str = "dev-local-key-change-me"
    require_api_key: bool = False

    # Database
    database_url: str = "sqlite:///./vibration_monitor.db"

    # Simulation / acquisition
    broadcast_hz: float = 1.0          # how often a new frame is analyzed & pushed
    snapshot_every_n_frames: int = 5   # how often a frame is persisted to history

    # CORS
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    model_config = SettingsConfigDict(env_file=".env", env_prefix="VIBRO_")


settings = Settings()
