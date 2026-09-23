from __future__ import annotations

from fastapi import Header, HTTPException, status

from .config import settings


async def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    """Simple shared-secret guard. Disabled by default for local dev
    (VIBRO_REQUIRE_API_KEY=false); enable it and set VIBRO_API_KEY in .env
    before exposing the backend beyond localhost."""
    if not settings.require_api_key:
        return
    if not x_api_key or x_api_key != settings.api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing API key")
