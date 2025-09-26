from redis.asyncio import Redis
from app.config import settings

redis = Redis.from_url(settings.redis_url, decode_responses=True)

async def publish(channel: str, message: dict):
    await redis.publish(channel, message)

def channel_for_table(table_id: int) -> str:
    return f"table:{table_id}"

def channel_staff() -> str:
    return "staff:all"
