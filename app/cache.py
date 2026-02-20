
import json
import time

REDIS_AVAILABLE = False
_redis = None

def _try_redis_connection():
    
    try:
        import redis
        client = redis.Redis(
            host="172.28.194.70", port=6379, db=0,
            socket_connect_timeout=0.05,
            socket_timeout=0.05,
            decode_responses=True
        )
        client.ping()
        return client
    except (ImportError, Exception):
        return None


REDIS_AVAILABLE = False
_redis = None


_mem: dict = {}
DEFAULT_TTL = 300


def _mem_get(key):
    entry = _mem.get(key)
    if entry is None:
        return None
    val, exp = entry
    if exp and time.time() > exp:
        del _mem[key]
        return None
    return val


def _mem_set(key, val, ttl=DEFAULT_TTL):
    _mem[key] = (val, time.time() + ttl if ttl else None)


def cache_get(key: str):
    if REDIS_AVAILABLE:
        raw = _redis.get(key)
        return json.loads(raw) if raw else None
    return _mem_get(key)


def cache_set(key: str, value, ttl: int = DEFAULT_TTL):
    if value is None:
        cache_delete(key)
        return
    if REDIS_AVAILABLE:
        _redis.setex(key, ttl, json.dumps(value))
    else:
        _mem_set(key, value, ttl)


def cache_delete(key: str):
    if REDIS_AVAILABLE:
        _redis.delete(key)
    else:
        _mem.pop(key, None)


def cache_delete_pattern(pattern: str):
    if REDIS_AVAILABLE:
        for key in _redis.scan_iter(pattern):
            _redis.delete(key)
    else:
        prefix = pattern.rstrip("*")
        for k in list(_mem.keys()):
            if k.startswith(prefix):
                del _mem[k]
