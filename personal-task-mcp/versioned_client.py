"""New client: reads server://info, prefers v2, and falls back to v1."""

from __future__ import annotations

import argparse
import asyncio

from mcp import ClientSession
from mcp.client.stdio import stdio_client

from client_utils import resource_payload, server_parameters, tool_payload


async def run(script_name: str) -> None:
    async with stdio_client(server_parameters(script_name)) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Metadata is deliberately read before list_tools/tool selection.
            metadata = resource_payload(await session.read_resource("server://info"))
            print(
                f"Đã đọc server://info: {metadata['name']} v{metadata['version']}"
            )

            advertised_tools = metadata.get("tools", {})
            selected_tool = (
                "save_task_v2" if "save_task_v2" in advertised_tools else "save_task"
            )
            print(f"Tool được chọn: {selected_tool}")

            arguments = {
                "title": f"Kiểm thử client với {script_name}",
                "description": "Client đọc capability trước khi chọn tool",
                "status": "todo",
                "due_date": "2026-09-05",
            }
            if selected_tool == "save_task_v2":
                arguments.update({"priority": "high", "tags": ["MCP", "versioning"]})

            result = tool_payload(
                await session.call_tool(selected_tool, arguments)
            )
            print("Kết quả:", result)


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--legacy", action="store_true", help="Kết nối server v1 để thử fallback"
    )
    args = parser.parse_args()
    await run("legacy_server.py" if args.legacy else "server.py")


if __name__ == "__main__":
    asyncio.run(main())
