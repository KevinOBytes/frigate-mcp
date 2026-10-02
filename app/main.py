"""Frigate-MCP Main Entrypoint and CLI.

Provides CLI command parsing for all camera operations, server lifecycle,
and MCP server execution over SSE or stdio transports.
"""

import argparse
import asyncio
import json
import logging
import os
import signal
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logging.basicConfig(stream=sys.stderr, level=logging.WARNING, format="%(levelname)s: %(message)s")

# Support execution both as installed package and direct script
if __package__ is None or __package__ == "":
    # When executed as python main.py directly inside app/
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    sys.path.insert(0, str(Path(__file__).resolve().parent))

try:
    from app.commands import (
        StatusCode,
        build_response,
        send_bad_request,
        send_not_found,
        send_success,
    )
    from app.config import get_config
    from app.frigate import get_client
    from app.mcp_server import create_starlette_app, mcp_server
except ImportError:
    from commands import (
        StatusCode,
        build_response,
        send_bad_request,
        send_not_found,
        send_success,
    )
    from frigate import get_client
    from mcp_server import create_starlette_app, mcp_server

    from config import get_config

PID_FILE = Path(os.getenv("FRIGATE_MCP_PID_FILE", "/tmp/frigate-mcp.pid"))
VERSION = "1.0.0"


def _print_json(res: Dict[str, Any]) -> None:
    """Print response dictionary as formatted JSON to stdout."""
    print(json.dumps(res, indent=2))


def _get_server_pid() -> Optional[int]:
    """Read running PID from PID file if process is still alive."""
    if PID_FILE.exists():
        try:
            pid = int(PID_FILE.read_text(encoding="utf-8").strip())
            os.kill(pid, 0)
            return pid
        except (ValueError, OSError):
            try:
                PID_FILE.unlink(missing_ok=True)
            except Exception:
                pass
    return None


def _write_pid(pid: int) -> None:
    """Write process PID to PID file."""
    try:
        PID_FILE.parent.mkdir(parents=True, exist_ok=True)
        PID_FILE.write_text(str(pid), encoding="utf-8")
    except Exception:
        pass


def _remove_pid() -> None:
    """Remove PID file."""
    try:
        PID_FILE.unlink(missing_ok=True)
    except Exception:
        pass


def handle_server_start(args: argparse.Namespace) -> int:
    """Handle frigate-mcp start command."""
    pid = _get_server_pid()
    if pid is not None:
        res = build_response(
            StatusCode.SUCCESS,
            f"Frigate MCP server is already running (PID: {pid})",
            {"pid": pid, "status": "running"},
            "start",
        )
        _print_json(res)
        return 0

    cfg = get_config(args.config)
    res = build_response(
        StatusCode.SUCCESS,
        "Frigate MCP server starting",
        {"host": cfg.host, "port": cfg.port, "status": "starting"},
        "start",
    )
    _print_json(res)
    return run_server(args)


def handle_server_stop(args: argparse.Namespace) -> int:
    """Handle frigate-mcp stop or quit command."""
    pid = _get_server_pid()
    if pid is not None:
        try:
            os.kill(pid, signal.SIGTERM)
            _remove_pid()
            res = build_response(
                StatusCode.SUCCESS,
                f"Frigate MCP server (PID: {pid}) stopped successfully",
                {"pid": pid, "status": "stopped"},
                "stop",
            )
            _print_json(res)
            return 0
        except OSError as e:
            res = build_response(
                StatusCode.INTERNAL_SERVER_ERROR,
                f"Failed to stop server PID {pid}: {e}",
                None,
                "stop",
            )
            _print_json(res)
            return 1

    res = build_response(
        StatusCode.SUCCESS,
        "Frigate MCP server is not currently running",
        {"status": "stopped"},
        "stop",
    )
    _print_json(res)
    return 0


