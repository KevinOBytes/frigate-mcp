"""Model Context Protocol (MCP) Server for Frigate multi-camera ecosystem.

Provides tools, resources, and prompts for camera management, PTZ controls,
snapshot capture, and settings configuration over stdio and SSE transports.
"""

import json
import logging
from typing import Any, Dict, Optional

from mcp.server import MCPServer
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.commands import (
    StatusCode,
    build_response,
    send_bad_request,
    send_not_found,
    send_success,
)
from app.frigate import get_client

logger = logging.getLogger("frigate-mcp.server")

# Create primary MCP Server
mcp_server = MCPServer(
    name="frigate-mcp",
    version="1.0.0",
    instructions="Manage and interact with Frigate NVR cameras via structured commands and tools.",
)


def _format_tool_result(res: Dict[str, Any]) -> str:
    """Serialize canonical response dict to JSON string for tool return."""
    return json.dumps(res, indent=2)


# ============================================================================
# MCP Tools
# ============================================================================


@mcp_server.tool()
def list_cameras() -> str:
    """List all available Frigate cameras and their status."""
    client = get_client()
    cams = client.list_cameras()
    res = send_success("list", cams, "Cameras retrieved successfully")
    return _format_tool_result(res)


@mcp_server.tool()
def picture(camera_id: str) -> str:
    """Take a picture / snapshot from the specified camera."""
    client = get_client()
    ok, msg, data = client.capture_picture(camera_id)
    if not ok:
        res = send_not_found("picture", data, msg)
    else:
        res = send_success("picture", data, msg)
    return _format_tool_result(res)


@mcp_server.tool()
def clip(camera_id: str) -> str:
    """Take a video clip from the specified camera."""
    client = get_client()
    ok, msg, data = client.capture_clip(camera_id)
    if not ok:
        res = send_not_found("clip", data, msg)
    else:
        res = send_success("clip", data, msg)
    return _format_tool_result(res)


@mcp_server.tool()
def record(camera_id: str) -> str:
    """Start recording from the specified camera."""
    client = get_client()
    ok, msg, data = client.start_recording(camera_id)
    if not ok:
        res = send_not_found("record", data, msg)
    else:
        res = send_success("record", data, msg)
    return _format_tool_result(res)


@mcp_server.tool()
def stop_record(camera_id: str) -> str:
    """Stop recording from the specified camera."""
    client = get_client()
    ok, msg, data = client.stop_recording(camera_id)
    if not ok:
        res = send_not_found("stop-record", data, msg)
    else:
        res = send_success("stop-record", data, msg)
    return _format_tool_result(res)


@mcp_server.tool()
def pan(camera_id: str, direction: str) -> str:
    """Pan the specified camera left or right (direction: 'left' | 'right')."""
    client = get_client()
    ok, msg, data = client.pan(camera_id, direction)
    if not ok:
        res = (
            send_not_found("pan", data, msg)
            if data is None and "not found" in msg.lower()
            else send_bad_request("pan", data, msg)
        )
    else:
        res = send_success("pan", data, msg)
    return _format_tool_result(res)


@mcp_server.tool()
def tilt(camera_id: str, direction: str) -> str:
    """Tilt the specified camera upwards or downwards (direction: 'up' | 'down')."""
    client = get_client()
    ok, msg, data = client.tilt(camera_id, direction)
    if not ok:
        res = (
            send_not_found("tilt", data, msg)
            if data is None and "not found" in msg.lower()
            else send_bad_request("tilt", data, msg)
        )
    else:
        res = send_success("tilt", data, msg)
    return _format_tool_result(res)


@mcp_server.tool()
def zoom(camera_id: str, direction: str) -> str:
    """Zoom the specified camera in or out (direction: 'in' | 'out')."""
    client = get_client()
    ok, msg, data = client.zoom(camera_id, direction)
    if not ok:
        res = (
            send_not_found("zoom", data, msg)
            if data is None and "not found" in msg.lower()
            else send_bad_request("zoom", data, msg)
        )
    else:
        res = send_success("zoom", data, msg)
    return _format_tool_result(res)


