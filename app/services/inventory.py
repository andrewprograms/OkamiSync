from app.db import AsyncSession

# Placeholder hooks for 86 status, quantity deductions, etc.
async def is_item_available(session: AsyncSession, item_id: str) -> bool:
    from sqlalchemy import select
    from app.models.menu import Item
    res = await session.execute(select(Item).where(Item.id==item_id))
    item = res.scalar_one_or_none()
    if not item or not item.active or item.is_86:
        return False
    return True
