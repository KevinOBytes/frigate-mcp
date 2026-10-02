# Frigate-MCP Requirements Specification

## 1. Functional Requirements

### 1.1 Command Interface & JSON Responses
- **FR-1.1**: The system must provide CLI subcommands for all camera operations and event queries documented in `README.md`.
- **FR-1.2**: All operations must return a strictly formatted JSON object containing:
  - `status`: String, either `"success"` or `"error"`.
  - `message`: Human-readable summary of the operation.
  - `status_code`: Integer HTTP status code matching standard semantics (`200`, `400`, `401`, `403`, `404`, `500`).
  - `data`: Object containing payload data or `null`.
- **FR-1.3**: Exit codes of CLI executions must reflect success (`0`) or failure (`1`).

### 1.2 Model Context Protocol Compliance
- **FR-2.1**: The system must implement the official Model Context Protocol (MCP) using Python `mcp` SDK v2+.
- **FR-2.2**: The server must support both `stdio` transport and `SSE` (Server-Sent Events) HTTP transport on port 5000.
- **FR-2.3**: The server must register tools for every camera capability, resources for cameras, events, and settings, and prompts for security workflows.

### 1.3 Frigate NVR Integration & Simulation Fallback
- **FR-3.1**: The client must query Frigate REST API when configured and reachable via `FRIGATE_URL`.
- **FR-3.2**: When no live Frigate instance is reachable, the client must automatically fall back to an internal simulation state store and event generator without throwing fatal connection errors.
- **FR-3.3**: Snapshot captures in simulation mode must return valid JPEG image data encoded in base64.

### 1.4 State Persistence & Durability
- **FR-4.1**: Camera settings, PTZ coordinates, and operational toggles must persist across distinct CLI command invocations and multi-worker server processes.
- **FR-4.2**: The system must support Redis caching when configured, with seamless fallback to disk storage in `FRIGATE_MCP_DATA`.

### 1.5 Real-time MQTT Integration
- **FR-5.1**: State changes and triggers must publish to Frigate MQTT topics when an MQTT broker is configured.

### 1.6 Input Validation
- **FR-6.1**: Level commands (`brightness`, `volume`, etc.) must strictly validate input to integers in the range `0` to `100` and return status code `400` on violation.
- **FR-6.2**: Toggle commands must validate states to `'on'` or `'off'` and return status code `400` on violation.
- **FR-6.3**: Non-existent cameras or event IDs must return status code `404`.

## 2. Non-Functional Requirements
- **NFR-1 (Performance)**: In-memory/local storage response times must be < 50ms per command.
- **NFR-2 (Reliability)**: Errors during live Frigate or MQTT communication must be caught gracefully and reported with structured error messages rather than unhandled tracebacks.
- **NFR-3 (Docker Compatibility)**: The application must package into a Docker image with clean health checks on port 5000.
- **NFR-4 (Quality Standards)**: Codebase must pass all Ruff linter checks, formatting checks, and 100% of automated Pytest suites.