def handle_server_restart(args: argparse.Namespace) -> int:
    """Handle frigate-mcp restart command."""
    handle_server_stop(args)
    return handle_server_start(args)


def handle_server_status(args: argparse.Namespace) -> int:
    """Handle frigate-mcp status command."""
    client = get_client()
    status_data = client.get_status()
    pid = _get_server_pid()
    status_data["pid"] = pid
    status_data["server_running"] = pid is not None

    res = send_success("status", status_data, "Server status retrieved")
    _print_json(res)
    return 0


def handle_camera_commands(command: str, args: List[str]) -> Tuple[int, Dict[str, Any]]:
    """Dispatch camera-specific commands."""
    client = get_client()

    if command == "list":
        cams = client.list_cameras()
        res = send_success("list", cams, "Cameras listed successfully")
        return 0, res

    if command == "events":
        # Syntax: events [camera_id] [--label <label>] [--limit <limit>]
        camera_id = None
        label = None
        limit = 20
        idx = 0
        while idx < len(args):
            arg = args[idx]
            if arg == "--label" and idx + 1 < len(args):
                label = args[idx + 1]
                idx += 2
            elif arg == "--limit" and idx + 1 < len(args):
                try:
                    limit = int(args[idx + 1])
                except ValueError:
                    pass
                idx += 2
            elif not arg.startswith("-") and camera_id is None:
                camera_id = arg
                idx += 1
            else:
                idx += 1

        ok, msg, data = client.get_events(camera_id=camera_id, label=label, limit=limit)
        res = send_success("events", data, msg)
        return 0, res

    if command == "event-picture":
        if not args:
            return 1, send_bad_request("event-picture", None, "Event ID required: frigate-mcp event-picture <event_id>")
        ok, msg, data = client.get_event_picture(args[0])
        if ok:
            return 0, send_success("event-picture", data, msg)
        return 1, send_not_found("event-picture", data, msg)

    if command == "event-clip":
        if not args:
            return 1, send_bad_request("event-clip", None, "Event ID required: frigate-mcp event-clip <event_id>")
        ok, msg, data = client.get_event_clip(args[0])
        if ok:
            return 0, send_success("event-clip", data, msg)
        return 1, send_not_found("event-clip", data, msg)

    if command == "retain-event":
        if not args:
            return 1, send_bad_request(
                "retain-event", None, "Event ID required: frigate-mcp retain-event <event_id> [true|false]"
            )
        event_id = args[0]
        retain = True
        if len(args) > 1 and args[1].lower() in ("false", "0", "off", "no"):
            retain = False
        ok, msg, data = client.retain_event(event_id, retain)
        return 0, send_success("retain-event", data, msg)

    if not args:
        res = send_bad_request(command, None, f"Camera ID required for '{command}' command")
        return 1, res

    cam_id = args[0]
    rest_args = args[1:]

    if command == "picture":
        ok, msg, data = client.capture_picture(cam_id)
        if ok:
            return 0, send_success("picture", data, msg)
        return 1, send_not_found("picture", data, msg)

    if command == "clip":
        ok, msg, data = client.capture_clip(cam_id)
        if ok:
            return 0, send_success("clip", data, msg)
        return 1, send_not_found("clip", data, msg)

    if command == "record":
        ok, msg, data = client.start_recording(cam_id)
        if ok:
            return 0, send_success("record", data, msg)
        return 1, send_not_found("record", data, msg)

    if command == "stop-record":
        ok, msg, data = client.stop_recording(cam_id)
        if ok:
            return 0, send_success("stop-record", data, msg)
        return 1, send_not_found("stop-record", data, msg)

    if command in ("pan", "tilt", "zoom"):
        if not rest_args:
            return 1, send_bad_request(
                command, None, f"Direction required for '{command}' (e.g. {command} <cam> left/right/up/down/in/out)"
            )
        direction = rest_args[0]
        func = getattr(client, command)
        ok, msg, data = func(cam_id, direction)
        if ok:
            return 0, send_success(command, data, msg)
        code_func = send_not_found if "not found" in msg.lower() else send_bad_request
        return 1, code_func(command, data, msg)

    if command == "focus":
        ok, msg, data = client.focus(cam_id)
        if ok:
            return 0, send_success("focus", data, msg)
        return 1, send_not_found("focus", data, msg)

    if command == "auto-focus":
        ok, msg, data = client.set_auto_focus(cam_id, True)
        if ok:
            return 0, send_success("auto-focus", data, msg)
        return 1, send_not_found("auto-focus", data, msg)

    if command == "disable-auto-focus":
        ok, msg, data = client.set_auto_focus(cam_id, False)
        if ok:
            return 0, send_success("disable-auto-focus", data, msg)
        return 1, send_not_found("disable-auto-focus", data, msg)

    toggle_map = {
        "night-vision": "night_vision",
        "infrared": "infrared",
        "motion-detection": "motion_detection",
        "privacy-mode": "privacy_mode",
        "audio": "audio",
        "speaker": "speaker",
        "microphone": "microphone",
    }
    if command in toggle_map:
        if not rest_args:
            return 1, send_bad_request(command, None, f"State ('on' or 'off') required for '{command}'")
        state = rest_args[0]
        ok, msg, data = client.set_toggle(cam_id, toggle_map[command], state)
        if ok:
            return 0, send_success(command, data, msg)
        code_func = send_not_found if "not found" in msg.lower() else send_bad_request
        return 1, code_func(command, data, msg)

    level_map = {
        "speaker-volume": "speaker_volume",
        "microphone-volume": "microphone_volume",
        "brightness": "brightness",
        "contrast": "contrast",
        "saturation": "saturation",
        "sharpness": "sharpness",
        "white-balance": "white_balance",
        "exposure": "exposure",
        "gain": "gain",
        "hue": "hue",
        "gamma": "gamma",
        "backlight-compensation": "backlight_compensation",
        "noise-reduction": "noise_reduction",
    }
    if command in level_map:
        if not rest_args:
            return 1, send_bad_request(command, None, f"Level (0-100) required for '{command}'")
        try:
            level = int(rest_args[0])
        except ValueError:
            return 1, send_bad_request(command, None, f"Level must be an integer, received: '{rest_args[0]}'")
        ok, msg, data = client.set_level(cam_id, level_map[command], level)
        if ok:
            return 0, send_success(command, data, msg)
        code_func = send_not_found if "not found" in msg.lower() else send_bad_request
        return 1, code_func(command, data, msg)

    if command == "settings":
        ok, msg, data = client.get_settings(cam_id)
        if ok:
            return 0, send_success("settings", data, msg)
        return 1, send_not_found("settings", data, msg)

    return 1, send_bad_request(command, None, f"Unrecognized command '{command}'")


