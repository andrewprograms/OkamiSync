from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_async_session
from app.schemas.common import CategoryOut, ItemOut
from app.models.menu import Category, Item
from app.tokens import extract_opaque
from app.models.tables import Table

router = APIRouter(prefix="/api/public", tags=["public"])

@router.get("/menu", response_model=dict)
async def get_menu(table_token: str = Query(...), session: AsyncSession = Depends(get_async_session)):
    # Accept signed token, JSON bootstrap, or raw opaque; just ensure table exists.
    opaque = extract_opaque(table_token)
    if not opaque:
        raise HTTPException(400, "Invalid table token")
    res = await session.execute(select(Table).where(Table.opaque_uid == opaque))
    if not res.scalar_one_or_none():
        raise HTTPException(404, "Unknown table")

    cats = (await session.execute(select(Category).where(Category.active==True).order_by(Category.sort_order))).scalars().all()
    items = (await session.execute(select(Item).where(Item.active==True).order_by(Item.sort_order))).scalars().all()

    def url_for(item):
        return f"/media/{item.image_path}" if item.image_path else None

    return {
        "categories": [CategoryOut(
            id=c.id, title_i18n=c.title_i18n, description_i18n=c.description_i18n, sort_order=c.sort_order
        ).model_dump() for c in cats],
        "items": [ItemOut(
            id=i.id, category_id=i.category_id, title_i18n=i.title_i18n,
            description_i18n=i.description_i18n, price=str(i.price), tax_class=i.tax_class,
            dietary_tags=i.dietary_tags, sort_order=i.sort_order, image_url=url_for(i), is_86=i.is_86
        ).model_dump() for i in items]
    }
