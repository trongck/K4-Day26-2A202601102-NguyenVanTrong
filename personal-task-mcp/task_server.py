"""Factory shared by stdio, authenticated HTTP, and legacy MCP servers."""

from __future__ import annotations

import json
from typing import Any

from mcp.server.auth.provider import TokenVerifier
from mcp.server.auth.settings import AuthSettings
from mcp.server.mcpserver import MCPServer

from database import save_task_record, search_task_records


def create_task_server(
    *,
    include_v2: bool = True,
    token_verifier: TokenVerifier | None = None,
    auth: AuthSettings | None = None,
) -> MCPServer:
    server_version = "2.0.0" if include_v2 else "1.0.0"
    mcp = MCPServer(
        "personal-task-manager",
        version=server_version,
        token_verifier=token_verifier,
        auth=auth,
    )

    @mcp.tool()
    def save_task(
        title: str | None = None,
        task_id: int | None = None,
        description: str | None = None,
        status: str | None = None,
        due_date: str | None = None,
    ) -> dict[str, Any]:
        """Tạo công việc mới hoặc cập nhật công việc theo task_id.

        Khi tạo mới, hãy truyền title và bỏ qua task_id. Khi cập nhật, truyền
        task_id cùng những trường cần đổi. status nhận todo, in_progress hoặc done.
        due_date dùng định dạng YYYY-MM-DD.
        """
        task, action = save_task_record(
            title=title,
            task_id=task_id,
            description=description,
            status=status,
            due_date=due_date,
        )
        # Response v1 intentionally stays small for old clients.
        return {"id": task["id"], "status": task["status"], "action": action}

    @mcp.tool()
    def search_tasks(
        keyword: str | None = None,
        status: str | None = None,
        due_before: str | None = None,
        limit: int = 20,
    ) -> dict[str, Any]:
        """Tìm công việc theo từ khóa, trạng thái hoặc hạn hoàn thành.

        Tất cả bộ lọc đều optional. status nhận todo, in_progress hoặc done;
        due_before dùng YYYY-MM-DD; limit nằm trong khoảng 1-100.
        """
        tasks = search_task_records(
            keyword=keyword,
            status=status,
            due_before=due_before,
            limit=limit,
        )
        return {"count": len(tasks), "tasks": tasks}

    if include_v2:

        @mcp.tool()
        def save_task_v2(
            title: str | None = None,
            task_id: int | None = None,
            description: str | None = None,
            status: str | None = None,
            due_date: str | None = None,
            priority: str | None = None,
            tags: list[str] | None = None,
        ) -> dict[str, Any]:
            """Tạo/cập nhật task v2 với priority, tags và response chi tiết.

            priority nhận low, medium hoặc high. Các tham số mới đều optional
            để giữ khả năng tương thích với cách gọi cũ.
            """
            task, action = save_task_record(
                title=title,
                task_id=task_id,
                description=description,
                status=status,
                due_date=due_date,
                priority=priority,
                tags=tags,
            )
            return {**task, "action": action, "api_version": "2.0.0"}

    @mcp.resource("server://info", mime_type="application/json")
    def server_info() -> str:
        """Công bố version và capability để client chọn tool phù hợp."""
        tools: dict[str, dict[str, Any]] = {
            "save_task": {"version": "1.0.0", "deprecated": False},
            "search_tasks": {"version": "1.0.0", "deprecated": False},
        }
        if include_v2:
            tools["save_task_v2"] = {"version": "2.0.0", "deprecated": False}
        return json.dumps(
            {
                "name": "personal-task-manager",
                "version": server_version,
                "tools": tools,
                "capabilities": {
                    "priority": include_v2,
                    "tags": include_v2,
                },
            },
            ensure_ascii=False,
        )

    return mcp
