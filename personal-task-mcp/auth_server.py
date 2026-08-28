"""Authenticated Personal Task MCP Server over Streamable HTTP."""

from __future__ import annotations

import os
import secrets

from mcp.server.auth.provider import AccessToken, TokenVerifier
from mcp.server.auth.settings import AuthSettings

from task_server import create_task_server


HOST = os.getenv("TASK_MCP_HOST", "0.0.0.0")
PORT = int(os.getenv("TASK_MCP_PORT", "8085"))
TOKEN = os.getenv("TASK_MCP_TOKEN")

if not TOKEN:
    raise RuntimeError(
        "Thiếu TASK_MCP_TOKEN. Hãy đặt biến môi trường trước khi chạy auth_server.py."
    )


class StaticTokenVerifier(TokenVerifier):
    def __init__(self, expected_token: str) -> None:
        self.expected_token = expected_token

    async def verify_token(self, token: str) -> AccessToken | None:
        if not secrets.compare_digest(token, self.expected_token):
            return None
        return AccessToken(
            token=token,
            client_id="personal-task-client",
            scopes=["tasks:read", "tasks:write"],
        )


base_url = f"http://localhost:{PORT}"
mcp = create_task_server(
    include_v2=True,
    token_verifier=StaticTokenVerifier(TOKEN),
    auth=AuthSettings(
        issuer_url=base_url,
        resource_server_url=base_url,
        required_scopes=["tasks:read"],
    ),
)


if __name__ == "__main__":
    mcp.run(transport="streamable-http", host=HOST, port=PORT)
