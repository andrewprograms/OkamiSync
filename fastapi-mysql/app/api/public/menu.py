from fastapi import APIRouter, HTTPException, Query
from app.db import fetch_one, fetch_all
from app.schemas.common import CategoryOut, ItemOut
from app.tokens import extract_opaque

router = APIRouter(prefix="/api/public", tags=["public"])

@router.get("/menu", response_model=dict)
async def get_menu(table_token: str = Query(...)):
    opaque = extract_opaque(table_token)
    if not opaque:
        raise HTTPException(400, "Invalid table token")

    table = await fetch_one("SELECT id FROM tables WHERE opaque_uid=%s LIMIT 1", (opaque,))
    if not table:
        raise HTTPException(404, "Unknown table")

    cats = await fetch_all(
        "SELECT id, title_i18n, description_i18n, sort_order FROM categories WHERE active=1 ORDER BY sort_order"
    )
    items = await fetch_all(
        """
        SELECT id, category_id, title_i18n, description_i18n, price, tax_class, dietary_tags,
               sort_order, image_path, is_86
        FROM items
        WHERE active=1
        ORDER BY sort_order
        """
    )

    def url_for(image_path):
        return f"/media/{image_path}" if image_path else None

    return {
        "categories": [
            CategoryOut(
                id=c["id"],
                title_i18n=c.get("title_i18n") or {},
                description_i18n=c.get("description_i18n") or {},
                sort_order=c["sort_order"],
            ).model_dump()
            for c in cats
        ],
        "items": [
            ItemOut(
                id=i["id"],
                category_id=i.get("category_id"),
                title_i18n=i.get("title_i18n") or {},
                description_i18n=i.get("description_i18n") or {},
                price=str(i["price"]),
                tax_class=i["tax_class"],
                dietary_tags=i.get("dietary_tags") or [],
                sort_order=i["sort_order"],
                image_url=url_for(i.get("image_path")),
                is_86=bool(i["is_86"]),
            ).model_dump()
            for i in items
        ],
    }
