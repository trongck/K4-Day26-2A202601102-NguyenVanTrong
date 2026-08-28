"""SQLite persistence and validation for the personal task MCP server."""

from __future__ import annotations

import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Iterator


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DB_PATH = BASE_DIR / "data" / "tasks.db"
VALID_STATUSES = {"todo", "in_progress", "done"}
VALID_PRIORITIES = {"low", "medium", "high"}


def database_path() -> Path:
    """Return the configured database path and keep it inside an explicit location."""
    configured = os.getenv("TASK_DB_PATH")
    return Path(configured).resolve() if configured else DEFAULT_DB_PATH


@contextmanager
def connect() -> Iterator[sqlite3.Connection]:
    path = database_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def initialize_database() -> None:
    with connect() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                status TEXT NOT NULL DEFAULT 'todo',
                due_date TEXT,
                priority TEXT NOT NULL DEFAULT 'medium',
                tags TEXT NOT NULL DEFAULT '[]',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )


def _validate_status(status: str | None, *, default: str | None = None) -> str | None:
    value = default if status is None else status.strip().lower()
    if value is not None and value not in VALID_STATUSES:
        raise ValueError("status phải là: todo, in_progress hoặc done")
    return value


def _validate_priority(priority: str | None, *, default: str | None = None) -> str | None:
    value = default if priority is None else priority.strip().lower()
    if value is not None and value not in VALID_PRIORITIES:
        raise ValueError("priority phải là: low, medium hoặc high")
    return value


def _validate_date(value: str | None, field_name: str) -> str | None:
    if value is None or value == "":
        return None
    try:
        date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} phải có định dạng YYYY-MM-DD") from exc
    return value


def _normalize_tags(tags: list[str] | None) -> list[str] | None:
    if tags is None:
        return None
    cleaned = list(dict.fromkeys(tag.strip() for tag in tags if tag.strip()))
    if len(cleaned) > 20:
        raise ValueError("tags không được vượt quá 20 phần tử")
    return cleaned


def _row_to_task(row: sqlite3.Row) -> dict[str, Any]:
    task = dict(row)
    task["tags"] = json.loads(task["tags"])
    return task


def get_task(task_id: int) -> dict[str, Any]:
    initialize_database()
    with connect() as connection:
        row = connection.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    if row is None:
        raise ValueError(f"Không tìm thấy công việc có id={task_id}")
    return _row_to_task(row)


def save_task_record(
    *,
    title: str | None = None,
    task_id: int | None = None,
    description: str | None = None,
    status: str | None = None,
    due_date: str | None = None,
    priority: str | None = None,
    tags: list[str] | None = None,
) -> tuple[dict[str, Any], str]:
    """Create a task when task_id is absent, otherwise update provided fields."""
    initialize_database()
    due_date = _validate_date(due_date, "due_date")
    tags = _normalize_tags(tags)
    now = datetime.now(timezone.utc).isoformat()

    with connect() as connection:
        if task_id is None:
            if not title or not title.strip():
                raise ValueError("title là bắt buộc khi tạo công việc mới")
            normalized_status = _validate_status(status, default="todo")
            normalized_priority = _validate_priority(priority, default="medium")
            cursor = connection.execute(
                """
                INSERT INTO tasks
                    (title, description, status, due_date, priority, tags, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    title.strip(),
                    description,
                    normalized_status,
                    due_date,
                    normalized_priority,
                    json.dumps(tags or [], ensure_ascii=False),
                    now,
                    now,
                ),
            )
            task_id = int(cursor.lastrowid)
            action = "created"
        else:
            existing = connection.execute(
                "SELECT id FROM tasks WHERE id = ?", (task_id,)
            ).fetchone()
            if existing is None:
                raise ValueError(f"Không tìm thấy công việc có id={task_id}")

            updates: list[str] = []
            values: list[Any] = []
            if title is not None:
                if not title.strip():
                    raise ValueError("title không được để trống")
                updates.append("title = ?")
                values.append(title.strip())
            if description is not None:
                updates.append("description = ?")
                values.append(description)
            if status is not None:
                updates.append("status = ?")
                values.append(_validate_status(status))
            if due_date is not None:
                updates.append("due_date = ?")
                values.append(due_date)
            if priority is not None:
                updates.append("priority = ?")
                values.append(_validate_priority(priority))
            if tags is not None:
                updates.append("tags = ?")
                values.append(json.dumps(tags, ensure_ascii=False))
            if not updates:
                raise ValueError("Cần cung cấp ít nhất một trường để cập nhật")

            updates.append("updated_at = ?")
            values.extend([now, task_id])
            connection.execute(
                f"UPDATE tasks SET {', '.join(updates)} WHERE id = ?", values
            )
            action = "updated"

    return get_task(task_id), action


def search_task_records(
    *,
    keyword: str | None = None,
    status: str | None = None,
    due_before: str | None = None,
    limit: int = 20,
) -> list[dict[str, Any]]:
    initialize_database()
    if not 1 <= limit <= 100:
        raise ValueError("limit phải nằm trong khoảng 1-100")
    normalized_status = _validate_status(status)
    due_before = _validate_date(due_before, "due_before")

    clauses: list[str] = []
    values: list[Any] = []
    if keyword and keyword.strip():
        clauses.append("(LOWER(title) LIKE ? OR LOWER(COALESCE(description, '')) LIKE ?)")
        pattern = f"%{keyword.strip().lower()}%"
        values.extend([pattern, pattern])
    if normalized_status:
        clauses.append("status = ?")
        values.append(normalized_status)
    if due_before:
        clauses.append("due_date IS NOT NULL AND due_date <= ?")
        values.append(due_before)

    where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
    values.append(limit)
    query = f"SELECT * FROM tasks{where} ORDER BY updated_at DESC, id DESC LIMIT ?"
    with connect() as connection:
        rows = connection.execute(query, values).fetchall()
    return [_row_to_task(row) for row in rows]
