import os
import redis


REDIS_URL = os.getenv("REDIS_URL")

if REDIS_URL:
    r = redis.Redis.from_url(
        REDIS_URL,
        decode_responses=True,
        socket_connect_timeout=1,
    )
else:
    r = redis.Redis(
        host=os.getenv("REDIS_HOST", "localhost"),
        port=int(os.getenv("REDIS_PORT", "6379")),
        decode_responses=True,
        socket_connect_timeout=1,
    )

TODOS_CACHE_KEY = "todos:all"


def cache_get(key):
    try:
        return r.get(key)
    except redis.RedisError:
        return None


def cache_set(key, value, ttl=30):
    try:
        r.set(key, value, ex=ttl)
    except redis.RedisError:
        return None


def cache_clear(key):
    try:
        r.delete(key)
    except redis.RedisError:
        return None
    return None