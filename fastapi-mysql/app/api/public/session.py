import uuid, bleach
from fastapi import APIRouter, HTTPException
from app.db import fetch_one, execute
from app.schemas.public import SessionStartIn, SessionStartOut
from app.tokens import extract_opaque, issue_session_cap

router = APIRouter(prefix="/api/public", tags=["public"])

@router.post("/session/start", response_model=SessionStartOut)
async def session_start(payload: SessionStartIn):
    opaque = extract_opaque(payload.table_token)
    if not opaque:
        raise HTTPException(400, "Invalid table token")
    table = await fetch_one("SELECT id, name, active FROM tables WHERE opaque_uid=%s LIMIT 1", (opaque,))
    if not table or not table["active"]:
        raise HTTPException(404, "Unknown table")
    _device_id = bleach.clean(payload.device_id or "", strip=True)[:64] or str(uuid.uuid4())
    sess_id = str(uuid.uuid4())
    await execute("INSERT INTO table_sessions (id, table_id) VALUES (%s, %s)", (sess_id, table["id"]))
    cap = issue_session_cap(table_id=table["id"], session_id=sess_id, ttl_seconds=600)
    return SessionStartOut(table_id=table["id"], session_id=sess_id, session_cap=cap, table_name=table["name"])
