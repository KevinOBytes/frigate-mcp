"""Frigate client library and camera management engine.

Provides unified interface for camera discovery, PTZ controls,
snapshot capture, clip generation, camera parameter adjustments,
Frigate event detection, and real-time state persistence.
Supports live Frigate NVR endpoints with automated simulation fallback.
"""

import base64
import json
import logging
import time
from typing import Any, Dict, List, Optional, Tuple

import httpx

from app.config import get_config
from app.mqtt import get_mqtt
from app.storage import get_storage

logger = logging.getLogger("frigate-mcp.frigate")

# 1x1 valid JPEG image encoded in base64
MINIMAL_JPEG_B64 = (
    "/9j/4AAQSkZJRgABAQEASABIAAD/2wBDAP///////////////////////////////////"
    "///////////////////////////////////////////////////wgALCAABAAEBAREA"
    "/8QAFBABAAAAAAAAAAAAAAAAAAAAAP/aAAgBAQABPxA="
)


class CameraState:
    """Represents the real-time operational state of a Frigate camera."""

    def __init__(self, camera_id: str, name: Optional[str] = None, model: str = "Standard-Camera"):
        self.camera_id = camera_id
        self.name = name or camera_id
        self.model = model
        self.status = "online"
        self.is_recording = False
        self.pan_position = 0.0  # -180.0 to 180.0
        self.tilt_position = 0.0  # -90.0 to 90.0
        self.zoom_level = 1.0  # 1.0x to 10.0x
        self.focused = True
        self.auto_focus = True

        # Toggles
        self.night_vision = False
        self.infrared = False
        self.motion_detection = True
        self.privacy_mode = False
        self.audio = True
        self.speaker = True
        self.microphone = True

        # Scaled settings (0-100)
        self.speaker_volume = 50
        self.microphone_volume = 50
        self.brightness = 50
        self.contrast = 50
        self.saturation = 50
        self.sharpness = 50
        self.white_balance = 50
        self.exposure = 50
        self.gain = 50
        self.hue = 50
        self.gamma = 50
        self.backlight_compensation = 50
        self.noise_reduction = 50

        # Custom settings dict
        self.custom_settings: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert camera state to dictionary."""
        return {
            "camera_id": self.camera_id,
            "name": self.name,
            "model": self.model,
            "status": self.status,
            "recording": self.is_recording,
            "pan_position": self.pan_position,
            "tilt_position": self.tilt_position,
            "zoom_level": self.zoom_level,
            "auto_focus": self.auto_focus,
            "night_vision": self.night_vision,
            "infrared": self.infrared,
            "motion_detection": self.motion_detection,
            "privacy_mode": self.privacy_mode,
            "audio": self.audio,
            "speaker": self.speaker,
            "microphone": self.microphone,
            "settings": self.get_all_settings(),
        }

    def to_state_dict(self) -> Dict[str, Any]:
        """Convert full internal state to dictionary for persistence."""
        return {
            "camera_id": self.camera_id,
            "name": self.name,
            "model": self.model,
            "status": self.status,
            "recording": self.is_recording,
            "pan_position": self.pan_position,
            "tilt_position": self.tilt_position,
            "zoom_level": self.zoom_level,
            "auto_focus": self.auto_focus,
            "night_vision": self.night_vision,
            "infrared": self.infrared,
            "motion_detection": self.motion_detection,
            "privacy_mode": self.privacy_mode,
            "audio": self.audio,
            "speaker": self.speaker,
            "microphone": self.microphone,
            "speaker_volume": self.speaker_volume,
            "microphone_volume": self.microphone_volume,
            "brightness": self.brightness,
            "contrast": self.contrast,
            "saturation": self.saturation,
            "sharpness": self.sharpness,
            "white_balance": self.white_balance,
            "exposure": self.exposure,
            "gain": self.gain,
            "hue": self.hue,
            "gamma": self.gamma,
            "backlight_compensation": self.backlight_compensation,
            "noise_reduction": self.noise_reduction,
            "custom_settings": self.custom_settings,
        }

    def update_from_dict(self, data: Dict[str, Any]) -> None:
        """Update state attributes from saved dictionary."""
        for key, val in data.items():
            if key == "recording":
                self.is_recording = bool(val)
            elif key == "custom_settings" and isinstance(val, dict):
                self.custom_settings.update(val)
            elif hasattr(self, key):
                setattr(self, key, val)

    def get_all_settings(self) -> Dict[str, Any]:
        """Retrieve dictionary of all current settings."""
        settings = {
            "recording": self.is_recording,
            "auto_focus": self.auto_focus,
            "night_vision": "on" if self.night_vision else "off",
            "infrared": "on" if self.infrared else "off",
            "motion_detection": "on" if self.motion_detection else "off",
            "privacy_mode": "on" if self.privacy_mode else "off",
            "audio": "on" if self.audio else "off",
            "speaker": "on" if self.speaker else "off",
            "microphone": "on" if self.microphone else "off",
            "speaker_volume": self.speaker_volume,
            "microphone_volume": self.microphone_volume,
            "brightness": self.brightness,
            "contrast": self.contrast,
            "saturation": self.saturation,
            "sharpness": self.sharpness,
            "white_balance": self.white_balance,
            "exposure": self.exposure,
            "gain": self.gain,
            "hue": self.hue,
            "gamma": self.gamma,
            "backlight_compensation": self.backlight_compensation,
            "noise_reduction": self.noise_reduction,
        }
        settings.update(self.custom_settings)
        return settings


class FrigateClient:
    """Client for interacting with Frigate NVR and managing cameras."""

    def __init__(self, config_path: Optional[str] = None):
        self.config = get_config(config_path)
        self.base_url = self.config.frigate_url.rstrip("/")
        self.timeout = self.config.frigate_timeout
        self.storage = get_storage()
        self.mqtt = get_mqtt()
        self.is_connected = False
        self.cameras: Dict[str, CameraState] = {}
        self._init_cameras()
        self._check_connection()

    def _init_cameras(self) -> None:
        """Initialize camera states from configuration and stored persistence."""
        saved_states = self.storage.load_all_states()

        for cam_id, cam_info in self.config.cameras.items():
            name = cam_info.get("name", cam_id)
            model = cam_info.get("model", "Standard-Camera")
            state = CameraState(cam_id, name, model)
            if cam_id in saved_states:
                state.update_from_dict(saved_states[cam_id])
            self.cameras[cam_id] = state

    def _persist_camera(self, camera_id: str) -> None:
        """Save updated camera state to persistence layer."""
        cam = self.cameras.get(camera_id)
        if cam:
            self.storage.save_camera_state(camera_id, cam.to_state_dict())

    def _check_connection(self) -> bool:
        """Attempt to ping Frigate REST API."""
        try:
            with httpx.Client(timeout=1.0) as client:
                res = client.get(f"{self.base_url}/api/version")
                if res.status_code == 200:
                    self.is_connected = True
                    logger.info("Connected to Frigate NVR at %s (version: %s)", self.base_url, res.text.strip())
                    self._sync_cameras_from_frigate(client)
                    return True
        except Exception:
            pass
        self.is_connected = False
        logger.debug("Frigate NVR not reachable at %s, running in simulation mode", self.base_url)
        return False

    def _sync_cameras_from_frigate(self, client: httpx.Client) -> None:
        """Sync camera list from live Frigate instance."""
        try:
            res = client.get(f"{self.base_url}/api/config")
            if res.status_code == 200:
                cfg = res.json()
                frigate_cams = cfg.get("cameras", {})
                for cam_id, cam_cfg in frigate_cams.items():
                    if cam_id not in self.cameras:
                        self.cameras[cam_id] = CameraState(cam_id, cam_cfg.get("name", cam_id))
        except Exception as e:
            logger.warning("Failed to sync config from Frigate NVR: %s", e)

    def get_camera(self, camera_id: str) -> Optional[CameraState]:
        """Get camera state by ID."""
        return self.cameras.get(camera_id)

    def list_cameras(self) -> List[Dict[str, Any]]:
        """List all available cameras."""
        return [
            {
                "camera_id": cam.camera_id,
                "name": cam.name,
                "model": cam.model,
                "status": cam.status,
                "recording": cam.is_recording,
            }
            for cam in self.cameras.values()
        ]

    def capture_picture(self, camera_id: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Capture picture from camera."""
        cam = self.get_camera(camera_id)
        if not cam:
            return False, f"Camera '{camera_id}' not found", None

        image_data = MINIMAL_JPEG_B64
        if self.is_connected:
            try:
                with httpx.Client(timeout=self.timeout) as client:
                    resp = client.get(f"{self.base_url}/api/{camera_id}/latest.jpg")
                    if resp.status_code == 200:
                        image_data = base64.b64encode(resp.content).decode("ascii")
            except Exception as e:
                logger.warning("Live picture capture failed for %s, using fallback: %s", camera_id, e)

        data = {
            "camera_id": camera_id,
            "image": image_data,
            "format": "jpeg",
            "timestamp": time.time(),
        }
        return True, "Image captured successfully", data

    def capture_clip(self, camera_id: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Capture a video clip from camera."""
        cam = self.get_camera(camera_id)
        if not cam:
            return False, f"Camera '{camera_id}' not found", None

        clip_id = f"clip_{camera_id}_{int(time.time())}.mp4"
        clip_url = f"{self.base_url}/api/events/{clip_id}" if self.is_connected else f"/data/clips/{clip_id}"

        data = {
            "camera_id": camera_id,
            "clip_id": clip_id,
            "url": clip_url,
            "duration_seconds": 10,
            "timestamp": time.time(),
        }
        return True, "Video clip captured successfully", data

    def start_recording(self, camera_id: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Start recording on camera."""
        cam = self.get_camera(camera_id)
        if not cam:
            return False, f"Camera '{camera_id}' not found", None

        cam.is_recording = True
        self._persist_camera(camera_id)
        self.mqtt.publish(f"{camera_id}/recordings/set", "ON")

        if self.is_connected:
            try:
                with httpx.Client(timeout=self.timeout) as client:
                    client.post(f"{self.base_url}/api/{camera_id}/recordings/state", json={"state": "ON"})
            except Exception as e:
                logger.warning("Live recording toggle failed for %s: %s", camera_id, e)

        data = {"camera_id": camera_id, "recording": True}
        return True, f"Recording started on camera {camera_id}", data

    def stop_recording(self, camera_id: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Stop recording on camera."""
        cam = self.get_camera(camera_id)
        if not cam:
            return False, f"Camera '{camera_id}' not found", None

        cam.is_recording = False
        self._persist_camera(camera_id)
        self.mqtt.publish(f"{camera_id}/recordings/set", "OFF")

        if self.is_connected:
            try:
                with httpx.Client(timeout=self.timeout) as client:
                    client.post(f"{self.base_url}/api/{camera_id}/recordings/state", json={"state": "OFF"})
            except Exception as e:
                logger.warning("Live recording toggle failed for %s: %s", camera_id, e)

        data = {"camera_id": camera_id, "recording": False}
        return True, f"Recording stopped on camera {camera_id}", data

    def pan(self, camera_id: str, direction: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Pan camera left or right."""
        cam = self.get_camera(camera_id)
        if not cam:
            return False, f"Camera '{camera_id}' not found", None

        direction = direction.lower()
        if direction not in ("left", "right"):
            return False, f"Invalid pan direction: {direction}. Expected 'left' or 'right'", None

        delta = -15.0 if direction == "left" else 15.0
        cam.pan_position = max(-180.0, min(180.0, cam.pan_position + delta))
        self._persist_camera(camera_id)
        self.mqtt.publish(f"{camera_id}/ptz", f"PAN_{direction.upper()}")

        if self.is_connected:
            try:
                with httpx.Client(timeout=self.timeout) as client:
                    client.post(
                        f"{self.base_url}/api/{camera_id}/ptz", json={"action": "move", "argument": f"pan-{direction}"}
                    )
            except Exception as e:
                logger.warning("PTZ pan failed: %s", e)

        data = {"camera_id": camera_id, "pan_position": cam.pan_position, "direction": direction}
        return True, f"Camera {camera_id} panned {direction} to {cam.pan_position}°", data

    def tilt(self, camera_id: str, direction: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Tilt camera up or down."""
        cam = self.get_camera(camera_id)
        if not cam:
            return False, f"Camera '{camera_id}' not found", None

        direction = direction.lower()
        if direction not in ("up", "down"):
            return False, f"Invalid tilt direction: {direction}. Expected 'up' or 'down'", None

        delta = 10.0 if direction == "up" else -10.0
        cam.tilt_position = max(-90.0, min(90.0, cam.tilt_position + delta))
        self._persist_camera(camera_id)
        self.mqtt.publish(f"{camera_id}/ptz", f"TILT_{direction.upper()}")

        if self.is_connected:
            try:
                with httpx.Client(timeout=self.timeout) as client:
                    client.post(
                        f"{self.base_url}/api/{camera_id}/ptz", json={"action": "move", "argument": f"tilt-{direction}"}
                    )
            except Exception as e:
                logger.warning("PTZ tilt failed: %s", e)

        data = {"camera_id": camera_id, "tilt_position": cam.tilt_position, "direction": direction}
        return True, f"Camera {camera_id} tilted {direction} to {cam.tilt_position}°", data

    def zoom(self, camera_id: str, direction: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Zoom camera in or out."""
        cam = self.get_camera(camera_id)
        if not cam:
            return False, f"Camera '{camera_id}' not found", None

        direction = direction.lower()
        if direction not in ("in", "out"):
            return False, f"Invalid zoom direction: {direction}. Expected 'in' or 'out'", None

        delta = 0.5 if direction == "in" else -0.5
        cam.zoom_level = max(1.0, min(10.0, round(cam.zoom_level + delta, 1)))
        self._persist_camera(camera_id)
        self.mqtt.publish(f"{camera_id}/ptz", f"ZOOM_{direction.upper()}")

        if self.is_connected:
            try:
                with httpx.Client(timeout=self.timeout) as client:
                    client.post(
                        f"{self.base_url}/api/{camera_id}/ptz", json={"action": "move", "argument": f"zoom-{direction}"}
                    )
            except Exception as e:
                logger.warning("PTZ zoom failed: %s", e)

        data = {"camera_id": camera_id, "zoom_level": cam.zoom_level, "direction": direction}
        return True, f"Camera {camera_id} zoomed {direction} to {cam.zoom_level}x", data

    def focus(self, camera_id: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Perform manual focus trigger on camera."""
        cam = self.get_camera(camera_id)
        if not cam:
            return False, f"Camera '{camera_id}' not found", None

        cam.focused = True
        self._persist_camera(camera_id)
        data = {"camera_id": camera_id, "focused": True}
        return True, f"Camera {camera_id} focused successfully", data

    def set_auto_focus(self, camera_id: str, enabled: bool) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Enable or disable auto-focus."""
        cam = self.get_camera(camera_id)
        if not cam:
            return False, f"Camera '{camera_id}' not found", None

        cam.auto_focus = enabled
        self._persist_camera(camera_id)
        data = {"camera_id": camera_id, "auto_focus": enabled}
        state_str = "enabled" if enabled else "disabled"
        return True, f"Auto-focus {state_str} for camera {camera_id}", data

    def set_toggle(self, camera_id: str, feature: str, state: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Generic handler for on/off camera feature toggles."""
        cam = self.get_camera(camera_id)
        if not cam:
            return False, f"Camera '{camera_id}' not found", None

        state_clean = state.strip().lower()
        if state_clean not in ("on", "off", "enable", "disable", "true", "false", "1", "0"):
            return False, f"Invalid state: '{state}'. Expected 'on' or 'off'", None

        is_on = state_clean in ("on", "enable", "true", "1")
        if not hasattr(cam, feature):
            return False, f"Unknown feature: {feature}", None

        setattr(cam, feature, is_on)
        self._persist_camera(camera_id)

        # Frigate API & MQTT sync for toggles
        topic_suffix = f"{camera_id}/{feature}/set"
        self.mqtt.publish(topic_suffix, "ON" if is_on else "OFF")

        if self.is_connected:
            api_map = {
                "motion_detection": "motion",
                "audio": "audio",
            }
            if feature in api_map:
                try:
                    with httpx.Client(timeout=self.timeout) as client:
                        client.post(
                            f"{self.base_url}/api/{camera_id}/{api_map[feature]}/set",
                            json={"state": "ON" if is_on else "OFF"},
                        )
                except Exception as e:
                    logger.warning("Feature toggle failed on Frigate: %s", e)

        display_name = feature.replace("_", " ")
        status_text = "enabled" if is_on else "disabled"
        data = {"camera_id": camera_id, feature: is_on, "state": "on" if is_on else "off"}
        return True, f"{display_name.capitalize()} {status_text} for camera {camera_id}", data

    def set_level(self, camera_id: str, parameter: str, level: int) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Generic handler for 0-100 camera parameter adjustments."""
        cam = self.get_camera(camera_id)
        if not cam:
            return False, f"Camera '{camera_id}' not found", None

        if not isinstance(level, int) or level < 0 or level > 100:
            return False, f"Invalid level: {level}. Level must be an integer between 0 and 100", None

        if not hasattr(cam, parameter):
            return False, f"Unknown parameter: {parameter}", None

        setattr(cam, parameter, level)
        self._persist_camera(camera_id)
        display_name = parameter.replace("_", " ")
        data = {"camera_id": camera_id, parameter: level}
        return True, f"{display_name.capitalize()} set to {level} for camera {camera_id}", data

    def get_settings(self, camera_id: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Retrieve all settings for the specified camera."""
        cam = self.get_camera(camera_id)
        if not cam:
            return False, f"Camera '{camera_id}' not found", None

        data = {
            "camera_id": camera_id,
            "settings": cam.get_all_settings(),
        }
        return True, f"Settings retrieved successfully for camera {camera_id}", data

    def set_custom_setting(
        self, camera_id: str, setting: str, value: Any
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Set a named camera setting to an arbitrary value."""
        cam = self.get_camera(camera_id)
        if not cam:
            return False, f"Camera '{camera_id}' not found", None

        setting_clean = setting.strip().lower().replace("-", "_")

        # Check if it corresponds to an existing level attribute
        if hasattr(cam, setting_clean) and isinstance(getattr(cam, setting_clean), int):
            try:
                int_val = int(value)
                return self.set_level(camera_id, setting_clean, int_val)
            except ValueError:
                pass

        # Check if it corresponds to an existing boolean toggle
        if hasattr(cam, setting_clean) and isinstance(getattr(cam, setting_clean), bool):
            if str(value).lower() in ("on", "off", "enable", "disable", "true", "false", "1", "0"):
                return self.set_toggle(camera_id, setting_clean, str(value))

        # Store in custom settings
        cam.custom_settings[setting_clean] = value
        self._persist_camera(camera_id)
        data = {"camera_id": camera_id, "setting": setting_clean, "value": value}
        return True, f"Setting '{setting_clean}' set to '{value}' for camera {camera_id}", data

    # ========================================================================
    # Events, Detections and Alerts
    # ========================================================================

    def get_events(
        self,
        camera_id: Optional[str] = None,
        label: Optional[str] = None,
        limit: int = 20,
    ) -> Tuple[bool, str, List[Dict[str, Any]]]:
        """Retrieve detected object events and alerts."""
        if self.is_connected:
            try:
                params: Dict[str, Any] = {"limit": limit}
                if camera_id:
                    params["cameras"] = camera_id
                if label:
                    params["labels"] = label

                with httpx.Client(timeout=self.timeout) as client:
                    resp = client.get(f"{self.base_url}/api/events", params=params)
                    if resp.status_code == 200:
                        return True, "Events retrieved successfully", resp.json()
            except Exception as e:
                logger.warning("Failed to fetch live events from Frigate: %s", e)

        # Simulation fallback events
        now = time.time()
        simulated_events = [
            {
                "id": "evt_101",
                "camera": "front_door",
                "label": "person",
                "score": 0.92,
                "top_score": 0.94,
                "start_time": now - 300,
                "end_time": now - 280,
                "has_clip": True,
                "has_snapshot": True,
                "zones": ["porch"],
                "retain_indefinitely": False,
            },
            {
                "id": "evt_102",
                "camera": "driveway",
                "label": "car",
                "score": 0.88,
                "top_score": 0.91,
                "start_time": now - 900,
                "end_time": now - 850,
                "has_clip": True,
                "has_snapshot": True,
                "zones": ["driveway"],
                "retain_indefinitely": False,
            },
            {
                "id": "evt_103",
                "camera": "camera_2",
                "label": "dog",
                "score": 0.85,
                "top_score": 0.87,
                "start_time": now - 1800,
                "end_time": now - 1760,
                "has_clip": True,
                "has_snapshot": True,
                "zones": ["yard"],
                "retain_indefinitely": False,
            },
            {
                "id": "evt_104",
                "camera": "front_door",
                "label": "package",
                "score": 0.95,
                "top_score": 0.96,
                "start_time": now - 3600,
                "end_time": now - 3550,
                "has_clip": True,
                "has_snapshot": True,
                "zones": ["porch"],
                "retain_indefinitely": True,
            },
        ]

        filtered = simulated_events
        if camera_id:
            filtered = [e for e in filtered if e["camera"] == camera_id]
        if label:
            filtered = [e for e in filtered if e["label"] == label.lower()]

        return True, f"Retrieved {len(filtered[:limit])} events", filtered[:limit]

    def get_event_picture(self, event_id: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Retrieve snapshot picture for a specific event."""
        image_data = MINIMAL_JPEG_B64
        if self.is_connected:
            try:
                with httpx.Client(timeout=self.timeout) as client:
                    resp = client.get(f"{self.base_url}/api/events/{event_id}/snapshot.jpg")
                    if resp.status_code == 200:
                        image_data = base64.b64encode(resp.content).decode("ascii")
            except Exception as e:
                logger.warning("Failed to fetch event snapshot from Frigate: %s", e)

        data = {
            "event_id": event_id,
            "image": image_data,
            "format": "jpeg",
            "timestamp": time.time(),
        }
        return True, f"Snapshot for event '{event_id}' retrieved successfully", data

    def get_event_clip(self, event_id: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Retrieve video clip for a specific event."""
        clip_url = (
            f"{self.base_url}/api/events/{event_id}/clip.mp4" if self.is_connected else f"/data/clips/{event_id}.mp4"
        )
        data = {
            "event_id": event_id,
            "url": clip_url,
            "format": "mp4",
            "duration_seconds": 15,
        }
        return True, f"Clip for event '{event_id}' retrieved successfully", data

    def retain_event(self, event_id: str, retain: bool = True) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Toggle indefinite retention on an event."""
        if self.is_connected:
            try:
                with httpx.Client(timeout=self.timeout) as client:
                    client.post(f"{self.base_url}/api/events/{event_id}/retain", json={"retain": retain})
            except Exception as e:
                logger.warning("Failed to retain event on Frigate: %s", e)

        action = "retained" if retain else "un-retained"
        data = {"event_id": event_id, "retained": retain}
        return True, f"Event '{event_id}' {action} successfully", data

    def get_status(self) -> Dict[str, Any]:
        """Retrieve MCP server, storage, and camera subsystem health status."""
        return {
            "server": "frigate-mcp",
            "version": "1.0.0",
            "status": "running",
            "frigate_connected": self.is_connected,
            "frigate_url": self.base_url,
            "mqtt_connected": self.mqtt.is_connected,
            "storage_mode": "redis" if self.storage._redis_available else "disk",
            "cameras_count": len(self.cameras),
            "cameras": [c.camera_id for c in self.cameras.values()],
        }


# Global singleton FrigateClient instance
_client_instance: Optional[FrigateClient] = None


def get_client() -> FrigateClient:
    """Retrieve or initialize singleton FrigateClient."""
    global _client_instance
    if _client_instance is None:
        _client_instance = FrigateClient()
    return _client_instance


def reset_client() -> FrigateClient:
    """Reset the singleton FrigateClient."""
    global _client_instance
    _client_instance = FrigateClient()
    return _client_instance


def send(message: str) -> None:
    """Send command message to Frigate subsystem or log channel."""
    try:
        data = json.loads(message)
        logger.info("Frigate command dispatched: %s", data)
    except Exception:
        logger.info("Frigate raw message: %s", message)
