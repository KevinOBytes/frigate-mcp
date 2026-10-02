"""Unit tests for commands.py and response formatting."""

from app.commands import (
    StatusCode,
    build_response,
    send_bad_request,
    send_command,
    send_forbidden,
    send_internal_server_error,
    send_not_found,
    send_success,
    send_unauthorized,
)


def test_status_codes():
    assert StatusCode.SUCCESS == 200
    assert StatusCode.BAD_REQUEST == 400
    assert StatusCode.UNAUTHORIZED == 401
    assert StatusCode.FORBIDDEN == 403
    assert StatusCode.NOT_FOUND == 404
    assert StatusCode.INTERNAL_SERVER_ERROR == 500


def test_build_response_success():
    res = build_response(StatusCode.SUCCESS, "All good", {"key": "val"}, command="test")
    assert res["status"] == "success"
    assert res["status_code"] == 200
    assert res["message"] == "All good"
    assert res["data"] == {"key": "val"}
    assert res["command"] == "test"


def test_build_response_error():
    res = build_response(StatusCode.NOT_FOUND, "Camera not found", None, command="picture")
    assert res["status"] == "error"
    assert res["status_code"] == 404
    assert res["message"] == "Camera not found"
    assert res["data"] is None
    assert res["command"] == "picture"


def test_send_helpers():
    s = send_success("list", [{"id": "cam1"}], "Listed")
    assert s["status"] == "success"
    assert s["status_code"] == 200

    b = send_bad_request("pan", None, "Invalid direction")
    assert b["status"] == "error"
    assert b["status_code"] == 400

    u = send_unauthorized("admin", None)
    assert u["status"] == "error"
    assert u["status_code"] == 401

    f = send_forbidden("delete", None)
    assert f["status"] == "error"
    assert f["status_code"] == 403

    n = send_not_found("picture", None, "Not found")
    assert n["status"] == "error"
    assert n["status_code"] == 404

    ie = send_internal_server_error("crash", None)
    assert ie["status"] == "error"
    assert ie["status_code"] == 500


def test_send_command_dispatches_json():
    res = send_command("custom", StatusCode.SUCCESS, {"foo": "bar"}, "Custom ok")
    assert res["command"] == "custom"
    assert res["data"] == {"foo": "bar"}
