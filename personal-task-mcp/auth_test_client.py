"""Verify valid, missing, and invalid bearer-token behavior."""

from __future__ import annotations

import asyncio
import os

import httpx
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

from client_utils import exception_summary


SERVER_URL = os.getenv("TASK_MCP_URL", "http://localhost:8085/mcp")


async def probe(label: str, token: str | None) -> bool:
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    try:
        async with httpx.AsyncClient(headers=headers) as http_client:
            async with streamable_http_client(
                SERVER_URL, http_client=http_client
            ) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    await session.list_tools()
        print(f"{label}: ALLOWED")
        return True
    except BaseException as exc:
        print(f"{label}: REJECTED ({exception_summary(exc)})")
        return False


async def rejection_status(label: str, token: str | None) -> int:
    """Send an initialize request to expose the HTTP auth status directly."""
    headers = {
        "Accept": "application/json, text/event-stream",
        "Content-Type": "application/json",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2025-06-18",
            "capabilities": {},
            "clientInfo": {"name": "auth-probe", "version": "1.0"},
        },
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(SERVER_URL, headers=headers, json=body)
    print(f"{label}: HTTP {response.status_code}")
    return response.status_code


async def main() -> None:
    valid_token = os.getenv("TASK_MCP_TOKEN")
    if not valid_token:
        raise RuntimeError("Thiếu TASK_MCP_TOKEN để chạy auth test")

    valid = await probe("Token đúng", valid_token)
    missing_status = await rejection_status("Thiếu token", None)
    invalid_status = await rejection_status("Token sai", f"invalid-{valid_token}")

    if not valid or missing_status not in {401, 403} or invalid_status not in {401, 403}:
        raise SystemExit("Authentication test failed")
    print("Authentication test passed")


if __name__ == "__main__":
    asyncio.run(main())