def handle_set_command(args: List[str]) -> Tuple[int, Dict[str, Any]]:
    """Handle 'frigate-mcp set setting <camera_id> <setting> <value>' syntax."""
    # Syntax: set setting <camera_id> <setting> <value>
    client = get_client()
    if len(args) >= 4 and args[0] == "setting":
        cam_id = args[1]
        setting = args[2]
        value = " ".join(args[3:])
        ok, msg, data = client.set_custom_setting(cam_id, setting, value)
        if ok:
            return 0, send_success("set", data, msg)
        code_func = send_not_found if "not found" in msg.lower() else send_bad_request
        return 1, code_func("set", data, msg)
    if len(args) >= 3:
        cam_id = args[0]
        setting = args[1]
        value = " ".join(args[2:])
        ok, msg, data = client.set_custom_setting(cam_id, setting, value)
        if ok:
            return 0, send_success("set", data, msg)
        code_func = send_not_found if "not found" in msg.lower() else send_bad_request
        return 1, code_func("set", data, msg)

    return 1, send_bad_request("set", None, "Usage: frigate-mcp set setting <camera_id> <setting> <value>")


def run_server(args: argparse.Namespace) -> int:
    """Start MCP Server in specified transport mode (sse or stdio)."""
    cfg = get_config(args.config)
    transport = getattr(args, "transport", None) or os.getenv("FRIGATE_MCP_TRANSPORT", "sse").lower()
    host = getattr(args, "host", None) or cfg.host
    port = getattr(args, "port", None) or cfg.port

    _write_pid(os.getpid())

    try:
        if transport == "stdio":
            asyncio.run(mcp_server.run_stdio_async())
        else:
            import uvicorn

            app = create_starlette_app()
            uvicorn.run(
                app,
                host=host,
                port=port,
                log_level=cfg.log_level,
                workers=1,
            )
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        _remove_pid()
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Build root CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="frigate-mcp",
        description="Frigate Multi-Camera Processing MCP Server and CLI",
        add_help=True,
    )
    parser.add_argument("--version", action="version", version=f"frigate-mcp {VERSION}")
    parser.add_argument("--config", "-c", type=str, default=None, help="Path to YAML configuration file")
    parser.add_argument("--transport", "-t", choices=["sse", "stdio"], default=None, help="MCP transport mode")
    parser.add_argument("--host", type=str, default=None, help="Bind host for SSE server")
    parser.add_argument("--port", "-p", type=int, default=None, help="Bind port for SSE server")
    return parser


