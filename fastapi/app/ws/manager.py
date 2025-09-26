import asyncio, json
from typing import Dict, Set
from app.redis_ext import redis, channel_for_table, channel_staff
from starlette.websockets import WebSocket

class WSManager:
    def __init__(self):
        self.table_conns: Dict[int, Set[WebSocket]] = {}
        self.staff_conns: Set[WebSocket] = set()
        self.tasks: Dict[WebSocket, asyncio.Task] = {}

    async def connect_table(self, table_id: int, ws: WebSocket):
        conns = self.table_conns.setdefault(table_id, set())
        conns.add(ws)
        self.tasks[ws] = asyncio.create_task(self._listen_table(table_id, ws))

    async def disconnect_table(self, table_id: int, ws: WebSocket):
        self.table_conns.get(table_id, set()).discard(ws)
        t = self.tasks.pop(ws, None)
        if t:
            t.cancel()

    async def connect_staff(self, ws: WebSocket):
        self.staff_conns.add(ws)
        self.tasks[ws] = asyncio.create_task(self._listen_staff(ws))

    async def disconnect_staff(self, ws: WebSocket):
        self.staff_conns.discard(ws)
        t = self.tasks.pop(ws, None)
        if t:
            t.cancel()

    async def _listen_table(self, table_id: int, ws: WebSocket):
        pubsub = redis.pubsub()
        await pubsub.subscribe(channel_for_table(table_id))
        try:
            async for msg in pubsub.listen():
                if msg and msg.get("type") == "message":
                    await ws.send_text(msg["data"])
        finally:
            await pubsub.unsubscribe(channel_for_table(table_id))

    async def _listen_staff(self, ws: WebSocket):
        pubsub = redis.pubsub()
        await pubsub.subscribe(channel_staff())
        try:
            async for msg in pubsub.listen():
                if msg and msg.get("type") == "message":
                    await ws.send_text(msg["data"])
        finally:
            await pubsub.unsubscribe(channel_staff())

manager = WSManager()
