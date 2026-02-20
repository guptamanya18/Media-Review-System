import redis
import json

try:
    r = redis.Redis(host='localhost', port=6379, decode_responses=True)
    r.ping()
except redis.ConnectionError:
    r = None  


def get_cache(key):
    if r:
        return r.get(key)
    return None


def set_cache(key, value, expire=300):
    if r:
        r.set(key, json.dumps(value), ex=expire)


def delete_cache(key):
    if r:
        r.delete(key)