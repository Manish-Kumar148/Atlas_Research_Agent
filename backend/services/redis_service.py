import json
import logging
from typing import AsyncIterator

import redis.asyncio as aioredis

from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

_pool: aioredis.ConnectionPool | None = None


def get_redis() -> aioredis.Redis:
    global _pool
    if _pool is None:
        _pool = aioredis.ConnectionPool.from_url(
            settings.redis_url, decode_responses=True, max_connections=20
        )
    return aioredis.Redis(connection_pool=_pool)


def _session_key(session_id: str) -> str:
    return f"atlas:{session_id}:state"


def _events_key(session_id: str) -> str:
    return f"atlas:{session_id}:events"


async def set_session_state(session_id: str, state_dict: dict) -> None:
    r = get_redis()
    await r.setex(
        _session_key(session_id),
        settings.redis_ttl_seconds,
        json.dumps(state_dict, default=str),
    )


async def get_session_state(session_id: str) -> dict | None:
    r = get_redis()
    raw = await r.get(_session_key(session_id))
    if raw:
        return json.loads(raw)
    return None


async def publish_event(channel: str, event_dict: dict) -> None:
    r = get_redis()
    await r.publish(channel, json.dumps(event_dict, default=str))


async def subscribe(channel: str) -> AsyncIterator[dict]:
    r = get_redis()
    pubsub = r.pubsub()
    await pubsub.subscribe(channel)
    try:
        async for message in pubsub.listen():
            if message["type"] == "message":
                yield json.loads(message["data"])
    finally:
        await pubsub.unsubscribe(channel)
        await pubsub.aclose()


async def ping() -> bool:
    try:
        r = get_redis()
        return await r.ping()
    except Exception as e:
        logger.error(f"Redis ping failed: {e}")
        return False