def cli_entrypoint(argv: Optional[List[str]] = None) -> int:
    """Main CLI entrypoint function."""
    if argv is None:
        argv = sys.argv[1:]

    # Handle standard --version flag early
    if "--version" in argv:
        res = send_success("version", {"version": VERSION}, f"frigate-mcp v{VERSION}")
        _print_json(res)
        return 0

    # Handle help command as json if explicitly passed as positional 'help'
    if argv and argv[0] == "help":
        help_data = {
            "version": VERSION,
            "usage": "frigate-mcp <command> [arguments]",
            "basic_commands": ["help", "--help", "--version", "quit", "status", "start", "stop", "restart", "serve"],
            "camera_commands": [
                "list",
                "picture",
                "clip",
                "record",
                "stop-record",
                "pan",
                "tilt",
                "zoom",
                "focus",
                "auto-focus",
                "disable-auto-focus",
                "night-vision",
                "infrared",
                "motion-detection",
                "privacy-mode",
                "audio",
                "speaker",
                "microphone",
                "speaker-volume",
                "microphone-volume",
                "brightness",
                "contrast",
                "saturation",
                "sharpness",
                "white-balance",
                "exposure",
                "gain",
                "hue",
                "gamma",
                "backlight-compensation",
                "noise-reduction",
                "settings",
                "set setting",
                "events",
                "event-picture",
                "event-clip",
                "retain-event",
            ],
        }
        res = send_success("help", help_data, "Frigate MCP command reference")
        _print_json(res)
        return 0

    # If no arguments are provided, default to starting the MCP server
    if not argv:
        parser = build_parser()
        args = parser.parse_args([])
        return run_server(args)

    cmd = argv[0].lower()
    cmd_args = argv[1:]

    # Check for server lifecycle commands
    parser = build_parser()
    args, unknown = parser.parse_known_args(argv)

    if cmd in ("serve", "server"):
        return run_server(args)
    if cmd == "start":
        return handle_server_start(args)
    if cmd in ("stop", "quit"):
        return handle_server_stop(args)
    if cmd == "restart":
        return handle_server_restart(args)
    if cmd == "status":
        return handle_server_status(args)
    if cmd == "set":
        exit_code, res = handle_set_command(cmd_args)
        _print_json(res)
        return exit_code

    # Dispatch camera commands
    exit_code, res = handle_camera_commands(cmd, cmd_args)
    _print_json(res)
    return exit_code


if __name__ == "__main__":
    sys.exit(cli_entrypoint())
