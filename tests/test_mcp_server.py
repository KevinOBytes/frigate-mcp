"""Tests for FastMCP server tools, resources, prompts, and Starlette HTTP endpoints."""

import json

import pytest
from starlette.testclient import TestClient

from app.mcp_server import create_starlette_app, mcp_server


@pytest.mark.anyio
async def test_mcp_tools():
    tools = await mcp_server.list_tools()
    tool_names = [t.name for t in tools]
    expected_tools = [
        "list_cameras",
        "picture",
        "clip",
        "record",
        "stop_record",
        "pan",
        "tilt",
        "zoom",
        "focus",
        "auto_focus",
        "disable_auto_focus",
        "night_vision",
        "infrared",
        "motion_detection",
        "privacy_mode",
        "audio",
        "speaker",
        "microphone",
        "speaker_volume",
        "microphone_volume",
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
        "get_camera_settings",
        "set_setting",
        "server_status",
        "get_events",
        "get_event_picture",
        "get_event_clip",
        "retain_event",
    ]
    for expected in expected_tools:
        assert expected in tool_names, f"Tool '{expected}' should be registered in MCP server"

    # Test calling list_cameras
    res = await mcp_server.call_tool("list_cameras", {})
    parsed = json.loads(res.content[0].text)
    assert parsed["status"] == "success"
    assert len(parsed["data"]) >= 4

    # Test calling picture
    res = await mcp_server.call_tool("picture", {"camera_id": "camera_1"})
    parsed = json.loads(res.content[0].text)
    assert parsed["status"] == "success"
    assert parsed["data"]["camera_id"] == "camera_1"

    # Test calling pan
    res = await mcp_server.call_tool("pan", {"camera_id": "camera_1", "direction": "left"})
    parsed = json.loads(res.content[0].text)
    assert parsed["status"] == "success"

    # Test calling get_events
    res_ev = await mcp_server.call_tool("get_events", {"limit": 2})
    parsed_ev = json.loads(res_ev.content[0].text)
    assert parsed_ev["status"] == "success"
    assert len(parsed_ev["data"]) == 2


@pytest.mark.anyio
async def test_mcp_resources():
    resources = await mcp_server.list_resources()
    assert len(resources) >= 3

    # Read cameras resource
    content = await mcp_server.read_resource("frigate://cameras")
    data = json.loads(content[0].content)
    assert isinstance(data, list)
    assert len(data) >= 4

    # Read events resource
    content_ev = await mcp_server.read_resource("frigate://events")
    data_ev = json.loads(content_ev[0].content)
    assert isinstance(data_ev, list)
    assert len(data_ev) > 0


@pytest.mark.anyio
async def test_mcp_prompts():
    prompts = await mcp_server.list_prompts()
    prompt_names = [p.name for p in prompts]
    assert "camera_audit" in prompt_names
    assert "security_sweep" in prompt_names

    p = await mcp_server.get_prompt("camera_audit", {"camera_id": "camera_1"})
    assert "camera_1" in p.messages[0].content.text


def test_http_endpoints():
    app = create_starlette_app()
    client = TestClient(app)

    # /health
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["data"]["server"] == "frigate-mcp"

    # /status
    res = client.get("/status")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"

    # /command list
    res = client.post("/command", json={"command": "list"})
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert len(data["data"]) >= 4

    # /command picture
    res = client.post("/command", json={"command": "picture", "camera_id": "camera_1"})
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["data"]["camera_id"] == "camera_1"

    # /command invalid
    res = client.post("/command", json={"command": "nonexistent"})
    assert res.status_code == 400
