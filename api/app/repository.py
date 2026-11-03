from __future__ import annotations

import sqlite3
from dataclasses import dataclass

from app.models import TaskCreateRequest

TASK_SELECT = """
    SELECT id, title, description, status, owner, priority, created_at
    FROM tasks
"""
SEED_TASKS = (
    (
        "Refactor login",
        "Separar responsabilidades en frontend",
        "TODO",
        "student",
        "HIGH",
    ),
    (
        "Review API",
        "Revisar seguridad de endpoints",
        "IN_PROGRESS",
        "student",
        "MEDIUM",
    ),
    ("Trainer notes", "Preparar retrospectiva", "TODO", "trainer", "LOW"),
)


@dataclass(frozen=True)
class TaskRecord:
    id: int
    title: str
    description: str
    status: str
    owner: str
    priority: str
    created_at: str


@dataclass(frozen=True)
class TaskSummaryRecord:
    status: str
    priority: str


class TaskRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def initialize(self) -> None:
        self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                status TEXT NOT NULL,
                owner TEXT NOT NULL,
                priority TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        task_count = self._connection.execute(
            "SELECT COUNT(*) AS total FROM tasks"
        ).fetchone()["total"]
        if task_count != 0:
            return

        self._connection.executemany(
            """
            INSERT INTO tasks(title, description, status, owner, priority, created_at)
            VALUES (?, ?, ?, ?, ?, datetime('now'))
            """,
            SEED_TASKS,
        )
        self._connection.commit()

    def list_by_owner(self, owner: str) -> list[TaskRecord]:
        rows = self._connection.execute(
            TASK_SELECT + " WHERE owner = ? ORDER BY id",
            (owner,),
        ).fetchall()
        return [self._task_from_row(row) for row in rows]

    def create(self, task: TaskCreateRequest, owner: str) -> TaskRecord:
        cursor = self._connection.execute(
            """
            INSERT INTO tasks(title, description, status, owner, priority, created_at)
            VALUES (?, ?, ?, ?, ?, datetime('now'))
            """,
            (task.title, task.description, task.status, owner, task.priority),
        )
        self._connection.commit()
        row = self._connection.execute(
            TASK_SELECT + " WHERE id = ?",
            (cursor.lastrowid,),
        ).fetchone()
        if row is None:
            raise RuntimeError("Inserted task could not be retrieved")
        return self._task_from_row(row)

    def list_summary_by_owner(self, owner: str) -> list[TaskSummaryRecord]:
        rows = self._connection.execute(
            "SELECT status, priority FROM tasks WHERE owner = ?",
            (owner,),
        ).fetchall()
        return [
            TaskSummaryRecord(status=row["status"], priority=row["priority"])
            for row in rows
        ]

    @staticmethod
    def _task_from_row(row: sqlite3.Row) -> TaskRecord:
        return TaskRecord(
            id=row["id"],
            title=row["title"],
            description=row["description"],
            status=row["status"],
            owner=row["owner"],
            priority=row["priority"],
            created_at=row["created_at"],
        )
