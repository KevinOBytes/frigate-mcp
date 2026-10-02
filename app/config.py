"""Configuration management for Frigate-MCP."""

import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml


class Config:
    """Application configuration loaded from environment variables and YAML file."""

    def __init__(self, config_path: Optional[str] = None):
        self.env = os.getenv("FRIGATE_MCP_ENV", "production")
        self.log_level = os.getenv("FRIGATE_MCP_LOG_LEVEL", "info").lower()
        self.host = os.getenv("FRIGATE_MCP_HOST", "0.0.0.0")
        self.port = int(os.getenv("FRIGATE_MCP_PORT", "5000"))
        self.debug = os.getenv("FRIGATE_MCP_DEBUG", "false").lower() in ("true", "1", "yes")
        self.workers = int(os.getenv("FRIGATE_MCP_WORKERS", "4"))
        self.timeout = int(os.getenv("FRIGATE_MCP_TIMEOUT", "30"))
        self.reload = os.getenv("FRIGATE_MCP_RELOAD", "false").lower() in ("true", "1", "yes")
        self.workdir = os.getenv("FRIGATE_MCP_WORKDIR", "/app")
        self.log_file = os.getenv("FRIGATE_MCP_LOG_FILE", "./logs/frigate-mcp.log")
        self.data_dir = os.getenv("FRIGATE_MCP_DATA", "./data")
        self.cache_dir = os.getenv("FRIGATE_MCP_CACHE", "./cache")

        # Frigate NVR connection
        self.frigate_url = os.getenv("FRIGATE_URL", os.getenv("FRIGATE_HOST", "http://localhost:5000"))
        if not self.frigate_url.startswith("http://") and not self.frigate_url.startswith("https://"):
            self.frigate_url = f"http://{self.frigate_url}"
        self.frigate_timeout = float(os.getenv("FRIGATE_TIMEOUT", "5.0"))
        self.simulation_mode = os.getenv("FRIGATE_SIMULATION_MODE", "auto").lower()

        # Redis connection
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

        # Load YAML config if present
        cfg_file = config_path or os.getenv("FRIGATE_MCP_CONFIG")
        self.yaml_data: Dict[str, Any] = {}
        if cfg_file:
            path = Path(cfg_file)
            if path.is_file():
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        self.yaml_data = yaml.safe_load(f) or {}
                except Exception:
                    self.yaml_data = {}

        # Merge YAML values
        if "frigate" in self.yaml_data:
            f_cfg = self.yaml_data["frigate"]
            if "url" in f_cfg:
                self.frigate_url = f_cfg["url"]
            if "timeout" in f_cfg:
                self.frigate_timeout = float(f_cfg["timeout"])

        self.cameras: Dict[str, Dict[str, Any]] = self.yaml_data.get(
            "cameras",
            {
                "camera_1": {"name": "Front Porch", "model": "PTZ-1080P"},
                "camera_2": {"name": "Backyard", "model": "Fixed-4K"},
                "front_door": {"name": "Front Doorbell", "model": "Doorbell-2K"},
                "driveway": {"name": "Driveway", "model": "PTZ-4K"},
            },
        )


_config_instance: Optional[Config] = None


def get_config(config_path: Optional[str] = None) -> Config:
    """Retrieve singleton config instance."""
    global _config_instance
    if _config_instance is None or config_path is not None:
        _config_instance = Config(config_path)
    return _config_instance


def reset_config(config_path: Optional[str] = None) -> Config:
    """Reset singleton config instance."""
    global _config_instance
    _config_instance = Config(config_path)
    return _config_instance
