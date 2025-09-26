import json, asyncio, hashlib
from app.redis_ext import redis

IDEMP_PREFIX = "idem:"

async def idempotent(key: str, ttl: int = 60*60, compute=None):
    cache_key = IDEMP_PREFIX + hashlib.sha256(key.encode()).hexdigest()
    # Use SETNX to reserve
    ok = await redis.setnx(cache_key + ":lock", "1")
    if ok:
        await redis.expire(cache_key + ":lock", 15)  # short lock
        result = await compute()
        await redis.set(cache_key, json.dumps(result), ex=ttl)
        await redis.delete(cache_key + ":lock")
        return result, False
    # If existing result
    cached = await redis.get(cache_key)
    if cached:
        return json.loads(cached), True
    # Busy-wait briefly
    for _ in range(10):
        await asyncio.sleep(0.2)
        cached = await redis.get(cache_key)
        if cached:
            return json.loads(cached), True
    # Fallback compute
    result = await compute()
    await redis.set(cache_key, json.dumps(result), ex=ttl)
    return result, False
