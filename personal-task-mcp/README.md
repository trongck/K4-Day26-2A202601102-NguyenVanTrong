# Personal Task MCP Server

MCP Server quản lý công việc cá nhân bằng dữ liệu SQLite thật. Server hỗ trợ
stdio để dùng với Claude Code, Streamable HTTP có Bearer Token, versioning và
resource `server://info` để client chọn capability phù hợp.

## 1. Use case

**Công việc hiện tại:** thêm, tìm kiếm và theo dõi trạng thái các công việc cá
nhân hằng ngày.

**Cách làm thủ công:** ghi công việc vào file hoặc ứng dụng ghi chú, tự tìm lại,
kiểm tra hạn hoàn thành và sửa trạng thái khi tiến độ thay đổi.

**Input:** tiêu đề, mô tả, hạn hoàn thành, trạng thái, từ khóa và mức ưu tiên.

**Output:** mã công việc, dữ liệu vừa tạo/cập nhật và danh sách công việc khớp
điều kiện tìm kiếm.

```text
User -> Claude Code -> MCP Client -> MCP Server -> SQLite
```

SQLite được tạo tại `data/tasks.db` khi tool được gọi lần đầu. File database
không được commit vào Git.

### Cấu trúc có giao diện

```text
personal-task-mcp/
├── mcp-server/                 # Streamable HTTP + Bearer Token
│   ├── server.py
│   ├── pyproject.toml
│   └── .env.example
├── mcp-client/                 # Google ADK Web
│   ├── task_agent/
│   │   ├── __init__.py
│   │   └── agent.py
│   ├── pyproject.toml
│   └── .env.example
├── task_server.py              # Tools dùng chung
├── database.py                 # SQLite
└── data/
```

## 2. Tools

### `save_task` — v1

Tạo task khi không truyền `task_id`; cập nhật task khi có `task_id`.

| Input | Kiểu | Bắt buộc | Ý nghĩa |
|---|---|---:|---|
| `title` | string/null | Khi tạo mới | Tiêu đề công việc |
| `task_id` | integer/null | Khi cập nhật | ID công việc |
| `description` | string/null | Không | Mô tả |
| `status` | string/null | Không | `todo`, `in_progress`, `done` |
| `due_date` | string/null | Không | Ngày hạn `YYYY-MM-DD` |

Output v1 giữ ổn định cho client cũ:

```json
{"id": 1, "status": "todo", "action": "created"}
```

### `search_tasks` — v1

Tìm task theo `keyword`, `status`, `due_before` và `limit`. Các bộ lọc đều
optional; `limit` từ 1 đến 100. Tool truy vấn SQLite bằng parameterized SQL.

```json
{
  "count": 1,
  "tasks": [
    {
      "id": 1,
      "title": "Hoàn thành bài MCP",
      "status": "in_progress",
      "due_date": "2026-09-02"
    }
  ]
}
```

### `save_task_v2` — v2

Giữ toàn bộ input v1 và thêm hai optional parameters:

- `priority`: `low`, `medium`, `high`.
- `tags`: danh sách tối đa 20 nhãn.

Output v2 vẫn giữ `id`, `status`, `action` và bổ sung toàn bộ task cùng
`api_version`, `priority`, `tags`, `created_at`, `updated_at`.

## 3. Cài đặt

Từ thư mục gốc repository:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r personal-task-mcp\requirements.txt
```

## 4. Chạy stdio và kiểm thử client cũ

MCP stdio server thường do client tự khởi động; không cần mở server ở terminal
riêng. Chạy client v1:

```powershell
python personal-task-mcp\client.py
```

Client sẽ khám phá tools, gọi `save_task` để tạo/cập nhật và gọi
`search_tasks` để đọc dữ liệu vừa ghi trong SQLite.

## 5. Đăng ký với Claude Code

Repository có sẵn file `.mcp.json` ở thư mục gốc với project-scoped server
`personal-task-manager`. Mở Claude Code từ thư mục gốc repository, chấp nhận
server của project khi được hỏi, rồi kiểm tra:

```text
/mcp
```

`.mcp.json` dùng `uv` và đường dẫn tương đối, vì vậy không chứa đường dẫn riêng
của máy tác giả. Máy chạy cần cài `uv`. Có thể đăng ký lại bằng Claude Code CLI:

```powershell
claude mcp add personal-task-manager --scope project -- uv run `
  --project personal-task-mcp/mcp-server `
  python personal-task-mcp/server.py
