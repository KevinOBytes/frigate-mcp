# Frigate-MCP Feature Catalogue

Frigate-MCP exposes complete camera lifecycle management, live feeds, PTZ movement, image enhancement controls, and AI object detection alerts.

## 1. Discovery & Status
- **List Cameras**: Discover all cameras configured in Frigate or the local configuration file.
- **System Health**: Check connectivity to Frigate NVR, camera count, active PIDs, and runtime status.
- **Camera Settings**: Inspect all active settings, toggle states, and resolution/PTZ metadata for any camera.

## 2. Media Capture & Recording
- **Snapshots (`picture`)**: Capture immediate JPEG snapshot from any camera, returning base64 encoded payload and metadata.
- **Video Clips (`clip`)**: Trigger and retrieve short video clips from events.
- **Recording Controls (`record` / `stop-record`)**: Start and stop continuous 24/7 recording per camera.

## 3. Events, Alerts & Object Detection
- **Query Events (`events`)**: Retrieve object detection events filtered by camera, label (person, car, dog, package), or limit.
- **Event Snapshot (`event-picture`)**: Download high-resolution snapshot associated with a detected event.
- **Event Video Clip (`event-clip`)**: Download mp4 video clip recorded during a detected event.
- **Retain Event (`retain-event`)**: Mark an event to be retained indefinitely in Frigate storage.

## 4. Pan-Tilt-Zoom (PTZ) Controls
- **Pan**: Move camera `left` or `right` within -180° to +180° limits.
- **Tilt**: Adjust camera elevation `up` or `down` within -90° to +90° limits.
- **Zoom**: Optical / digital zoom `in` or `out` with 0.5x stepping (1.0x to 10.0x).
- **Focus**: Trigger instantaneous manual focus calibration.
- **Auto-Focus**: Enable or disable continuous autofocus tracking.

## 5. Operational Modes & Hardware Toggles
All toggles accept `'on'` / `'off'` states:
- `night-vision`: Night vision infrared cutoff switch.
- `infrared`: Auxiliary IR illuminators.
- `motion-detection`: On-device or Frigate software motion detection pipelines.
- `privacy-mode`: Shutter cover or stream blanking for privacy.
- `audio`: Audio stream capture toggle.
- `speaker`: Two-way speaker output toggle.
- `microphone`: Two-way microphone input toggle.

## 6. Image & Audio Tuning (0-100 Range)
Granular adjustments with boundary validation:
- `speaker-volume`: Audio playback volume (0-100).
- `microphone-volume`: Microphone gain level (0-100).
- `brightness`: Image luminance level (0-100).
- `contrast`: Dynamic contrast enhancement (0-100).
- `saturation`: Color vibrancy level (0-100).
- `sharpness`: Edge enhancement filter (0-100).
- `white-balance`: Color temperature calibration (0-100).
- `exposure`: Sensor shutter/exposure timing (0-100).
- `gain`: Sensor analog/digital gain (0-100).
- `hue`: Color spectrum rotation (0-100).
- `gamma`: Gamma correction curve (0-100).
- `backlight-compensation`: High dynamic range backlight compensation (0-100).
- `noise-reduction`: 2D/3D temporal noise reduction (0-100).

## 7. Persistence & Protocol Integrations
- **Dual-Tier Storage**: Redis and disk-backed state persistence for multi-worker and CLI durability.
- **MQTT Integration**: Real-time event publishing and topic subscriptions.
- **38 Registered MCP Tools**: Full symmetry between CLI commands and LLM agent tool calls.
- **MCP Resources**: `frigate://cameras`, `frigate://cameras/{camera_id}/settings`, `frigate://events`, `frigate://status`.
- **MCP Prompts**: Workflows for automated camera auditing and security sweeping.
- **Transports**: Native `stdio` and `SSE` support.
