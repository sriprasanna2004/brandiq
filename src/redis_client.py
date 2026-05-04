"""Shared Redis client — handles Railway rediss:// with redis-py 5.x."""
import os
import redis as redis_lib

def get_redis():
    url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    if url.startswith("rediss://") and "ssl_cert_reqs" not in url:
        url = url + ("&" if "?" in url else "?") + "ssl_cert_reqs=none"
    return redis_lib.from_url(url, decode_responses=True)

try:
    _redis = get_redis()
    _redis.ping()
except Exception:
    _redis = None

def redis_client():
    return _redis