```

Các câu hỏi tự nhiên để thử agent tự chọn tool:

```text
Tạo công việc hoàn thành bài MCP, hạn ngày 2 tháng 9 năm 2026.

Chuyển công việc số 1 sang trạng thái đang thực hiện.

Tìm tối đa 5 công việc đang thực hiện có chứa từ MCP.

Đánh dấu công việc số 1 là hoàn thành rồi kiểm tra lại trạng thái.
```

Không yêu cầu Claude gọi tên tool; mục tiêu là để agent tự quyết định.

## 6. Streamable HTTP và Authentication

Server không có token mặc định và sẽ từ chối khởi động nếu thiếu biến môi
trường `TASK_MCP_TOKEN`.

Terminal 1:

```powershell
$env:TASK_MCP_TOKEN="thay-bang-token-dai-ngau-nhien"
python personal-task-mcp\auth_server.py
```

Server mặc định bind `0.0.0.0:8085`, endpoint:

```text
http://localhost:8085/mcp
```

Terminal 2, dùng đúng token:

```powershell
$env:TASK_MCP_TOKEN="thay-bang-token-dai-ngau-nhien"
python personal-task-mcp\http_client.py
```

Chạy đủ ba trường hợp auth:

```powershell
$env:TASK_MCP_TOKEN="thay-bang-token-dai-ngau-nhien"
python personal-task-mcp\auth_test_client.py
```

Kết quả mong đợi:

```text
Token đúng: ALLOWED
Thiếu token: HTTP 401
Token sai: HTTP 401
Authentication test passed
```

Nếu cổng 8085 đang được dùng, đặt cùng một port cho server và client:

```powershell
$env:TASK_MCP_PORT="8086"
$env:TASK_MCP_URL="http://localhost:8086/mcp"
```

### Chạy bằng hai project `mcp-server` và `mcp-client` có giao diện

Weather Lab đang dùng cổng 8085, vì vậy ví dụ giao diện dùng cổng 8086.

Tạo file `personal-task-mcp/mcp-server/.env`:

```env
TASK_MCP_TOKEN=task-token-abc123
TASK_MCP_HOST=0.0.0.0
TASK_MCP_PORT=8086
```

Terminal 1:

```powershell
cd personal-task-mcp\mcp-server
uv sync
uv run python server.py
```

Tạo file `personal-task-mcp/mcp-client/.env`:

```env
GOOGLE_API_KEY=YOUR_GOOGLE_API_KEY
TASK_MCP_TOKEN=task-token-abc123
TASK_MCP_URL=http://localhost:8086/mcp
TASK_AGENT_MODEL=gemini-2.5-flash
```

`TASK_MCP_TOKEN` ở hai file phải giống nhau.

Terminal 2:

```powershell
cd personal-task-mcp\mcp-client
uv sync
uv run python verify_connection.py
uv run adk web
```

Mở `http://localhost:8000`, chọn `task_agent`, sau đó thử:

```text
Tạo công việc hoàn thành bài MCP, hạn ngày 2 tháng 9 năm 2026,
ưu tiên cao và gắn nhãn AI.

Tìm các công việc chưa hoàn thành có chứa từ MCP.
```

Để thử trong LAN, giữ host `0.0.0.0`, cho phép port qua firewall và dùng
`http://<LAN-IP>:8085/mcp`. Chỉ mở mạng khi hiểu rõ phạm vi truy cập và dùng
token thử nghiệm riêng.

## 7. Versioning và backward compatibility

`server://info` trả metadata JSON:

