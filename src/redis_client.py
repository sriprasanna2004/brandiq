"""Shared Redis client — handles Railway rediss:// correctly."""
import os
import ssl
import redis as redis_lib

def get_redis():
    url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    if url.startswith("rediss://"):
        # Use ssl_context with CERT_NONE — works in redis-py 4.x
        ssl_ctx = ssl.create_default_context()
        ssl_ctx.check_hostname = False
        ssl_ctx.verify_mode = ssl.CERT_NONE
        return redis_lib.from_url(url, decode_responses=True, ssl_context=ssl_ctx)
    return redis_lib.from_url(url, decode_responses=True)

try:
    _redis = get_redis()
    _redis.ping()
except Exception:
    _redis = None

def redis_client():
    return _redis
