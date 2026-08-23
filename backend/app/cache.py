from __future__ import annotations

import json
import os
from typing import Any
from urllib.parse import quote

import redis


class EvaluationCache:
    """Redis-backed evaluation cache that fails open when Redis is unavailable."""

    _global_version_key = "evaluation:version:all"

    def __init__(self) -> None:
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.ttl = int(os.getenv("EVALUATION_CACHE_TTL", "60"))
        self.client = redis.Redis.from_url(
            self.redis_url,
            decode_responses=True,
            socket_connect_timeout=0.2,
            socket_timeout=0.2,
        )

    @staticmethod
    def _safe_part(value: str | None) -> str:
        return quote(value or "", safe="")

    def _flag_version_key(self, flag_key: str) -> str:
        return f"evaluation:version:flag:{self._safe_part(flag_key)}"

    def _version(self, key: str) -> int:
        value = self.client.get(key)
        return int(value or 0)

    def cache_key(self, flag_key: str, environment: str, user_id: str, group: str | None = None) -> str:
        global_version = self._version(self._global_version_key)
        flag_version = self._version(self._flag_version_key(flag_key))
        parts = [
            "evaluation",
            self._safe_part(flag_key),
            f"v{global_version}",
            f"f{flag_version}",
            self._safe_part(environment),
            self._safe_part(user_id),
            self._safe_part(group),
        ]
        return ":".join(parts)

    def get(self, flag_key: str, environment: str, user_id: str, group: str | None = None) -> dict[str, Any] | None:
        try:
            cached = self.client.get(self.cache_key(flag_key, environment, user_id, group))
            return json.loads(cached) if cached else None
        except (redis.RedisError, OSError, ValueError, TypeError, json.JSONDecodeError):
            return None

    def set(
        self,
        flag_key: str,
        environment: str,
        user_id: str,
        group: str | None,
        result: dict[str, Any],
    ) -> None:
        try:
            self.client.setex(
                self.cache_key(flag_key, environment, user_id, group),
                self.ttl,
                json.dumps(result),
            )
        except (redis.RedisError, OSError, TypeError, ValueError):
            return

    def invalidate_flag(self, flag_key: str) -> None:
        try:
            self.client.incr(self._flag_version_key(flag_key))
        except (redis.RedisError, OSError):
            return

    def invalidate_all(self) -> None:
        try:
            self.client.incr(self._global_version_key)
        except (redis.RedisError, OSError):
            return


evaluation_cache = EvaluationCache()


def invalidate_flag_evaluation_cache(flag_key: str) -> None:
    evaluation_cache.invalidate_flag(flag_key)


def invalidate_all_evaluation_cache() -> None:
    evaluation_cache.invalidate_all()