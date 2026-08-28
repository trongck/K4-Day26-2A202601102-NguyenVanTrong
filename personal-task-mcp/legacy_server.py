"""Version 1 server used to prove the new client can fall back."""

from task_server import create_task_server


mcp = create_task_server(include_v2=False)


if __name__ == "__main__":
    mcp.run(transport="stdio")
