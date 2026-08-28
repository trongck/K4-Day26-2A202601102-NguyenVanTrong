# Personal Task Agent — Google ADK Web

Giao diện chat Google ADK kết nối tới Personal Task MCP Server qua Streamable
HTTP và gửi `Authorization: Bearer <TOKEN>` trong mọi request.

## Chạy

Tạo `.env` từ `.env.example`, điền `GOOGLE_API_KEY`, token giống server và URL:

```env
GOOGLE_API_KEY=your-google-key
TASK_MCP_TOKEN=your-shared-task-token
TASK_MCP_URL=http://localhost:8086/mcp
TASK_AGENT_MODEL=gemini-2.5-flash
```

Sau khi MCP Server đã chạy:

```powershell
uv sync
uv run python verify_connection.py
uv run adk web
```

Mở `http://localhost:8000`, chọn `task_agent` và nhập yêu cầu tự nhiên.
