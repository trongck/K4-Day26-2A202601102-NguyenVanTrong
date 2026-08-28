"""Authenticated Streamable HTTP client for the personal task server."""

from __future__ import annotations

import asyncio
import os

import httpx
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

from client_utils import tool_payload


SERVER_URL = os.getenv("TASK_MCP_URL", "http://localhost:8085/mcp")


async def main() -> None:
    token = os.getenv("TASK_MCP_TOKEN")
    if not token:
        raise RuntimeError("Thiếu TASK_MCP_TOKEN cho HTTP client")

    async with httpx.AsyncClient(
        headers={"Authorization": f"Bearer {token}"}
    ) as http_client:
        async with streamable_http_client(
            SERVER_URL, http_client=http_client
        ) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools = await session.list_tools()
                print("HTTP tools:", ", ".join(t.name for t in tools.tools))
                result = tool_payload(
                    await session.call_tool(
                        "search_tasks", {"status": "todo", "limit": 5}
                    )
                )
                print("HTTP result:", result)


if __name__ == "__main__":
    asyncio.run(main())
