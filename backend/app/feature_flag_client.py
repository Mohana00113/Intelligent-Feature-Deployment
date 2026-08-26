"""Small, dependency-free client for consuming feature flags from the API."""

from __future__ import annotations

import json
import logging
import threading
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen

logger = logging.getLogger(__name__)


class FeatureFlagClient:
    """Keep a periodically refreshed, last-known-good snapshot of feature flags."""

    def __init__(self, base_url: str, refresh_interval: float = 30, timeout: float = 5) -> None:
        if refresh_interval <= 0:
            raise ValueError("refresh_interval must be greater than zero")
        self.base_url = base_url.rstrip("/")
        self.refresh_interval = refresh_interval
        self.timeout = timeout
        self._flags: dict[str, dict[str, Any]] = {}
        self._lock = threading.RLock()
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def _fetch_flags(self) -> dict[str, dict[str, Any]]:
        request = Request(f"{self.base_url}/flags", headers={"Accept": "application/json"})
        with urlopen(request, timeout=self.timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
        if not isinstance(payload, list):
            raise ValueError("Feature flag API returned an invalid payload")
        return {
            item["key"]: item
            for item in payload
            if isinstance(item, dict) and isinstance(item.get("key"), str)
        }

    def refresh(self) -> bool:
        """Refresh the snapshot, returning false while retaining stale data on failure."""

        try:
            flags = self._fetch_flags()
            if not isinstance(flags, dict):
                raise ValueError("Feature flag API returned an invalid snapshot")
        except (OSError, URLError, ValueError, json.JSONDecodeError) as exc:
            logger.warning("Unable to refresh feature flags: %s", exc)
            return False
        with self._lock:
            self._flags = flags
        return True

    def _refresh_loop(self) -> None:
        while not self._stop_event.wait(self.refresh_interval):
            self.refresh()

    def start(self) -> None:
        """Load the initial snapshot and start periodic refreshes."""

        self.refresh()
        with self._lock:
            if self._thread and self._thread.is_alive():
                return
            self._stop_event.clear()
            self._thread = threading.Thread(target=self._refresh_loop, name="feature-flag-refresh", daemon=True)
            self._thread.start()

    def stop(self) -> None:
        """Stop periodic refreshes and wait briefly for the worker to exit."""

        self._stop_event.set()
        thread = self._thread
        if thread and thread is not threading.current_thread():
            thread.join(timeout=max(self.refresh_interval, 1))
        self._thread = None

    close = stop

    def get_flag(self, key: str) -> dict[str, Any] | None:
        with self._lock:
            flag = self._flags.get(key)
            return dict(flag) if flag is not None else None

    def is_enabled(self, key: str) -> bool:
        flag = self.get_flag(key)
        return bool(flag and flag.get("enabled", False))

    def __enter__(self) -> "FeatureFlagClient":
        self.start()
        return self

    def __exit__(self, *_: object) -> None:
        self.stop()