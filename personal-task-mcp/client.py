"""Old v1-style client: proves stdio discovery and backward compatibility."""

from __future__ import annotations

import asyncio

from mcp import ClientSession
from mcp.client.stdio import stdio_client

from client_utils import server_parameters, tool_payload


async def main() -> None:
    async with stdio_client(server_parameters("server.py")) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            names = [tool.name for tool in tools.tools]
            print("Tools được khám phá:", ", ".join(names))

            created = tool_payload(
                await session.call_tool(
                    "save_task",
                    {
                        "title": "Hoàn thành bài MCP",
                        "description": "Kiểm thử client v1 với dữ liệu SQLite thật",
                        "due_date": "2026-09-02",
                    },
                )
            )
            print("Đã tạo bằng v1:", created)

            updated = tool_payload(
                await session.call_tool(
                    "save_task",
                    {"task_id": created["id"], "status": "in_progress"},
                )
            )
            print("Đã cập nhật bằng v1:", updated)

            found = tool_payload(
                await session.call_tool(
                    "search_tasks",
                    {"keyword": "MCP", "status": "in_progress", "limit": 5},
                )
            )
            print("Kết quả tìm kiếm:", found)


if __name__ == "__main__":
    asyncio.run(main())
