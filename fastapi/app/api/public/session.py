import uuid, bleach
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_async_session
from app.models.tables import Table, TableSession
from app.schemas.public import SessionStartIn, SessionStartOut
from app.tokens import extract_opaque, issue_session_cap

router = APIRouter(prefix="/api/public", tags=["public"])

@router.post("/session/start", response_model=SessionStartOut)
async def session_start(payload: SessionStartIn, session: AsyncSession = Depends(get_async_session)):
    opaque = extract_opaque(payload.table_token)
    if not opaque:
        raise HTTPException(400, "Invalid table token")
    res = await session.execute(select(Table).where(Table.opaque_uid == opaque))
    table = res.scalar_one_or_none()
    if not table or not table.active:
        raise HTTPException(404, "Unknown table")
    # sanitize device_id (ephemeral)
    device_id = bleach.clean(payload.device_id or "", strip=True)[:64] or str(uuid.uuid4())
    # Create a new short-lived device table session
    sess_id = str(uuid.uuid4())
    ts = TableSession(id=sess_id, table_id=table.id)
    session.add(ts)
    await session.commit()
    cap = issue_session_cap(table_id=table.id, session_id=sess_id, ttl_seconds=600)
    return SessionStartOut(table_id=table.id, session_id=sess_id, session_cap=cap, table_name=table.name)
