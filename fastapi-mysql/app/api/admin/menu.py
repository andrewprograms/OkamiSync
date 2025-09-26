from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
import uuid, json
from app.auth.deps import admin_required
from app.db import execute, fetch_one
from app.services.images import process_and_save
from app.services.media_proxy import gen_signed_url

router = APIRouter(prefix="/api/admin", tags=["admin"])

@router.post("/categories")
async def create_category(data: dict, user=Depends(admin_required)):
    cid = str(uuid.uuid4())
    await execute(
        """
        INSERT INTO categories (id, parent_id, title_i18n, description_i18n, sort_order, active)
        VALUES (%s, %s, %s, %s, %s, 1)
        """,
        (
            cid,
            data.get("parent_id"),
            json.dumps(data.get("title_i18n") or {}),
            json.dumps(data.get("description_i18n") or {}),
            int(data.get("sort_order") or 0),
        ),
    )
    return {"id": cid}

@router.post("/items")
async def create_item(data: dict, user=Depends(admin_required)):
    iid = str(uuid.uuid4())
    await execute(
        """
        INSERT INTO items (id, category_id, title_i18n, description_i18n, price, tax_class,
                           dietary_tags, availability, sort_order, image_path, is_86, active)
        VALUES (%s, %s, %s, %s, %s, %s,
                %s, NULL, %s, %s, 0, 1)
        """,
        (
            iid,
            data.get("category_id"),
            json.dumps(data.get("title_i18n") or {}),
            json.dumps(data.get("description_i18n") or {}),
            str(data.get("price", "0.00")),
            data.get("tax_class") or "standard",
            json.dumps(data.get("dietary_tags") or []),
            int(data.get("sort_order") or 0),
            data.get("image_path"),
        ),
    )
    return {"id": iid}

@router.post("/media")
async def upload_image(file: UploadFile = File(...), user=Depends(admin_required)):
    data = process_and_save(file.file, file.filename)
    path = data.get("512x512") or list(data.values())[0]
    url = gen_signed_url(path)
    return {"variants": data, "url": url}
