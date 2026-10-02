"""Unit tests for frigate client and camera state simulation."""

from app.frigate import CameraState, get_client


def test_camera_state_defaults():
    cam = CameraState("cam_test", "Test Camera", "PTZ-100")
    assert cam.camera_id == "cam_test"
    assert cam.name == "Test Camera"
    assert cam.status == "online"
    assert cam.is_recording is False
    assert cam.pan_position == 0.0
    assert cam.brightness == 50
    settings = cam.get_all_settings()
    assert settings["brightness"] == 50
    assert settings["motion_detection"] == "on"


def test_list_cameras():
    client = get_client()
    cams = client.list_cameras()
    assert len(cams) >= 4
    cam_ids = [c["camera_id"] for c in cams]
    assert "camera_1" in cam_ids
    assert "camera_2" in cam_ids


def test_capture_picture():
    client = get_client()
    ok, msg, data = client.capture_picture("camera_1")
    assert ok is True
    assert "successfully" in msg.lower()
    assert data["camera_id"] == "camera_1"
    assert data["format"] == "jpeg"
    assert len(data["image"]) > 0

    # Missing camera
    ok, msg, data = client.capture_picture("unknown_cam")
    assert ok is False
    assert data is None
    assert "not found" in msg.lower()


def test_capture_clip():
    client = get_client()
    ok, msg, data = client.capture_clip("camera_1")
    assert ok is True
    assert data["camera_id"] == "camera_1"
    assert "clip_id" in data
    assert "url" in data


def test_recording_toggles():
    client = get_client()
    ok, msg, data = client.start_recording("camera_1")
    assert ok is True
    assert data["recording"] is True
    cam = client.get_camera("camera_1")
    assert cam.is_recording is True

    ok, msg, data = client.stop_recording("camera_1")
    assert ok is True
    assert data["recording"] is False
    assert cam.is_recording is False


def test_ptz_pan_tilt_zoom():
    client = get_client()

    # Pan
    ok, msg, data = client.pan("camera_1", "left")
    assert ok is True
    assert data["pan_position"] == -15.0

    ok, msg, data = client.pan("camera_1", "right")
    assert ok is True
    assert data["pan_position"] == 0.0

    ok, msg, data = client.pan("camera_1", "invalid")
    assert ok is False
    assert "invalid" in msg.lower()

    # Tilt
    ok, msg, data = client.tilt("camera_1", "up")
    assert ok is True
    assert data["tilt_position"] == 10.0

    ok, msg, data = client.tilt("camera_1", "down")
    assert ok is True
    assert data["tilt_position"] == 0.0

    # Zoom
    ok, msg, data = client.zoom("camera_1", "in")
    assert ok is True
    assert data["zoom_level"] == 1.5

    ok, msg, data = client.zoom("camera_1", "out")
    assert ok is True
    assert data["zoom_level"] == 1.0


def test_focus_and_auto_focus():
    client = get_client()
    ok, msg, data = client.focus("camera_1")
    assert ok is True
    assert data["focused"] is True

    ok, msg, data = client.set_auto_focus("camera_1", False)
    assert ok is True
    assert data["auto_focus"] is False

    ok, msg, data = client.set_auto_focus("camera_1", True)
    assert ok is True
    assert data["auto_focus"] is True


def test_feature_toggles():
    client = get_client()
    features = ["night_vision", "infrared", "motion_detection", "privacy_mode", "audio", "speaker", "microphone"]
    for feat in features:
        ok, msg, data = client.set_toggle("camera_1", feat, "off")
        assert ok is True
        assert data[feat] is False

        ok, msg, data = client.set_toggle("camera_1", feat, "on")
        assert ok is True
        assert data[feat] is True

    # Invalid state
    ok, msg, data = client.set_toggle("camera_1", "night_vision", "maybe")
    assert ok is False


def test_level_settings():
    client = get_client()
    levels = [
        "brightness",
        "contrast",
        "saturation",
        "sharpness",
        "white_balance",
        "exposure",
        "gain",
        "hue",
        "gamma",
        "backlight_compensation",
        "noise_reduction",
        "speaker_volume",
        "microphone_volume",
    ]
    for param in levels:
        ok, msg, data = client.set_level("camera_1", param, 75)
        assert ok is True
        assert data[param] == 75

    # Boundary tests
    ok, msg, data = client.set_level("camera_1", "brightness", 0)
    assert ok is True
    ok, msg, data = client.set_level("camera_1", "brightness", 100)
    assert ok is True

    # Invalid levels
    ok, msg, data = client.set_level("camera_1", "brightness", -1)
    assert ok is False
    ok, msg, data = client.set_level("camera_1", "brightness", 101)
    assert ok is False


def test_custom_settings():
    client = get_client()
    ok, msg, data = client.set_custom_setting("camera_1", "custom_param", "custom_value")
    assert ok is True
    assert data["setting"] == "custom_param"
    assert data["value"] == "custom_value"

    ok, msg, data = client.get_settings("camera_1")
    assert ok is True
    assert data["settings"]["custom_param"] == "custom_value"


def test_server_status():
    client = get_client()
    status = client.get_status()
    assert status["server"] == "frigate-mcp"
    assert status["status"] == "running"
    assert status["cameras_count"] >= 4
