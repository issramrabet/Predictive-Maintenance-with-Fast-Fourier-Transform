from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .database import Base, engine
from .routers import config_router, realtime_router, history_router, status_router, rul_router
from .tasks import acquisition_loop

Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(acquisition_loop())
    yield
    task.cancel()


app = FastAPI(
    title="Vibration Signature Analysis API",
    description="Predictive maintenance API for asynchronous motor monitoring "
                 "(HS-173HT triaxial accelerometer + temperature) — H-FFT diagnostics, "
                 "ISO 20816-3 severity, real-time WebSocket telemetry.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(config_router.router)
app.include_router(realtime_router.router)
app.include_router(history_router.router)
app.include_router(status_router.router)
app.include_router(rul_router.router)


@app.get("/api/health")
def health():
    """Unauthenticated liveness check."""
    return {"status": "ok", "service": "vibration-monitor-api"}