@mcp_server.tool()
def focus(camera_id: str) -> str:
    """Focus the specified camera."""
    client = get_client()
    ok, msg, data = client.focus(camera_id)
    if not ok:
        res = send_not_found("focus", data, msg)
    else:
        res = send_success("focus", data, msg)
    return _format_tool_result(res)


@mcp_server.tool()
def auto_focus(camera_id: str) -> str:
    """Enable auto-focus for the specified camera."""
    client = get_client()
    ok, msg, data = client.set_auto_focus(camera_id, True)
    if not ok:
        res = send_not_found("auto-focus", data, msg)
    else:
        res = send_success("auto-focus", data, msg)
    return _format_tool_result(res)


@mcp_server.tool()
def disable_auto_focus(camera_id: str) -> str:
    """Disable auto-focus for the specified camera."""
    client = get_client()
    ok, msg, data = client.set_auto_focus(camera_id, False)
    if not ok:
        res = send_not_found("disable-auto-focus", data, msg)
    else:
        res = send_success("disable-auto-focus", data, msg)
    return _format_tool_result(res)


@mcp_server.tool()
def night_vision(camera_id: str, state: str) -> str:
    """Enable or disable night vision for camera (state: 'on' | 'off')."""
    client = get_client()
    ok, msg, data = client.set_toggle(camera_id, "night_vision", state)
    if not ok:
        res = (
            send_not_found("night-vision", data, msg)
            if "not found" in msg.lower()
            else send_bad_request("night-vision", data, msg)
        )
    else:
        res = send_success("night-vision", data, msg)
    return _format_tool_result(res)


@mcp_server.tool()
def infrared(camera_id: str, state: str) -> str:
    """Enable or disable infrared for camera (state: 'on' | 'off')."""
    client = get_client()
    ok, msg, data = client.set_toggle(camera_id, "infrared", state)
    if not ok:
        res = (
            send_not_found("infrared", data, msg)
            if "not found" in msg.lower()
            else send_bad_request("infrared", data, msg)
        )
    else:
        res = send_success("infrared", data, msg)
    return _format_tool_result(res)


@mcp_server.tool()
def motion_detection(camera_id: str, state: str) -> str:
    """Enable or disable motion detection for camera (state: 'on' | 'off')."""
    client = get_client()
    ok, msg, data = client.set_toggle(camera_id, "motion_detection", state)
    if not ok:
        res = (
            send_not_found("motion-detection", data, msg)
            if "not found" in msg.lower()
            else send_bad_request("motion-detection", data, msg)
        )
    else:
        res = send_success("motion-detection", data, msg)
    return _format_tool_result(res)


@mcp_server.tool()
def privacy_mode(camera_id: str, state: str) -> str:
    """Enable or disable privacy mode for camera (state: 'on' | 'off')."""
    client = get_client()
    ok, msg, data = client.set_toggle(camera_id, "privacy_mode", state)
    if not ok:
        res = (
            send_not_found("privacy-mode", data, msg)
            if "not found" in msg.lower()
            else send_bad_request("privacy-mode", data, msg)
        )
    else:
        res = send_success("privacy-mode", data, msg)
    return _format_tool_result(res)


@mcp_server.tool()
def audio(camera_id: str, state: str) -> str:
    """Enable or disable audio for camera (state: 'on' | 'off')."""
    client = get_client()
    ok, msg, data = client.set_toggle(camera_id, "audio", state)
    if not ok:
        res = send_not_found("audio", data, msg) if "not found" in msg.lower() else send_bad_request("audio", data, msg)
    else:
        res = send_success("audio", data, msg)
    return _format_tool_result(res)


@mcp_server.tool()
def speaker(camera_id: str, state: str) -> str:
    """Enable or disable speaker for camera (state: 'on' | 'off')."""
    client = get_client()
    ok, msg, data = client.set_toggle(camera_id, "speaker", state)
    if not ok:
        res = (
            send_not_found("speaker", data, msg)
            if "not found" in msg.lower()
            else send_bad_request("speaker", data, msg)
        )
    else:
        res = send_success("speaker", data, msg)
    return _format_tool_result(res)


@mcp_server.tool()
def microphone(camera_id: str, state: str) -> str:
    """Enable or disable microphone for camera (state: 'on' | 'off')."""
    client = get_client()
    ok, msg, data = client.set_toggle(camera_id, "microphone", state)
    if not ok:
        res = (
            send_not_found("microphone", data, msg)
            if "not found" in msg.lower()
            else send_bad_request("microphone", data, msg)
        )
    else:
        res = send_success("microphone", data, msg)
    return _format_tool_result(res)


