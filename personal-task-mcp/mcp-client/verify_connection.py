"""Verify that Google ADK discovers tools from the authenticated MCP server."""

from __future__ import annotations

import asyncio
import sys

from task_agent.agent import MCP_SERVER_URL, task_tools


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


async def main() -> None:
    try:
        tools = await task_tools.get_tools()
        names = [tool.name for tool in tools]
        print(f"MCP Server: {MCP_SERVER_URL}")
        print("ADK nhìn thấy tools:", ", ".join(names))
        required = {"save_task", "search_tasks", "save_task_v2"}
        missing = required.difference(names)
        if missing:
            raise RuntimeError(f"Thiếu tools: {sorted(missing)}")
        print("ADK MCP connection: PASS")
    finally:
        await task_tools.close()


if __name__ == "__main__":
    asyncio.run(main())
