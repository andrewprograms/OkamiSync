from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Depends
from starlette.websockets import WebSocketState
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_async_session
from app.tokens import extract_opaque, verify_session_cap
from app.ws.manager import manager
from app.models.tables import Table
from app.auth.deps import staff_required
from app.config import settings

router = APIRouter()

def _origin_allowed(origin: str) -> bool:
    allowed = set([o.strip() for o in settings.cors_allowlist.split(",") if o.strip()])
    return origin in allowed

@router.websocket("/ws/table")
async def ws_table(websocket: WebSocket, token: str = Query(...), session_id: str = Query(...), session_cap: str = Query(...), db: AsyncSession = Depends(get_async_session)):
    origin = websocket.headers.get("origin")
    if origin and not _origin_allowed(origin):
        await websocket.close(code=4403)
        return
    await websocket.accept()
    table = None
    try:
        opaque = extract_opaque(token)
        cap = verify_session_cap(session_cap)
        if not opaque or not cap:
            await websocket.close(code=4401); return
        res = await db.execute(select(Table).where(Table.opaque_uid==opaque))
        table = res.scalar_one_or_none()
        if not table or table.id != cap.get("tid"):
            await websocket.close(code=4403); return
        await manager.connect_table(table.id, websocket)
        await websocket.send_json({"event": "hello", "data": {"table_id": table.id}})
        while True:
            # No client->server messages required; keep alive by reading
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        if websocket.client_state != WebSocketState.DISCONNECTED:
            await websocket.close()
        if table:
            await manager.disconnect_table(table.id, websocket)

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