```json
{
  "name": "personal-task-manager",
  "version": "2.0.0",
  "tools": {
    "save_task": {"version": "1.0.0", "deprecated": false},
    "search_tasks": {"version": "1.0.0", "deprecated": false},
    "save_task_v2": {"version": "2.0.0", "deprecated": false}
  },
  "capabilities": {"priority": true, "tags": true}
}
```

Client mới đọc resource trước khi chọn tool:

```powershell
# Server v2: client chọn save_task_v2
python personal-task-mcp\versioned_client.py

# Server v1: không có v2, client fallback save_task
python personal-task-mcp\versioned_client.py --legacy
```

Client cũ trong `client.py` chỉ gọi v1 và vẫn hoạt động với server v2.

## 8. Kiểm thử tự động

```powershell
python -m unittest discover -s personal-task-mcp\tests -v
```

Test bao phủ tạo/cập nhật/tìm kiếm SQLite, dữ liệu v2, input sai và task không
tồn tại.

## 9. Biến môi trường

| Biến | Mặc định | Công dụng |
|---|---|---|
| `TASK_MCP_TOKEN` | Không có | Bearer token bắt buộc cho HTTP server/client |
| `TASK_MCP_HOST` | `0.0.0.0` | Host HTTP server |
| `TASK_MCP_PORT` | `8085` | Port HTTP server |
| `TASK_MCP_URL` | `http://localhost:8085/mcp` | URL của HTTP client |
| `TASK_DB_PATH` | `data/tasks.db` | Database path tùy chọn |

Không commit `.env`, token thật hoặc `data/tasks.db`. Nếu secret từng được push,
cần revoke/rotate secret; chỉ xóa khỏi commit mới là chưa đủ.

## 10. Xử lý lỗi thường gặp

- Claude Code không thấy server: kiểm tra `.mcp.json`, đường dẫn Python/script,
  working directory, sau đó restart/reload và dùng `/mcp`.
- Thấy server nhưng không thấy tool: kiểm tra server import thành công và các
  hàm đã có `@mcp.tool()`.
- HTTP không kết nối: kiểm tra host, port, `/mcp`, firewall và server đang chạy.
- Token đúng vẫn bị từ chối: header phải là `Authorization: Bearer <TOKEN>`.
- Token nào cũng gọi được: kiểm tra `TokenVerifier` thực sự được truyền vào
  server; `auth_test_client.py` phải từ chối missing/invalid.

## 11. Đối chiếu yêu cầu bài làm

Quy ước:

- `[x]`: đã được kiểm tra bằng script/client trong repository.
- `[~]`: chưa kiểm tra đúng client được rubric chỉ định, hoặc là phần tùy chọn.
- `[ ]`: chưa thực hiện.

### Bài Dễ

- [x] MCP Server khởi động được qua stdio.
- [x] Có hai tool nghiệp vụ v1 tự xây: `save_task`, `search_tasks`.
- [x] Tool giải quyết việc tạo, cập nhật, tìm và theo dõi công việc cá nhân.
- [x] Tool đọc/ghi SQLite thật, không trả dữ liệu hard-code vô nghĩa.
- [x] Google ADK nhận ra MCP Server qua Streamable HTTP.
- [x] Google ADK nhìn thấy `save_task`, `save_task_v2`, `search_tasks` và gọi
  được tools từ giao diện Web.
- [~] Claude Code chưa được kiểm thử vì môi trường hiện tại không có Claude
  Code. Repository vẫn có `.mcp.json` và hướng dẫn đăng ký nếu rubric bắt buộc
  đúng client này.
- [x] Tool nhận đúng arguments; test bao phủ title, task ID, status, due date,
  priority, tags và các input không hợp lệ.
- [x] Tool trả dữ liệu đúng và dữ liệu tồn tại trong SQLite sau khi server dừng.
- [x] Đã kiểm thử bằng câu hỏi tự nhiên trên ADK Web; agent tự quyết định chọn
  tool và tool hoạt động bình thường, không yêu cầu người dùng gọi tên tool.

Câu kiểm tra tự nhiên đề xuất:

```text
Tạo công việc hoàn thành báo cáo MCP, hạn ngày 5 tháng 9 năm 2026,
ưu tiên cao và gắn nhãn Day26.

Tìm tối đa 5 công việc chưa hoàn thành có chứa từ MCP.
```

