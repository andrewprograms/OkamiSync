from app.db import fetch_one

async def is_item_available(item_id: str) -> bool:
    row = await fetch_one("SELECT active, is_86 FROM items WHERE id=%s LIMIT 1", (item_id,))
    if not row:
        return False
    return bool(row["active"]) and not bool(row["is_86"])
