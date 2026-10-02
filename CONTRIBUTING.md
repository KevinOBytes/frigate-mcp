# Contributing to Frigate-MCP

Thank you for your interest in improving Frigate-MCP! We welcome contributions, bug reports, and feature requests.

## Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/your-org/frigate-mcp.git
   cd frigate-mcp
   ```

2. Create a virtual environment and install dependencies:
   ```bash
   python3.12 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   pip install -e ".[dev]"
   ```

## Code Quality Standards

Before submitting a Pull Request, ensure all checks pass:

- **Linting**:
  ```bash
  ruff check .
  ```

- **Formatting**:
  ```bash
  ruff format --check .
  ```

- **Tests**:
  ```bash
  pytest -v
  ```

## Adding New Commands or Tools

1. If adding a camera setting or PTZ action, add it to `app/frigate.py` on the `CameraState` and `FrigateClient`.
2. Register the tool on `app/mcp_server.py` with comprehensive docstrings and types.
3. Add the CLI dispatch handling in `app/main.py`.
4. Add corresponding test cases in `tests/test_cli.py`, `tests/test_frigate.py`, or `tests/test_mcp_server.py`.
5. Update `docs/FEATURES.md` and `README.md`.
