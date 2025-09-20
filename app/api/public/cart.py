import uuid, json, bleach
from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_async_session
from app.models.orders import Cart, CartItem, Order, OrderItem, OrderEvent
from app.models.menu import Item
from app.models.tables import Table
from app.services.inventory import is_item_available
from app.services.idempotency import idempotent
from app.redis_ext import redis, channel_for_table, channel_staff
from app.tokens import extract_opaque, verify_session_cap
from app.schemas.public import AddCartItemIn, CartOut, CartItemOut, SubmitOut

router = APIRouter(prefix="/api/public", tags=["public"])

def _sanitize(s: str | None) -> str | None:
    if not s:
        return None
    return bleach.clean(s, strip=True)[:280]

async def _cart_for_table(session: AsyncSession, table_id: int) -> Cart:
    res = await session.execute(select(Cart).where(Cart.table_id==table_id))
    cart = res.scalar_one_or_none()
    if not cart:
        cart = Cart(id=str(uuid.uuid4()), table_id=table_id)
        session.add(cart)
        await session.commit()
    return cart

async def _broadcast(table_id: int, event: str, payload: dict):
    msg = json.dumps({"event": event, "data": payload})
    await redis.publish(channel_for_table(table_id), msg)
    await redis.publish(channel_staff(), msg)  # staff receive all

@router.get("/cart", response_model=CartOut)
async def get_cart(table_token: str, session_cap: str, session: AsyncSession = Depends(get_async_session)):
    opaque = extract_opaque(table_token)
    cap = verify_session_cap(session_cap)
    if not opaque or not cap:
        raise HTTPException(401, "Invalid token")
    res = await session.execute(select(Table).where(Table.opaque_uid==opaque))
    table = res.scalar_one_or_none()
    if not table or table.id != cap.get("tid"):
        raise HTTPException(403, "Token mismatch")
    cart = await _cart_for_table(session, table.id)
    items = (await session.execute(select(CartItem).where(CartItem.cart_id==cart.id))).scalars().all()
    out = [CartItemOut(
        id=i.id, client_uid=None, item_id=i.item_id, title=str(i.item_id), quantity=i.quantity,
        options=i.options, notes=i.notes, added_by=i.added_by, state=i.state
    ).model_dump() for i in items]
    return CartOut(cart_id=cart.id, items=out)

@router.post("/cart/items", response_model=CartOut)
async def add_item(
    payload: AddCartItemIn,
    table_token: str,
    session_cap: str,
    anon_user_id: str,
    idem_key: str = Header(...),
    session: AsyncSession = Depends(get_async_session)
):
    opaque = extract_opaque(table_token)
    cap = verify_session_cap(session_cap)
    if not opaque or not cap:
        raise HTTPException(401, "Invalid token")
    if not anon_user_id:
        raise HTTPException(400, "missing anon_user_id")

    res = await session.execute(select(Table).where(Table.opaque_uid==opaque))
    table = res.scalar_one_or_none()
    if not table or table.id != cap.get("tid"):
        raise HTTPException(403, "Token mismatch")

    async def compute():
        cart = await _cart_for_table(session, table.id)
        lock_key = f"lock:cart:{cart.id}"
        await redis.setnx(lock_key, "1")
        await redis.expire(lock_key, 5)

        # Validate item
        res2 = await session.execute(select(Item).where(Item.id == payload.item_id))
        item = res2.scalar_one_or_none()
        if not item or not await is_item_available(session, payload.item_id):
            await redis.delete(lock_key)
            raise HTTPException(400, "Item unavailable")

        ci = CartItem(
            id=str(uuid.uuid4()),
            cart_id=cart.id,
            item_id=payload.item_id,
            quantity=max(1, payload.quantity or 1),
            options=payload.options or {},
            notes=_sanitize(payload.notes),
            added_by=anon_user_id,
            state="in_cart"
        )
        session.add(ci)
        await session.commit()
        await redis.delete(lock_key)
        await _broadcast(table.id, "cart_updated", {"cart_id": cart.id})

        # Return updated cart
        items = (await session.execute(select(CartItem).where(CartItem.cart_id==cart.id))).scalars().all()
        return {"cart_id": cart.id, "items": [{
            "id": i.id, "client_uid": None, "item_id": i.item_id, "title": str(i.item_id), "quantity": i.quantity,
            "options": i.options, "notes": i.notes, "added_by": i.added_by, "state": i.state
        } for i in items]}

    result, reused = await idempotent(f"{idem_key}:{cap['sid']}", compute=compute)
    return result

@router.post("/cart/submit", response_model=SubmitOut)
async def submit_cart(
    table_token: str,
    session_cap: str,
    anon_user_id: str,
    idem_key: str = Header(...),
    session: AsyncSession = Depends(get_async_session)
):
    opaque = extract_opaque(table_token)
    cap = verify_session_cap(session_cap)
    if not opaque or not cap:
        raise HTTPException(401, "Invalid token")

    res = await session.execute(select(Table).where(Table.opaque_uid==opaque))
    table = res.scalar_one_or_none()
    if not table or table.id != cap.get("tid"):
        raise HTTPException(403, "Token mismatch")

    async def compute():
        cart = await _cart_for_table(session, table.id)
        items = (await session.execute(
            select(CartItem).where(CartItem.cart_id==cart.id, CartItem.state=="in_cart")
        )).scalars().all()
        if not items:
            raise HTTPException(400, "Cart empty")

        # Create order snapshot
        order_id = str(uuid.uuid4())
        from app.services.pricing import compute_totals
        # NOTE: for demo pricing we use a flat "10.00" per item; replace with item.price in a fuller impl.
        line_items = [{"quantity": i.quantity, "price_each": "10.00"} for i in items]
        totals = compute_totals(line_items, tax_inclusive=False)

        order = Order(id=order_id, table_id=table.id,
                      subtotal=totals["subtotal"], tax=totals["tax"], total=totals["total"])
        session.add(order)
        for i in items:
            oi = OrderItem(id=str(uuid.uuid4()), order_id=order_id, item_id=i.item_id,
                           title_snapshot=str(i.item_id), quantity=i.quantity,
                           price_each="10.00", options=i.options, notes=i.notes, state="submitted")
            session.add(oi)
            i.state = "submitted"

        session.add(OrderEvent(order_id=order_id, order_item_id=None,
                               actor_table_user=anon_user_id, action="submitted", reason=None))
        await session.commit()
        await _broadcast(table.id, "order_submitted", {"order_id": order_id})
        return {"order_id": order_id, "state": "submitted"}

    result, reused = await idempotent(f"submit:{idem_key}:{cap['sid']}", compute=compute)
    return result
