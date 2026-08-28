"""Personal Task MCP Server v2 over stdio."""

from task_server import create_task_server


mcp = create_task_server(include_v2=True)


if __name__ == "__main__":
    mcp.run(transport="stdio")
