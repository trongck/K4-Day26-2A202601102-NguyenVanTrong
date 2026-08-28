"""HTTP entry point for the Personal Task MCP Server used by the ADK UI."""

from __future__ import annotations

import sys
from pathlib import Path

from dotenv import load_dotenv


SERVER_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SERVER_DIR.parent
# Project-local configuration must win over stale variables inherited from an
# already activated parent shell.
load_dotenv(SERVER_DIR / ".env", override=True)
sys.path.insert(0, str(PROJECT_DIR))

from auth_server import HOST, PORT, mcp  # noqa: E402


if __name__ == "__main__":
    print(f"Personal Task MCP Server: http://{HOST}:{PORT}/mcp")
    mcp.run(transport="streamable-http", host=HOST, port=PORT)
