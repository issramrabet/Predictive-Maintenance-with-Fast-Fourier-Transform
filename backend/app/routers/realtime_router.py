from __future__ import annotations

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends

from ..schemas import DemoFaultIn
from ..security import require_api_key
from ..tasks import sensor_source
from ..ws_manager import manager
from ..physics import PEAK_CATALOG

router = APIRouter(prefix="/api/realtime", tags=["realtime"])


@router.websocket("/ws")
async def live_feed(websocket: WebSocket):
    """Streams one analyzed frame per broadcast tick (see VIBRO_BROADCAST_HZ).
    No auth on the socket itself in dev mode; put this behind your reverse
    proxy / auth layer before exposing it beyond localhost."""
    await manager.connect(websocket)
    try:
        while True:
            # keep the connection alive; all data is pushed from acquisition_loop
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@router.post("/demo-fault", dependencies=[Depends(require_api_key)])
def set_demo_fault(payload: DemoFaultIn):
    """Training/demo mode: force the simulator to inject a specific defect
    signature (row id from the peak catalog, e.g. '5' = BPFI), or null to
    return to a healthy baseline. Swapped out entirely once real hardware
    is wired to a SensorSource."""
    sensor_source.set_active_fault(payload.fault)
    return {"active_fault": payload.fault}


@router.get("/fault-options")
def fault_options():
    return [{"row": "healthy", "label": "Normal operation (no fault)"}] + \
        [{"row": p["row"], "label": p["name"]} for p in PEAK_CATALOG]
