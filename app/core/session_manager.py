import json
import redis
from app.core.config import settings
import uuid

# Global redis instance (should ideally use async redis, but keeping simple per requirements or using redis-py's asyncio support)
# Given requirements don't strictly mandate motor/async-redis, we will use a basic redis client or an in-memory fallback if redis isn't strictly available locally.
# We will provide an in-memory fallback for local dev if Redis isn't up, as requested: "Redis (or in-memory store with a documented upgrade path)"

class InMemoryFallbackRedis:
    def __init__(self):
        self.store = {}
    def get(self, key):
        return self.store.get(key)
    def setex(self, key, time, value):
        self.store[key] = value # naive implementation ignoring ttl
    def delete(self, key):
        self.store.pop(key, None)

try:
    redis_client = redis.Redis.from_url(settings.redis_url)
    redis_client.ping()
except (redis.ConnectionError, ValueError):
    print("WARNING: Redis not available. Falling back to in-memory store. Upgrade path: Set REDIS_URL in .env to a valid Redis instance.")
    redis_client = InMemoryFallbackRedis()

class SessionManager:
    @staticmethod
    def create_session() -> str:
        session_id = str(uuid.uuid4())
        session_data = {
            "status": "created",
            "used_nonces": [],
            "challenges": [],
            "challenge_index": 0,
            "accumulated_data": {
                 "frames_analyzed": 0,
                 "passive_scores": [],
                 "active_pass_count": 0,
                 "spoof_scores": []
            }
        }
        redis_client.setex(
            f"session:{session_id}",
            settings.session_timeout_seconds,
            json.dumps(session_data)
        )
        return session_id

    @staticmethod
    def get_session(session_id: str) -> dict:
        data = redis_client.get(f"session:{session_id}")
        if data:
            if isinstance(data, bytes):
                return json.loads(data.decode("utf-8"))
            return json.loads(data)
        return None

    @staticmethod
    def save_session(session_id: str, session_data: dict):
        redis_client.setex(
            f"session:{session_id}",
            settings.session_timeout_seconds,
            json.dumps(session_data)
        )

    @staticmethod
    def validate_nonce(session_id: str, session_data: dict, nonce: str) -> bool:
        if nonce in session_data.get("used_nonces", []):
            return False
        session_data.setdefault("used_nonces", []).append(nonce)
        return True
