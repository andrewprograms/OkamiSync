from fastapi import APIRouter, Depends, HTTPException
from app.auth.deps import staff_required
from app.db import fetch_all, fetch_one, execute
from app.schemas.staff import ActionIn
from app.redis_ext import redis, channel_for_table, channel_staff
import json

router = APIRouter(prefix="/api/staff", tags=["staff"])

def _to_row(o):
    return {
        "id": o["id"],
        "table_id": o["table_id"],
        "state": o["state"],
        "items": [],
        "created_at": (o.get("created_at") or "").isoformat() if o.get("created_at") else "",
        "elapsed_s": 0,
    }

@router.get("/orders")
async def list_orders(state: str | None = None, user=Depends(staff_required)):
    if state:
        rows = await fetch_all(
            "SELECT id, table_id, state, created_at FROM orders WHERE state=%s ORDER BY created_at DESC",
            (state,),
        )
    else:
        rows = await fetch_all(
            "SELECT id, table_id, state, created_at FROM orders ORDER BY created_at DESC"
        )
    return {"orders": [_to_row(r) for r in rows]}

async def _broadcast_state(table_id: int, order_id: str, new_state: str):
    msg = json.dumps({"event": "order_state_changed", "data": {"order_id": order_id, "state": new_state}})
    await redis.publish(channel_for_table(table_id), msg)
    await redis.publish(channel_staff(), msg)

async def _update_state(order_id: str, new_state: str, user):
    o = await fetch_one("SELECT id, table_id FROM orders WHERE id=%s LIMIT 1", (order_id,))
    if not o:
        raise HTTPException(404, "order not found")
    await execute("UPDATE orders SET state=%s WHERE id=%s", (new_state, order_id))
    await execute(
        "INSERT INTO order_events (order_id, order_item_id, actor_user_id, actor_table_user, action, reason) "
        "VALUES (%s, NULL, %s, NULL, %s, NULL)",
        (order_id, user["uid"], new_state),
    )
    await _broadcast_state(o["table_id"], order_id, new_state)
    return {"ok": True, "state": new_state}

@router.post("/orders/{order_id}/accept")
async def accept_order(order_id: str, user=Depends(staff_required)):
    return await _update_state(order_id, "accepted", user)

@router.post("/orders/{order_id}/ready")
async def ready_order(order_id: str, user=Depends(staff_required)):
    return await _update_state(order_id, "ready", user)

@router.post("/orders/{order_id}/served")
async def served_order(order_id: str, user=Depends(staff_required)):
    return await _update_state(order_id, "served", user)

@router.post("/orders/{order_id}/void")
async def void_order(order_id: str, payload: ActionIn, user=Depends(staff_required)):
    o = await fetch_one("SELECT id, table_id FROM orders WHERE id=%s LIMIT 1", (order_id,))
    if not o:
        raise HTTPException(404, "order not found")
    await execute("UPDATE orders SET state='voided' WHERE id=%s", (order_id,))
    await execute(
        "INSERT INTO order_events (order_id, order_item_id, actor_user_id, actor_table_user, action, reason) "
        "VALUES (%s, NULL, %s, NULL, 'voided', %s)",
        (order_id, user["uid"], (payload.reason or "")[:255]),
    )
    await _broadcast_state(o["table_id"], order_id, "voided")
    return {"ok": True, "state": "voided"}
