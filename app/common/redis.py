from __future__ import annotations

import contextlib
import uuid
from typing import AsyncIterator

import redis.asyncio as redis

from app.common.config import settings


_redis: redis.Redis | None = None


def get_redis() -> redis.Redis:
    global _redis
    if _redis is None:
        _redis = redis.from_url(settings.redis_url, decode_responses=True)
    return _redis


@contextlib.asynccontextmanager
async def user_lock(user_id: int, ttl: int = 10) -> AsyncIterator[bool]:
    client = get_redis()
    lock_key = f"lock:user:{user_id}"
    token = str(uuid.uuid4())
    acquired = await client.set(lock_key, token, nx=True, ex=ttl)
    try:
        yield bool(acquired)
    finally:
        value = await client.get(lock_key)
        if value == token:
            await client.delete(lock_key)
