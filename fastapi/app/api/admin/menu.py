from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
from app.db import get_async_session
from app.auth.deps import admin_required
from app.models.menu import Category, Item
from app.services.images import process_and_save
from app.services.media_proxy import gen_signed_url

router = APIRouter(prefix="/api/admin", tags=["admin"])

@router.post("/categories")
async def create_category(data: dict, session: AsyncSession = Depends(get_async_session), user=Depends(admin_required)):
    c = Category(
        id=str(uuid.uuid4()),
        parent_id=data.get("parent_id"),
        title_i18n=data.get("title_i18n") or {},
        description_i18n=data.get("description_i18n") or {},
        sort_order=int(data.get("sort_order") or 0),
        active=True
    )
    session.add(c)
    await session.commit()
    return {"id": c.id}

@router.post("/items")
async def create_item(data: dict, session: AsyncSession = Depends(get_async_session), user=Depends(admin_required)):
    i = Item(
        id=str(uuid.uuid4()),
        category_id=data.get("category_id"),
        title_i18n=data.get("title_i18n") or {},
        description_i18n=data.get("description_i18n") or {},
        price=str(data.get("price", "0.00")),
        tax_class=data.get("tax_class") or "standard",
        dietary_tags=data.get("dietary_tags") or [],
        sort_order=int(data.get("sort_order") or 0),
        active=True
    )
    session.add(i)
    await session.commit()
    return {"id": i.id}

@router.post("/media")
async def upload_image(file: UploadFile = File(...), session: AsyncSession = Depends(get_async_session), user=Depends(admin_required)):
    data = process_and_save(file.file, file.filename)
    # Return the largest size signed URL
    path = data.get("512x512") or list(data.values())[0]
    url = gen_signed_url(path)
    return {"variants": data, "url": url}
