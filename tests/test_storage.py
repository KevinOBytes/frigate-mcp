"""Tests for storage layer and state persistence."""

import json
from pathlib import Path

from app.storage import Storage


def test_storage_disk_fallback(tmp_path: Path):
    storage = Storage(data_dir=str(tmp_path), redis_url="redis://invalid-host:9999/0")
    assert storage._redis_available is False

    # Save state
    storage.save_camera_state("cam_1", {"brightness": 90, "pan_position": 45.0})

    # Reload from fresh storage instance
    new_storage = Storage(data_dir=str(tmp_path), redis_url="redis://invalid-host:9999/0")
    state = new_storage.load_camera_state("cam_1")
    assert state is not None
    assert state["brightness"] == 90
    assert state["pan_position"] == 45.0

    # Verify JSON file on disk
    file_path = tmp_path / "cameras_state.json"
    assert file_path.exists()
    data = json.loads(file_path.read_text(encoding="utf-8"))
    assert data["cam_1"]["brightness"] == 90
