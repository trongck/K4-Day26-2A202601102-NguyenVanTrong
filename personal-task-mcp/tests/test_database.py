from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
import sys

sys.path.insert(0, str(PROJECT_DIR))

from database import save_task_record, search_task_records


class TaskDatabaseTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        os.environ["TASK_DB_PATH"] = str(Path(self.temp_dir.name) / "tasks.db")

    def tearDown(self) -> None:
        os.environ.pop("TASK_DB_PATH", None)
        self.temp_dir.cleanup()

    def test_create_update_and_search_real_sqlite_data(self) -> None:
        task, action = save_task_record(
            title="Hoàn thành bài MCP",
            description="Dữ liệu lưu thật trong SQLite",
            due_date="2026-09-02",
        )
        self.assertEqual(action, "created")
        self.assertEqual(task["status"], "todo")

        updated, action = save_task_record(
            task_id=task["id"], status="in_progress"
        )
        self.assertEqual(action, "updated")
        self.assertEqual(updated["status"], "in_progress")

        found = search_task_records(keyword="mcp", status="in_progress", limit=5)
        self.assertEqual([item["id"] for item in found], [task["id"]])

    def test_v2_fields_are_persisted(self) -> None:
        task, _ = save_task_record(
            title="Task ưu tiên",
            priority="high",
            tags=["MCP", "AI"],
        )
        self.assertEqual(task["priority"], "high")
        self.assertEqual(task["tags"], ["MCP", "AI"])

    def test_invalid_inputs_are_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "title"):
            save_task_record()
        with self.assertRaisesRegex(ValueError, "status"):
            save_task_record(title="Sai trạng thái", status="invalid")
        with self.assertRaisesRegex(ValueError, "YYYY-MM-DD"):
            save_task_record(title="Sai ngày", due_date="02/09/2026")
        with self.assertRaisesRegex(ValueError, "1-100"):
            search_task_records(limit=0)

    def test_missing_task_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "Không tìm thấy"):
            save_task_record(task_id=999, status="done")


if __name__ == "__main__":
    unittest.main()
