import os
from contextlib import contextmanager
from queue import Queue
import anyio
import pymysql
from pymysql.cursors import DictCursor
from app.config import settings

_POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "10"))
_pool: "Queue[pymysql.connections.Connection]" = Queue(maxsize=_POOL_SIZE)

def _make_conn():
    return pymysql.connect(
        host=settings.mysql_host,
        port=settings.mysql_port,
        user=settings.mysql_user,
        password=settings.mysql_password,
        database=settings.mysql_db,
        autocommit=False,
        charset="utf8mb4",
        cursorclass=DictCursor,
        read_timeout=10,
        write_timeout=10,
    )

@contextmanager
def get_conn():
    try:
        conn = _pool.get_nowait()
    except Exception:
        conn = _make_conn()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        try:
            _pool.put_nowait(conn)
        except Exception:
            try:
                conn.close()
            except Exception:
                pass

def execute_sync(sql: str, params=None) -> int:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params or ())
            return cur.rowcount

def executemany_sync(sql: str, seq) -> int:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.executemany(sql, seq)
            return cur.rowcount

def fetch_one_sync(sql: str, params=None):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params or ())
            return cur.fetchone()

def fetch_all_sync(sql: str, params=None):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params or ())
            return cur.fetchall()

async def execute(sql: str, params=None) -> int:
    return await anyio.to_thread.run_sync(execute_sync, sql, params)

async def executemany(sql: str, seq) -> int:
    return await anyio.to_thread.run_sync(executemany_sync, sql, seq)

async def fetch_one(sql: str, params=None):
    return await anyio.to_thread.run_sync(fetch_one_sync, sql, params)

async def fetch_all(sql: str, params=None):
    return await anyio.to_thread.run_sync(fetch_all_sync, sql, params)
