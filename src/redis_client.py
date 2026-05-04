"""Shared Redis client — handles Railway rediss:// with redis-py 5.x."""
import os
import redis as redis_lib

def get_redis():
    url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    if url.startswith("rediss://"):
        # redis-py 5.x: ssl_cert_reqs as string "none"
        return redis_lib.from_url(url, decode_responses=True, ssl_cert_reqs="none")
    return redis_lib.from_url(url, decode_responses=True)

try:
    _redis = get_redis()
    _redis.ping()
except Exception:
    _redis = None

def redis_client():
    return _redis
