"""Command dispatch and structured JSON response formatting for Frigate-MCP."""

import json
from typing import Any, Dict, Optional

try:
    from app import frigate
except ImportError:
    import frigate


class StatusCode:
    """Standard HTTP status codes supported by Frigate-MCP."""

    SUCCESS = 200
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    INTERNAL_SERVER_ERROR = 500


STATUS_MESSAGES = {
    StatusCode.SUCCESS: "Operation completed successfully",
    StatusCode.BAD_REQUEST: "Bad request",
    StatusCode.UNAUTHORIZED: "Unauthorized access",
    StatusCode.FORBIDDEN: "Forbidden operation",
    StatusCode.NOT_FOUND: "Resource not found",
    StatusCode.INTERNAL_SERVER_ERROR: "Internal server error",
}


def build_response(
    status_code: int,
    message: Optional[str] = None,
    data: Any = None,
    command: Optional[str] = None,
) -> Dict[str, Any]:
    """Construct a canonical Frigate-MCP response dictionary."""
    is_success = 200 <= status_code < 300
    status_text = "success" if is_success else "error"
    resolved_message = message or STATUS_MESSAGES.get(status_code, "Operation completed")

    payload: Dict[str, Any] = {
        "status": status_text,
        "message": resolved_message,
        "status_code": status_code,
        "data": data,
    }
    if command is not None:
        payload["command"] = command
    return payload


def send_command(
    command: str,
    status_code: int,
    data: Any = None,
    message: Optional[str] = None,
) -> Dict[str, Any]:
    """Format and send command response to frigate transport and return response dict."""
    response_payload = build_response(
        status_code=status_code,
        message=message,
        data=data,
        command=command,
    )
    frigate.send(json.dumps(response_payload))
    return response_payload


def send_success(
    command: str,
    data: Any = None,
    message: Optional[str] = None,
) -> Dict[str, Any]:
    """Dispatch a 200 Success response."""
    return send_command(command, StatusCode.SUCCESS, data, message or "Operation completed successfully")


def send_bad_request(
    command: str,
    data: Any = None,
    message: Optional[str] = None,
) -> Dict[str, Any]:
    """Dispatch a 400 Bad Request response."""
    return send_command(command, StatusCode.BAD_REQUEST, data, message or "Bad request")


def send_unauthorized(
    command: str,
    data: Any = None,
    message: Optional[str] = None,
) -> Dict[str, Any]:
    """Dispatch a 401 Unauthorized response."""
    return send_command(command, StatusCode.UNAUTHORIZED, data, message or "Unauthorized access")


def send_not_found(
    command: str,
    data: Any = None,
    message: Optional[str] = None,
) -> Dict[str, Any]:
    """Dispatch a 404 Not Found response."""
    return send_command(command, StatusCode.NOT_FOUND, data, message or "Resource not found")


def send_forbidden(
    command: str,
    data: Any = None,
    message: Optional[str] = None,
) -> Dict[str, Any]:
    """Dispatch a 403 Forbidden response."""
    return send_command(command, StatusCode.FORBIDDEN, data, message or "Forbidden operation")


def send_internal_server_error(
    command: str,
    data: Any = None,
    message: Optional[str] = None,
) -> Dict[str, Any]:
    """Dispatch a 500 Internal Server Error response."""
    return send_command(command, StatusCode.INTERNAL_SERVER_ERROR, data, message or "Internal server error")
