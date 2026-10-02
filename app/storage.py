"""Persistent state storage and caching for Frigate-MCP.

Provides dual-tier persistence: Redis (when available) with seamless fallback
to local JSON disk storage in FRIGATE_MCP_DATA. Ensures settings and states
persist across CLI invocations and multi-worker deployments.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

from app.config import get_config

logger = logging.getLogger("frigate-mcp.storage")


class Storage:
    """Handles camera state persistence and caching."""

    def __init__(self, data_dir: Optional[str] = None, redis_url: Optional[str] = None):
        cfg = get_config()
        self.data_dir = Path(data_dir or cfg.data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.file_path = self.data_dir / "cameras_state.json"

        self.redis_url = redis_url or cfg.redis_url
        self._redis_client = None
        self._redis_available = False
        self._init_redis()

    def _init_redis(self) -> None:
        """Attempt to connect to Redis if available."""
        try:
            import redis

            client = redis.from_url(self.redis_url, socket_timeout=1.0, decode_responses=True)
            client.ping()
            self._redis_client = client
            self._redis_available = True
            logger.info("Connected to Redis cache at %s", self.redis_url)
        except Exception:
            self._redis_available = False
            self._redis_client = None
            logger.debug("Redis not available, using disk storage at %s", self.file_path)

    def load_all_states(self) -> Dict[str, Dict[str, Any]]:
        """Load all camera states from storage."""
        if self._redis_available and self._redis_client:
            try:
                data = self._redis_client.get("frigate:cameras:state")
                if data:
                    return json.loads(data)
            except Exception as e:
                logger.warning("Failed to load state from Redis: %s", e)

        if self.file_path.is_file():
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    return json.load(f) or {}
            except Exception as e:
                logger.warning("Failed to load state from disk: %s", e)
        return {}

    def save_all_states(self, states: Dict[str, Dict[str, Any]]) -> None:
        """Save all camera states to storage."""
        if self._redis_available and self._redis_client:
            try:
                self._redis_client.set("frigate:cameras:state", json.dumps(states))
            except Exception as e:
                logger.warning("Failed to write state to Redis: %s", e)

        try:
            temp_file = self.file_path.with_suffix(".tmp")
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(states, f, indent=2)
            temp_file.replace(self.file_path)
        except Exception as e:
            logger.warning("Failed to write state to disk: %s", e)

    def load_camera_state(self, camera_id: str) -> Optional[Dict[str, Any]]:
        """Load single camera state."""
        states = self.load_all_states()
        return states.get(camera_id)

    def save_camera_state(self, camera_id: str, state: Dict[str, Any]) -> None:
        """Save single camera state."""
        states = self.load_all_states()
        states[camera_id] = state
        self.save_all_states(states)


_storage_instance: Optional[Storage] = None


def get_storage() -> Storage:
    """Retrieve singleton Storage instance."""
    global _storage_instance
    if _storage_instance is None:
        _storage_instance = Storage()
    return _storage_instance


def reset_storage() -> Storage:
    """Reset singleton Storage instance."""
    global _storage_instance
    _storage_instance = Storage()
    return _storage_instance
