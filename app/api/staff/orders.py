from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_async_session
from app.auth.deps import staff_required
from app.models.orders import Order, OrderEvent
from app.schemas.staff import ActionIn
from app.redis_ext import redis, channel_for_table, channel_staff
import json

router = APIRouter(prefix="/api/staff", tags=["staff"])

def _to_row(o: Order):
    return {
        "id": o.id, "table_id": o.table_id, "state": o.state,
        "items": [], "created_at": o.created_at.isoformat() if o.created_at else "",
        "elapsed_s": 0
    }

@router.get("/orders")
async def list_orders(state: str | None = None, session: AsyncSession = Depends(get_async_session), user=Depends(staff_required)):
    q = select(Order)
    if state:
        q = q.where(Order.state==state)
    orders = (await session.execute(q.order_by(Order.created_at.desc()))).scalars().all()
    out = [_to_row(o) for o in orders]
    return {"orders": out}

async def _broadcast_state(table_id: int, order_id: str, new_state: str):
    msg = json.dumps({"event": "order_state_changed", "data": {"order_id": order_id, "state": new_state}})
    await redis.publish(channel_for_table(table_id), msg)
    await redis.publish(channel_staff(), msg)

@router.post("/orders/{order_id}/accept")
async def accept_order(order_id: str, session: AsyncSession = Depends(get_async_session), user=Depends(staff_required)):
    res = await session.execute(select(Order).where(Order.id==order_id))
    o = res.scalar_one_or_none()
    if not o: raise HTTPException(404, "order not found")
    o.state = "accepted"
    session.add(OrderEvent(order_id=o.id, action="accepted", actor_user_id=user["uid"]))
    await session.commit()
    await _broadcast_state(o.table_id, o.id, o.state)
    return {"ok": True, "state": o.state}

@router.post("/orders/{order_id}/ready")
async def ready_order(order_id: str, session: AsyncSession = Depends(get_async_session), user=Depends(staff_required)):
    res = await session.execute(select(Order).where(Order.id==order_id))
    o = res.scalar_one_or_none()
    if not o: raise HTTPException(404, "order not found")
    o.state = "ready"
    session.add(OrderEvent(order_id=o.id, action="ready", actor_user_id=user["uid"]))
    await session.commit()
    await _broadcast_state(o.table_id, o.id, o.state)
    return {"ok": True, "state": o.state}

@router.post("/orders/{order_id}/served")
async def served_order(order_id: str, session: AsyncSession = Depends(get_async_session), user=Depends(staff_required)):
    res = await session.execute(select(Order).where(Order.id==order_id))
    o = res.scalar_one_or_none()
    if not o: raise HTTPException(404, "order not found")
    o.state = "served"
    session.add(OrderEvent(order_id=o.id, action="served", actor_user_id=user["uid"]))
    await session.commit()
    await _broadcast_state(o.table_id, o.id, o.state)
    return {"ok": True, "state": o.state}

@router.post("/orders/{order_id}/void")
async def void_order(order_id: str, payload: ActionIn, session: AsyncSession = Depends(get_async_session), user=Depends(staff_required)):
    res = await session.execute(select(Order).where(Order.id==order_id))
    o = res.scalar_one_or_none()
    if not o: raise HTTPException(404, "order not found")
    o.state = "voided"
    session.add(OrderEvent(order_id=o.id, action="voided", actor_user_id=user["uid"], reason=(payload.reason or "")[:255]))
    await session.commit()
    await _broadcast_state(o.table_id, o.id, o.state)
    return {"ok": True, "state": o.state}