### Bài Trung bình

- [x] Server chạy bằng Streamable HTTP, bind `0.0.0.0`.
- [x] MCP client và Google ADK kết nối được qua HTTP.
- [x] Authentication được bật bằng `TokenVerifier`.
- [x] Token hợp lệ gọi được tool.
- [x] Thiếu token bị từ chối bằng HTTP 401.
- [x] Token sai bị từ chối bằng HTTP 401.
- [ ] Truy cập từ máy khác trong LAN chưa được thực hiện; đây là phần tùy điều kiện.

### Bài Khó

- [x] Có thay đổi thật: `save_task_v2` thêm `priority`, `tags` và response chi tiết.
- [x] Client cũ vẫn gọi `save_task` v1 trên server v2.
- [x] Client mới dùng được `save_task_v2`.
- [x] Có resource `server://info`.
- [x] `server://info` chứa version, tool metadata và capabilities.
- [x] Client mới đọc metadata trước khi chọn tool.
- [x] Client mới fallback về `save_task` khi kết nối server v1.

## 12. Bằng chứng kiểm tra có thể tái hiện

### Database, stdio, client cũ và input/output

```powershell
python -m unittest discover -s personal-task-mcp\tests -v
python personal-task-mcp\client.py
```

Kết quả đã xác minh: 4/4 tests đạt; server công bố đủ tools; client tạo task,
chuyển trạng thái sang `in_progress` và tìm lại đúng bản ghi vừa lưu.

### Versioning và fallback

```powershell
python personal-task-mcp\versioned_client.py
python personal-task-mcp\versioned_client.py --legacy
```

Kết quả đã xác minh:

```text
server v2 -> chọn save_task_v2
server v1 -> fallback save_task
```

### HTTP và Authentication

Khi HTTP server đang chạy, thực hiện:

```powershell
python personal-task-mcp\auth_test_client.py
python personal-task-mcp\http_client.py
```

Kết quả đã xác minh:

```text
Token đúng: ALLOWED
Thiếu token: HTTP 401
Token sai: HTTP 401
Authentication test passed
```

### Google ADK MCP Client

```powershell
cd personal-task-mcp\mcp-client
uv run python verify_connection.py
```

Kết quả đã xác minh:

```text
ADK nhìn thấy tools: save_task, save_task_v2, search_tasks
ADK MCP connection: PASS
```

Đã kiểm thử thêm trên giao diện `http://localhost:8000`: người dùng nhập yêu
cầu bằng ngôn ngữ tự nhiên, ADK tự chọn MCP tool, truyền arguments và trả kết
quả từ SQLite thành công. Đây là MCP Client được dùng để thay thế Claude Code
trong môi trường hiện tại.

## 13. Checklist trước khi nộp

- [x] Có source code MCP Server tự xây.
- [x] Có ít nhất hai MCP tools nghiệp vụ.
- [x] README mô tả use case và input/output của tools.
- [x] README hướng dẫn cài đặt, chạy stdio, HTTP và ADK Web.
- [x] Có hướng dẫn đăng ký và kiểm tra trong Claude Code.
- [x] Có script/test làm bằng chứng tool hoạt động.
- [x] Có Streamable HTTP và Bearer Token authentication.
- [x] Có hướng dẫn test token đúng, sai và thiếu.
- [x] Có versioning, client cũ, client mới, fallback và `server://info`.
- [x] `.env`, database và private key được ignore.
- [x] Đã chạy câu hỏi tự nhiên bằng Google ADK Web và tool hoạt động bình thường.
- [~] Nếu giảng viên bắt buộc đúng Claude Code, cần xin chấp nhận Google ADK
  thay thế hoặc kiểm thử bổ sung trên máy có Claude Code.
- [ ] Push commit cuối lên GitHub cá nhân và nộp link repository.

Không đưa API key, access token, password, private key, secret hoặc `.env` thật
lên repository. Chỉ các file `.env.example` chứa placeholder được phép commit.
