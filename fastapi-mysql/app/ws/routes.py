from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Depends
from starlette.websockets import WebSocketState
from app.tokens import extract_opaque, verify_session_cap
from app.ws.manager import manager
from app.auth.deps import staff_required
from app.config import settings
from app.db import fetch_one

router = APIRouter()

def _origin_allowed(origin: str) -> bool:
    allowed = set([o.strip() for o in settings.cors_allowlist.split(",") if o.strip()])
    return origin in allowed

@router.websocket("/ws/table")
async def ws_table(websocket: WebSocket, token: str = Query(...), session_id: str = Query(...), session_cap: str = Query(...)):
    origin = websocket.headers.get("origin")
    if origin and not _origin_allowed(origin):
        await websocket.close(code=4403)
        return
    await websocket.accept()
    table_id = None
    try:
        opaque = extract_opaque(token)
        cap = verify_session_cap(session_cap)
        if not opaque or not cap:
            await websocket.close(code=4401); return
        row = await fetch_one("SELECT id FROM tables WHERE opaque_uid=%s LIMIT 1", (opaque,))
        if not row or row["id"] != cap.get("tid"):
            await websocket.close(code=4403); return
        table_id = row["id"]
        await manager.connect_table(table_id, websocket)
        await websocket.send_json({"event": "hello", "data": {"table_id": table_id}})
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        if websocket.client_state != WebSocketState.DISCONNECTED:
            await websocket.close()
        if table_id:
            await manager.disconnect_table(table_id, websocket)

@router.websocket("/ws/staff")
async def ws_staff(websocket: WebSocket, user=Depends(staff_required)):
    origin = websocket.headers.get("origin")
    if origin and not _origin_allowed(origin):
        await websocket.close(code=4403)
        return
    await websocket.accept()
    try:
        await manager.connect_staff(websocket)
        await websocket.send_json({"event": "hello", "data": {"role": user["role"]}})
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        await manager.disconnect_staff(websocket)