@mcp_server.tool()
def speaker_volume(camera_id: str, level: int) -> str:
    """Set speaker volume for camera (level: 0-100)."""
    client = get_client()
    ok, msg, data = client.set_level(camera_id, "speaker_volume", level)
    if not ok:
        res = (
            send_not_found("speaker-volume", data, msg)
            if "not found" in msg.lower()
            else send_bad_request("speaker-volume", data, msg)
        )
    else:
        res = send_success("speaker-volume", data, msg)
    return _format_tool_result(res)


@mcp_server.tool()
def microphone_volume(camera_id: str, level: int) -> str:
    """Set microphone volume for camera (level: 0-100)."""
    client = get_client()
    ok, msg, data = client.set_level(camera_id, "microphone_volume", level)
    if not ok:
        res = (
            send_not_found("microphone-volume", data, msg)
            if "not found" in msg.lower()
            else send_bad_request("microphone-volume", data, msg)
        )
    else:
        res = send_success("microphone-volume", data, msg)
    return _format_tool_result(res)


@mcp_server.tool()
def brightness(camera_id: str, level: int) -> str:
    """Set brightness for camera (level: 0-100)."""
    client = get_client()
    ok, msg, data = client.set_level(camera_id, "brightness", level)
    if not ok:
        res = (
            send_not_found("brightness", data, msg)
            if "not found" in msg.lower()
            else send_bad_request("brightness", data, msg)
        )
    else:
        res = send_success("brightness", data, msg)
    return _format_tool_result(res)


@mcp_server.tool()
def contrast(camera_id: str, level: int) -> str:
    """Set contrast for camera (level: 0-100)."""
    client = get_client()
    ok, msg, data = client.set_level(camera_id, "contrast", level)
    if not ok:
        res = (
            send_not_found("contrast", data, msg)
            if "not found" in msg.lower()
            else send_bad_request("contrast", data, msg)
        )
    else:
        res = send_success("contrast", data, msg)
    return _format_tool_result(res)


@mcp_server.tool()
def saturation(camera_id: str, level: int) -> str:
    """Set saturation for camera (level: 0-100)."""
    client = get_client()
    ok, msg, data = client.set_level(camera_id, "saturation", level)
    if not ok:
        res = (
            send_not_found("saturation", data, msg)
            if "not found" in msg.lower()
            else send_bad_request("saturation", data, msg)
        )
    else:
        res = send_success("saturation", data, msg)
    return _format_tool_result(res)


@mcp_server.tool()
def sharpness(camera_id: str, level: int) -> str:
    """Set sharpness for camera (level: 0-100)."""
    client = get_client()
    ok, msg, data = client.set_level(camera_id, "sharpness", level)
    if not ok:
        res = (
            send_not_found("sharpness", data, msg)
            if "not found" in msg.lower()
            else send_bad_request("sharpness", data, msg)
        )
    else:
        res = send_success("sharpness", data, msg)
    return _format_tool_result(res)


@mcp_server.tool()
def white_balance(camera_id: str, level: int) -> str:
    """Set white balance for camera (level: 0-100)."""
    client = get_client()
    ok, msg, data = client.set_level(camera_id, "white_balance", level)
    if not ok:
        res = (
            send_not_found("white-balance", data, msg)
            if "not found" in msg.lower()
            else send_bad_request("white-balance", data, msg)
        )
    else:
        res = send_success("white-balance", data, msg)
    return _format_tool_result(res)


@mcp_server.tool()
def exposure(camera_id: str, level: int) -> str:
    """Set exposure for camera (level: 0-100)."""
    client = get_client()
    ok, msg, data = client.set_level(camera_id, "exposure", level)
    if not ok:
        res = (
            send_not_found("exposure", data, msg)
            if "not found" in msg.lower()
            else send_bad_request("exposure", data, msg)
        )
    else:
        res = send_success("exposure", data, msg)
    return _format_tool_result(res)


