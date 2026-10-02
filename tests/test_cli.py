"""Integration tests for CLI entrypoint and commands."""

import json

from app.main import cli_entrypoint


def test_cli_version(capsys):
    code = cli_entrypoint(["--version"])
    assert code == 0
    captured = capsys.readouterr()
    res = json.loads(captured.out)
    assert res["status"] == "success"
    assert res["data"]["version"] == "1.0.0"


def test_cli_help(capsys):
    code = cli_entrypoint(["help"])
    assert code == 0
    captured = capsys.readouterr()
    res = json.loads(captured.out)
    assert res["status"] == "success"
    assert "basic_commands" in res["data"]
    assert "camera_commands" in res["data"]


def test_cli_list(capsys):
    code = cli_entrypoint(["list"])
    assert code == 0
    captured = capsys.readouterr()
    res = json.loads(captured.out)
    assert res["status"] == "success"
    assert isinstance(res["data"], list)
    assert len(res["data"]) >= 4


def test_cli_picture(capsys):
    code = cli_entrypoint(["picture", "camera_1"])
    assert code == 0
    captured = capsys.readouterr()
    res = json.loads(captured.out)
    assert res["status"] == "success"
    assert res["data"]["camera_id"] == "camera_1"
    assert "image" in res["data"]


def test_cli_picture_missing_camera(capsys):
    code = cli_entrypoint(["picture", "non_existent"])
    assert code == 1
    captured = capsys.readouterr()
    res = json.loads(captured.out)
    assert res["status"] == "error"
    assert res["status_code"] == 404


def test_cli_record_and_stop_record(capsys):
    code = cli_entrypoint(["record", "camera_1"])
    assert code == 0
    res = json.loads(capsys.readouterr().out)
    assert res["status"] == "success"
    assert res["data"]["recording"] is True

    code = cli_entrypoint(["stop-record", "camera_1"])
    assert code == 0
    res = json.loads(capsys.readouterr().out)
    assert res["status"] == "success"
    assert res["data"]["recording"] is False


def test_cli_pan_tilt_zoom(capsys):
    code = cli_entrypoint(["pan", "camera_1", "left"])
    assert code == 0
    res = json.loads(capsys.readouterr().out)
    assert res["status"] == "success"

    code = cli_entrypoint(["tilt", "camera_1", "up"])
    assert code == 0
    res = json.loads(capsys.readouterr().out)
    assert res["status"] == "success"

    code = cli_entrypoint(["zoom", "camera_1", "in"])
    assert code == 0
    res = json.loads(capsys.readouterr().out)
    assert res["status"] == "success"


def test_cli_level_validation(capsys):
    # Valid level
    code = cli_entrypoint(["brightness", "camera_1", "85"])
    assert code == 0
    res = json.loads(capsys.readouterr().out)
    assert res["status"] == "success"
    assert res["data"]["brightness"] == 85

    # Invalid level: out of bounds
    code = cli_entrypoint(["brightness", "camera_1", "120"])
    assert code == 1
    res = json.loads(capsys.readouterr().out)
    assert res["status"] == "error"
    assert res["status_code"] == 400

    # Invalid level: non-integer
    code = cli_entrypoint(["brightness", "camera_1", "high"])
    assert code == 1
    res = json.loads(capsys.readouterr().out)
    assert res["status"] == "error"
    assert res["status_code"] == 400


def test_cli_settings_and_set_setting(capsys):
    code = cli_entrypoint(["set", "setting", "camera_1", "custom_key", "custom_val"])
    assert code == 0
    res = json.loads(capsys.readouterr().out)
    assert res["status"] == "success"
    assert res["data"]["setting"] == "custom_key"
    assert res["data"]["value"] == "custom_val"

    code = cli_entrypoint(["settings", "camera_1"])
    assert code == 0
    res = json.loads(capsys.readouterr().out)
    assert res["status"] == "success"
    assert res["data"]["settings"]["custom_key"] == "custom_val"


def test_cli_status(capsys):
    code = cli_entrypoint(["status"])
    assert code == 0
    res = json.loads(capsys.readouterr().out)
    assert res["status"] == "success"
    assert res["data"]["server"] == "frigate-mcp"


def test_cli_stop(capsys):
    code = cli_entrypoint(["stop"])
    assert code == 0
    res = json.loads(capsys.readouterr().out)
    assert res["status"] == "success"


def test_cli_events(capsys):
    code = cli_entrypoint(["events", "--limit", "2"])
    assert code == 0
    res = json.loads(capsys.readouterr().out)
    assert res["status"] == "success"
    assert len(res["data"]) == 2

    # Filter by label
    code = cli_entrypoint(["events", "--label", "person"])
    assert code == 0
    res = json.loads(capsys.readouterr().out)
    assert res["status"] == "success"
    for ev in res["data"]:
        assert ev["label"] == "person"


def test_cli_event_media(capsys):
    code = cli_entrypoint(["event-picture", "evt_101"])
    assert code == 0
    res = json.loads(capsys.readouterr().out)
    assert res["status"] == "success"
    assert "image" in res["data"]

    code = cli_entrypoint(["event-clip", "evt_101"])
    assert code == 0
    res = json.loads(capsys.readouterr().out)
    assert res["status"] == "success"
    assert "url" in res["data"]

    code = cli_entrypoint(["retain-event", "evt_101", "true"])
    assert code == 0
    res = json.loads(capsys.readouterr().out)
    assert res["status"] == "success"
    assert res["data"]["retained"] is True
