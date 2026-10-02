## Frigate-MCP 

Frigate-MCP is a project that integrates with Frigate to provide enhanced multi-camera processing capabilities via model context protocol (MCP).

It works by running as a docker container that can then access frigate services using the docker container and the frigate python library. This allows for seamless integration and management of multiple cameras within the Frigate ecosystem.

It can do things such as list available cameras, take pictures, record video clips, control camera settings, and manage multi-camera configurations. 

It returns a json response for all commands, providing structured information about the status and results of the requested operations and any returns. 

## JSON Response Example 

### Basic Response
```json
{
    "status": "success",
    "message": "Operation completed successfully",
    "data": null
}
```

### Returning an image
```json
{
    "status": "success",
    "message": "Image captured successfully",
    "status_code": 200,
    "data": {
        "camera_id": "camera_1",
        "image": "image_data"
    }
}
```

## Response Status Codes

Responses include a status code indicating the result of the operation. Common status codes are:

- `200`: Success
- `400`: Bad Request
- `401`: Unauthorized
- `404`: Not Found
- `500`: Internal Server Error
- `403`: Forbidden


### Start / Stop

#### Start Frigate-MCP
```bash
docker-compose up -d
```

#### Stop Frigate-MCP
```bash
docker-compose down
```

## Frigate MCP Commands

Frigate-mcp supports multiple commands for its MCP server which can be used to manage and interact with the multi-camera processing capabilities.

### Basic Commands 

command | description |
--- | --- |
frigate-mcp --help | Show help information
frigate-mcp --version | Show version information
frigate-mcp quit | Quit the MCP server
frigate-mcp status | Show the current status of the MCP server
frigate-mcp start | Start the MCP server
frigate-mcp stop | Stop the MCP server
frigate-mcp restart | Restart the MCP server
frigate-mcp help | Show help information

### Control

command | description |
--- | --- |
frigate-mcp list | list available cameras and camera_id's
frigate-mcp picture <camera_id> | take a picture from the specified camera
frigate-mcp clip <camera_id> | take a video clip from the specified camera
frigate-mcp record <camera_id> | start recording from the specified camera
frigate-mcp stop-record <camera_id> | stop recording from the specified camera
frigate-mcp pan <camera_id> left | pan the specified camera to the left
frigate-mcp pan <camera_id> right | pan the specified camera to the right
frigate-mcp tilt <camera_id> up | tilt the specified camera upwards
frigate-mcp tilt <camera_id> down | tilt the specified camera downwards
frigate-mcp zoom <camera_id> in | zoom the specified camera in
frigate-mcp zoom <camera_id> out | zoom the specified camera out
frigate-mcp focus <camera_id> | focus the specified camera
frigate-mcp auto-focus <camera_id> | enable auto-focus for the specified camera
frigate-mcp disable-auto-focus <camera_id> | disable auto-focus for the specified camera
frigate-mcp night-vision <camera_id> on | enable night vision for the specified camera
frigate-mcp night-vision <camera_id> off | disable night vision for the specified camera
frigate-mcp infrared <camera_id> on | enable infrared for the specified camera
frigate-mcp infrared <camera_id> off | disable infrared for the specified camera
frigate-mcp motion-detection <camera_id> on | enable motion detection for the specified camera
frigate-mcp motion-detection <camera_id> off | disable motion detection for the specified camera
frigate-mcp privacy-mode <camera_id> on | enable privacy mode for the specified camera
frigate-mcp privacy-mode <camera_id> off | disable privacy mode for the specified camera
frigate-mcp audio <camera_id> on | enable audio for the specified camera
frigate-mcp audio <camera_id> off | disable audio for the specified camera
frigate-mcp speaker <camera_id> on | enable speaker for the specified camera
frigate-mcp speaker <camera_id> off | disable speaker for the specified camera
frigate-mcp microphone <camera_id> on | enable microphone for the specified camera
frigate-mcp microphone <camera_id> off | disable microphone for the specified camera
frigate-mcp speaker-volume <camera_id> <level> | set the speaker volume for the specified camera (level: 0-100)
frigate-mcp microphone-volume <camera_id> <level> | set the microphone volume for the specified camera (level: 0-100)
frigate-mcp brightness <camera_id> <level> | set the brightness for the specified camera (level: 0-100)
frigate-mcp contrast <camera_id> <level> | set the contrast for the specified camera (level: 0-100)
frigate-mcp saturation <camera_id> <level> | set the saturation for the specified camera (level: 0-100)
frigate-mcp sharpness <camera_id> <level> | set the sharpness for the specified camera (level: 0-100)
frigate-mcp white-balance <camera_id> <level> | set the white balance for the specified camera (level: 0-100)
frigate-mcp exposure <camera_id> <level> | set the exposure for the specified camera (level: 0-100)
frigate-mcp gain <camera_id> <level> | set the gain for the specified camera (level: 0-100)
frigate-mcp hue <camera_id> <level> | set the hue for the specified camera (level: 0-100)
frigate-mcp gamma <camera_id> <level> | set the gamma for the specified camera (level: 0-100)
frigate-mcp backlight-compensation <camera_id> <level> | set the backlight compensation for the specified camera (level: 0-100)
frigate-mcp noise-reduction <camera_id> <level> | set the noise reduction for the specified camera (level: 0-100)
frigate-mcp sharpness <camera_id> <level> | set the sharpness for the specified camera (level: 0-100)
frigate-mcp settings <camera_id> | get the current settings for the specified camera
frigate-mcp set setting <camera_id> <setting> <value> | set the specified setting for the specified camera to the given value
frigate-mcp events [camera_id] | list detected object events and alerts
frigate-mcp event-picture <event_id> | retrieve snapshot image for a detected event
frigate-mcp event-clip <event_id> | retrieve video clip for a detected event
frigate-mcp retain-event <event_id> [true/false] | retain an event indefinitely

