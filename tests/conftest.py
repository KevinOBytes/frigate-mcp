"""Pytest shared configuration and fixtures."""

import pytest

from app.config import reset_config
from app.frigate import reset_client
from app.storage import reset_storage


@pytest.fixture(autouse=True)
def isolate_test_environment(tmp_path, monkeypatch):
    """Isolate data directory and singleton states for each test."""
    monkeypatch.setenv("FRIGATE_MCP_DATA", str(tmp_path))
    reset_config()
    reset_storage()
    reset_client()