@mcp_server.tool()
def gain(camera_id: str, level: int) -> str:
    """Set gain for camera (level: 0-100)."""
    client = get_client()
    ok, msg, data = client.set_level(camera_id, "gain", level)
    if not ok:
        res = send_not_found("gain", data, msg) if "not found" in msg.lower() else send_bad_request("gain", data, msg)
    else:
        res = send_success("gain", data, msg)
    return _format_tool_result(res)


@mcp_server.tool()
def hue(camera_id: str, level: int) -> str:
    """Set hue for camera (level: 0-100)."""
    client = get_client()
    ok, msg, data = client.set_level(camera_id, "hue", level)
    if not ok:
        res = send_not_found("hue", data, msg) if "not found" in msg.lower() else send_bad_request("hue", data, msg)
    else:
        res = send_success("hue", data, msg)
    return _format_tool_result(res)


@mcp_server.tool()
def gamma(camera_id: str, level: int) -> str:
    """Set gamma for camera (level: 0-100)."""
    client = get_client()
    ok, msg, data = client.set_level(camera_id, "gamma", level)
    if not ok:
        res = send_not_found("gamma", data, msg) if "not found" in msg.lower() else send_bad_request("gamma", data, msg)
    else:
        res = send_success("gamma", data, msg)
    return _format_tool_result(res)


@mcp_server.tool()
def backlight_compensation(camera_id: str, level: int) -> str:
    """Set backlight compensation for camera (level: 0-100)."""
    client = get_client()
    ok, msg, data = client.set_level(camera_id, "backlight_compensation", level)
    if not ok:
        res = (
            send_not_found("backlight-compensation", data, msg)
            if "not found" in msg.lower()
            else send_bad_request("backlight-compensation", data, msg)
        )
    else:
        res = send_success("backlight-compensation", data, msg)
    return _format_tool_result(res)


@mcp_server.tool()
def noise_reduction(camera_id: str, level: int) -> str:
    """Set noise reduction for camera (level: 0-100)."""
    client = get_client()
    ok, msg, data = client.set_level(camera_id, "noise_reduction", level)
    if not ok:
        res = (
            send_not_found("noise-reduction", data, msg)
            if "not found" in msg.lower()
            else send_bad_request("noise-reduction", data, msg)
        )
    else:
        res = send_success("noise-reduction", data, msg)
    return _format_tool_result(res)


@mcp_server.tool()
def get_events(camera_id: Optional[str] = None, label: Optional[str] = None, limit: int = 20) -> str:
    """Retrieve detected object events and alerts (person, car, dog, package, etc.)."""
    client = get_client()
    ok, msg, data = client.get_events(camera_id=camera_id, label=label, limit=limit)
    res = send_success("events", data, msg)
    return _format_tool_result(res)


@mcp_server.tool()
def get_event_picture(event_id: str) -> str:
    """Retrieve snapshot picture for a detected object event."""
    client = get_client()
    ok, msg, data = client.get_event_picture(event_id)
    if not ok:
        res = send_not_found("event-picture", data, msg)
    else:
        res = send_success("event-picture", data, msg)
    return _format_tool_result(res)


@mcp_server.tool()
def get_event_clip(event_id: str) -> str:
    """Retrieve video clip for a detected object event."""
    client = get_client()
    ok, msg, data = client.get_event_clip(event_id)
    if not ok:
        res = send_not_found("event-clip", data, msg)
    else:
        res = send_success("event-clip", data, msg)
    return _format_tool_result(res)


@mcp_server.tool()
def retain_event(event_id: str, retain: bool = True) -> str:
    """Keep / retain an event indefinitely so Frigate does not purge it."""
    client = get_client()
    ok, msg, data = client.retain_event(event_id, retain)
    res = send_success("retain-event", data, msg)
    return _format_tool_result(res)


@mcp_server.tool()
def get_camera_settings(camera_id: str) -> str:
    """Get all current settings for the specified camera."""
    client = get_client()
    ok, msg, data = client.get_settings(camera_id)
    if not ok:
        res = send_not_found("settings", data, msg)
    else:
        res = send_success("settings", data, msg)
    return _format_tool_result(res)