## Development

Ensure you have Python 3.12 installed, as it is required for the development environment.

1. Clone the repository:

```bash
git clone https://github.com/yourusername/frigate-mcp.git
cd frigate-mcp
```

2. Create and activate a virtual environment:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
```

3. Install dependencies and the package in editable mode:

```bash
pip install --no-cache-dir -r requirements.txt
pip install -e .
```

4. Run tests and linting:

```bash
pytest -v
ruff check .
ruff format --check .
```

## Running the MCP Server

### Stdio Transport (Claude Desktop / Cursor / Antigravity)

Run the server communicating over standard IO:

```bash
frigate-mcp serve --transport stdio
```

#### Claude Desktop Configuration
Add the following to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "frigate-mcp": {
      "command": "/path/to/frigate-mcp/.venv/bin/frigate-mcp",
      "args": ["serve", "--transport", "stdio"],
      "env": {
        "FRIGATE_URL": "http://localhost:5000"
      }
    }
  }
}
```

### SSE / HTTP Transport (Docker / Network)

Run the server as a background service or container listening on port 5000:

```bash
# Direct execution
frigate-mcp serve --transport sse --host 0.0.0.0 --port 5000

# Or using Docker Compose
docker-compose up -d
```

HTTP Endpoints:
- `GET /sse`: Server-Sent Events MCP endpoint
- `POST /messages`: MCP client messages endpoint
- `GET /health`: Health check endpoint
- `GET /status`: Server status endpoint
- `POST /command`: JSON command dispatch endpoint

## State Persistence & Caching

Frigate-MCP includes a dual-tier state persistence layer:
1. **Redis**: Automatically connects to the Redis service configured in `docker-compose.yml` (`REDIS_URL`).
2. **Disk Fallback**: Automatically saves state to `./data/cameras_state.json` (mounted as `/data` in Docker), ensuring settings persist across process restarts and multi-worker deployments.
