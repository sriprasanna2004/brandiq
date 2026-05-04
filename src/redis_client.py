"""Shared Redis client that handles Railway's SSL Redis correctly."""
import os
import ssl
import redis as redis_lib

def get_redis():
    url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    if url.startswith("rediss://"):
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