@mcp_server.tool()
def set_setting(camera_id: str, setting: str, value: str) -> str:
    """Set any setting for the specified camera (frigate-mcp set setting <cam> <key> <val>)."""
    client = get_client()
    ok, msg, data = client.set_custom_setting(camera_id, setting, value)
    if not ok:
        res = send_not_found("set", data, msg) if "not found" in msg.lower() else send_bad_request("set", data, msg)
    else:
        res = send_success("set", data, msg)
    return _format_tool_result(res)


@mcp_server.tool()
def server_status() -> str:
    """Get the current operational status of the Frigate MCP server."""
    client = get_client()
    status_data = client.get_status()
    res = send_success("status", status_data, "Server is operational")
    return _format_tool_result(res)


# ============================================================================
# MCP Resources
# ============================================================================


@mcp_server.resource("frigate://cameras")
def resource_cameras() -> str:
    """Available Frigate cameras resource."""
    client = get_client()
    return json.dumps(client.list_cameras(), indent=2)


@mcp_server.resource("frigate://events")
def resource_events() -> str:
    """Recent Frigate object detection events resource."""
    client = get_client()
    _, _, events = client.get_events(limit=25)
    return json.dumps(events, indent=2)


@mcp_server.resource("frigate://cameras/{camera_id}/settings")
def resource_camera_settings(camera_id: str) -> str:
    """Camera settings resource."""
    client = get_client()
    cam = client.get_camera(camera_id)
    if not cam:
        return json.dumps({"error": f"Camera '{camera_id}' not found"}, indent=2)
    return json.dumps(cam.get_all_settings(), indent=2)


@mcp_server.resource("frigate://status")
def resource_status() -> str:
    """System health and status resource."""
    client = get_client()
    return json.dumps(client.get_status(), indent=2)


# ============================================================================
# MCP Prompts
# ============================================================================


@mcp_server.prompt()
def camera_audit(camera_id: str) -> str:
    """Generate an audit prompt for camera health, settings, and recording status."""
    return (
        f"Inspect camera '{camera_id}'. Retrieve its current settings, "
        f"verify that recording and motion detection are active, and evaluate image quality."
    )


@mcp_server.prompt()
def security_sweep() -> str:
    """Generate a multi-camera security sweep prompt across all online cameras."""
    return (
        "Execute a full security sweep across all connected Frigate cameras. "
        "List all cameras, capture a snapshot from each, verify recording status, and report anomalies."
    )


# ============================================================================
# HTTP Custom Routes for Docker & REST clients
# ============================================================================


@mcp_server.custom_route("/health", methods=["GET"])
async def health_endpoint(request: Request) -> JSONResponse:
    """Health check endpoint."""
    client = get_client()
    return JSONResponse(build_response(StatusCode.SUCCESS, "Frigate MCP server is healthy", client.get_status()))


@mcp_server.custom_route("/status", methods=["GET"])
async def status_endpoint(request: Request) -> JSONResponse:
    """Status endpoint."""
    client = get_client()
    return JSONResponse(build_response(StatusCode.SUCCESS, "Server status", client.get_status()))


@mcp_server.custom_route("/command", methods=["POST"])
async def command_endpoint(request: Request) -> JSONResponse:
    """Generic command dispatch endpoint."""
    try:
        body = await request.json()
    except Exception:
        return JSONResponse(
            build_response(StatusCode.BAD_REQUEST, "Malformed JSON request body", None), status_code=400
        )

    cmd = body.get("command")
    camera_id = body.get("camera_id")

    client = get_client()

    if not cmd:
        return JSONResponse(
            build_response(StatusCode.BAD_REQUEST, "Missing 'command' field in request", None), status_code=400
        )

    if cmd == "list":
        return JSONResponse(send_success("list", client.list_cameras()))
    if cmd == "status":
        return JSONResponse(send_success("status", client.get_status()))
    if cmd == "picture" and camera_id:
        ok, msg, data = client.capture_picture(camera_id)
        code = StatusCode.SUCCESS if ok else StatusCode.NOT_FOUND
        return JSONResponse(build_response(code, msg, data, cmd), status_code=code)

    return JSONResponse(build_response(StatusCode.BAD_REQUEST, f"Unknown command '{cmd}'", None), status_code=400)


def create_starlette_app():
    """Create the configured Starlette application for SSE and HTTP."""
    return mcp_server.sse_app()
