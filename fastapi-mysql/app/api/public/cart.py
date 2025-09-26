import uuid, json, bleach
from fastapi import APIRouter, Header, HTTPException
from app.db import fetch_one, fetch_all, execute
from app.redis_ext import redis, channel_for_table, channel_staff
from app.tokens import extract_opaque, verify_session_cap
from app.schemas.public import AddCartItemIn, CartOut, CartItemOut, SubmitOut
from app.services.idempotency import idempotent

router = APIRouter(prefix="/api/public", tags=["public"])

def _sanitize(s: str | None) -> str | None:
    if not s:
        return None
    return bleach.clean(s, strip=True)[:280]

def _json_loadmaybe(v):
    if v is None:
        return {}
    if isinstance(v, (dict, list)):
        return v
    try:
        return json.loads(v)
    except Exception:
        return {}

async def _cart_for_table(table_id: int) -> dict:
    row = await fetch_one(
        "SELECT id FROM carts WHERE table_id=%s ORDER BY created_at DESC LIMIT 1",
        (table_id,),
    )
    if row:
        return {"id": row["id"]}
    cart_id = str(uuid.uuid4())
    await execute("INSERT INTO carts (id, table_id) VALUES (%s, %s)", (cart_id, table_id))
    return {"id": cart_id}

async def _broadcast(table_id: int, event: str, payload: dict):
    msg = json.dumps({"event": event, "data": payload})
    await redis.publish(channel_for_table(table_id), msg)
    await redis.publish(channel_staff(), msg)

@router.get("/cart", response_model=CartOut)
async def get_cart(table_token: str, session_cap: str):
    opaque = extract_opaque(table_token)
    cap = verify_session_cap(session_cap)
    if not opaque or not cap:
        raise HTTPException(401, "Invalid token")
    table = await fetch_one("SELECT id FROM tables WHERE opaque_uid=%s LIMIT 1", (opaque,))
    if not table or table["id"] != cap.get("tid"):
        raise HTTPException(403, "Token mismatch")
    cart = await _cart_for_table(table["id"])
    items = await fetch_all(
        """
        SELECT id, item_id, quantity, options, notes, added_by, state
        FROM cart_items
        WHERE cart_id=%s
        ORDER BY created_at
        """,
        (cart["id"],),
    )
    out = [
        CartItemOut(
            id=i["id"],
            client_uid=None,
            item_id=i["item_id"],
            title=str(i["item_id"]),
            quantity=i["quantity"],
            options=_json_loadmaybe(i.get("options")),
            notes=i.get("notes"),
            added_by=i.get("added_by"),
            state=i.get("state"),
        ).model_dump()
        for i in items
    ]
    return CartOut(cart_id=cart["id"], items=out)

