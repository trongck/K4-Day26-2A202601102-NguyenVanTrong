"""Google ADK agent that consumes Personal Task tools over MCP HTTP."""

from __future__ import annotations

import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from google.adk import Agent
from google.adk.tools.mcp_tool.mcp_toolset import (
    McpToolset,
    StreamableHTTPConnectionParams,
)


CLIENT_DIR = Path(__file__).resolve().parents[1]
# Keep server and client deterministic even when the parent PowerShell session
# still contains TASK_MCP_TOKEN/TASK_MCP_URL from an earlier exercise.
load_dotenv(CLIENT_DIR / ".env", override=True)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MCP_SERVER_URL = os.getenv("TASK_MCP_URL", "http://localhost:8086/mcp")
MCP_TOKEN = os.getenv("TASK_MCP_TOKEN")
MODEL = os.getenv("TASK_AGENT_MODEL", "gemini-2.5-flash")

if not MCP_TOKEN:
    raise RuntimeError(
        "Thiếu TASK_MCP_TOKEN trong mcp-client/.env. "
        "Token phải giống mcp-server/.env."
    )

logger.info("Connecting task agent to MCP server: %s", MCP_SERVER_URL)

connection_params = StreamableHTTPConnectionParams(
    url=MCP_SERVER_URL,
    headers={"Authorization": f"Bearer {MCP_TOKEN}"},
    timeout=30.0,
    sse_read_timeout=300.0,
)

task_tools = McpToolset(connection_params=connection_params)

root_agent = Agent(
    name="personal_task_agent",
    model=MODEL,
    description="Trợ lý quản lý công việc cá nhân bằng MCP tools và SQLite.",
    instruction=(
        "Bạn là trợ lý quản lý công việc cá nhân và trả lời bằng tiếng Việt. "
        "Khi người dùng muốn tạo, cập nhật, hoàn thành, tìm hoặc liệt kê công "
        "việc, hãy tự chọn MCP tool phù hợp; không giả lập kết quả. "
        "Ưu tiên save_task_v2 khi cần priority hoặc tags. "
        "Nếu yêu cầu còn thiếu dữ liệu bắt buộc thì hỏi ngắn gọn. "
        "Sau khi gọi tool, tóm tắt ID, trạng thái và hạn hoàn thành rõ ràng."
    ),
    tools=[task_tools],
)
