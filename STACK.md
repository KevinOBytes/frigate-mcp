# Technology Stack & Tools

## Architecture
- **Language**: Python 3.12+ (CPython)
- **Protocol**: Model Context Protocol (MCP) using official Python `mcp` SDK (`mcp>=2.2.0`)
- **Web / Async Framework**: Starlette (`starlette>=0.27`), Uvicorn (`uvicorn>=0.31`), AnyIO (`anyio>=4.9`)
- **HTTP Client**: HTTPX (`httpx>=0.28`)
- **Validation & Serialization**: Pydantic v2 (`pydantic>=2.10`)
- **Configuration**: PyYAML (`pyyaml>=6.0`), Environment Variables (`python-dotenv`)
- **Containerization**: Docker & Docker Compose (Python 3.12-slim base)
- **Cache & Persistence**: Redis (`redis-py>=5.0.0`) & atomic disk JSON state caching
- **Messaging & PubSub**: MQTT (`paho-mqtt>=2.0.0`)
- **NVR Target**: Frigate NVR HTTP REST API / MQTT API with simulation engine fallback

## Development & Quality Tools
- **Linter & Formatter**: Ruff (`ruff`)
- **Test Framework**: Pytest (`pytest`)
- **Virtual Environment**: uv / venv
- **Packaging**: PEP 517 / `pyproject.toml` with `setuptools`

## Interfaces
- **MCP Server**: FastMCP server supporting `stdio` transport and `SSE` transport on port 5000.
- **CLI**: `frigate-mcp` command-line executable providing subcommands for all camera operations with standardized JSON output.
- **HTTP API**: Health check and command endpoints for Docker container runtime.