@router.post("/cart/items", response_model=CartOut)
async def add_item(payload: AddCartItemIn, table_token: str, session_cap: str, anon_user_id: str, idem_key: str = Header(...)):
    opaque = extract_opaque(table_token)
    cap = verify_session_cap(session_cap)
    if not opaque or not cap:
        raise HTTPException(401, "Invalid token")
    if not anon_user_id:
        raise HTTPException(400, "missing anon_user_id")
    table = await fetch_one("SELECT id FROM tables WHERE opaque_uid=%s LIMIT 1", (opaque,))
    if not table or table["id"] != cap.get("tid"):
        raise HTTPException(403, "Token mismatch")

    async def compute():
        cart = await _cart_for_table(table["id"])
        lock_key = f"lock:cart:{cart['id']}"
        await redis.setnx(lock_key, "1")
        await redis.expire(lock_key, 5)
        try:
            item = await fetch_one(
                "SELECT id, active, is_86 FROM items WHERE id=%s LIMIT 1",
                (payload.item_id,),
            )
            if not item or not item["active"] or item["is_86"]:
                raise HTTPException(400, "Item unavailable")
            ci_id = str(uuid.uuid4())
            await execute(
                """
                INSERT INTO cart_items
                  (id, cart_id, item_id, quantity, options, notes, added_by, state)
                VALUES
                  (%s, %s, %s, %s, %s, %s, %s, 'in_cart')
                """,
                (
                    ci_id,
                    cart["id"],
                    payload.item_id,
                    max(1, payload.quantity or 1),
                    json.dumps(payload.options or {}),
                    _sanitize(payload.notes),
                    anon_user_id,
                ),
            )
            await _broadcast(table["id"], "cart_updated", {"cart_id": cart["id"]})
            items = await fetch_all(
                """
                SELECT id, item_id, quantity, options, notes, added_by, state
                FROM cart_items WHERE cart_id=%s ORDER BY created_at
                """,
                (cart["id"],),
            )
            return {
                "cart_id": cart["id"],
                "items": [
                    {
                        "id": i["id"],
                        "client_uid": None,
                        "item_id": i["item_id"],
                        "title": str(i["item_id"]),
                        "quantity": i["quantity"],
                        "options": _json_loadmaybe(i.get("options")),
                        "notes": i.get("notes"),
                        "added_by": i.get("added_by"),
                        "state": i.get("state"),
                    }
                    for i in items
                ],
            }
        finally:
            await redis.delete(lock_key)

    result, _reused = await idempotent(f"{idem_key}:{cap['sid']}", compute=compute)
    return result

@router.post("/cart/submit", response_model=SubmitOut)
async def submit_cart(table_token: str, session_cap: str, anon_user_id: str, idem_key: str = Header(...)):
    opaque = extract_opaque(table_token)
    cap = verify_session_cap(session_cap)
    if not opaque or not cap:
        raise HTTPException(401, "Invalid token")
    table = await fetch_one("SELECT id FROM tables WHERE opaque_uid=%s LIMIT 1", (opaque,))
    if not table or table["id"] != cap.get("tid"):
        raise HTTPException(403, "Token mismatch")

    async def compute():
        cart = await _cart_for_table(table["id"])
        items = await fetch_all(
            """
            SELECT id, item_id, quantity, options, notes
            FROM cart_items
            WHERE cart_id=%s AND state='in_cart'
            """,
            (cart["id"],),
        )
        if not items:
            raise HTTPException(400, "Cart empty")
        from app.services.pricing import compute_totals
        line_items = [{"quantity": i["quantity"], "price_each": "10.00"} for i in items]
        totals = compute_totals(line_items, tax_inclusive=False)
        order_id = str(uuid.uuid4())
        await execute(
            """
            INSERT INTO orders
              (id, table_id, state, subtotal, tax, service_charge, discount_total, total)
            VALUES
              (%s, %s, 'submitted', %s, %s, 0, 0, %s)
            """,
            (order_id, table["id"], totals["subtotal"], totals["tax"], totals["total"]),
        )
        for i in items:
            await execute(
                """
                INSERT INTO order_items
                  (id, order_id, item_id, title_snapshot, quantity, price_each, options, notes, state)
                VALUES
                  (%s, %s, %s, %s, %s, %s, %s, %s, 'submitted')
                """,
                (
                    str(uuid.uuid4()),
                    order_id,
                    i["item_id"],
                    str(i["item_id"]),
                    i["quantity"],
                    "10.00",
                    json.dumps(i.get("options") or {}),
                    i.get("notes"),
                ),
            )
        await execute("UPDATE cart_items SET state='submitted' WHERE cart_id=%s AND state='in_cart'", (cart["id"],))
        await execute(
            "INSERT INTO order_events (order_id, order_item_id, actor_user_id, actor_table_user, action, reason) "
            "VALUES (%s, NULL, NULL, %s, 'submitted', NULL)",
            (order_id, anon_user_id),
        )
        await _broadcast(table["id"], "order_submitted", {"order_id": order_id})
        return {"order_id": order_id, "state": "submitted"}

    result, _reused = await idempotent(f"submit:{idem_key}:{cap['sid']}", compute=compute)
    return result
