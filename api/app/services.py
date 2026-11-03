from __future__ import annotations

from collections import Counter

from app.models import TaskCreateRequest, TaskResponse, TaskSummaryResponse
from app.repository import TaskRepository, TaskSummaryRecord
from app.security import Identity

HIGH_PRIORITY = "HIGH"
CLOSED_TASK_STATUSES = frozenset({"DONE", "ARCHIVED"})


class TaskService:
    def __init__(self, repository: TaskRepository) -> None:
        self._repository = repository

    def list_tasks(self, identity: Identity) -> list[TaskResponse]:
        tasks = self._repository.list_by_owner(identity["username"])
        return [
            TaskResponse(
                id=task.id,
                title=task.title,
                description=task.description,
                status=task.status,
                owner=task.owner,
                priority=task.priority,
                created_at=task.created_at,
            )
            for task in tasks
        ]

    def create_task(
        self,
        task: TaskCreateRequest,
        identity: Identity,
    ) -> TaskResponse:
        created_task = self._repository.create(task, identity["username"])
        return TaskResponse(
            id=created_task.id,
            title=created_task.title,
            description=created_task.description,
            status=created_task.status,
            owner=created_task.owner,
            priority=created_task.priority,
            created_at=created_task.created_at,
        )

    def summarize_tasks(self, identity: Identity) -> TaskSummaryResponse:
        rows = self._repository.list_summary_by_owner(identity["username"])
        return summarize_owner_tasks(identity["username"], rows)


def summarize_owner_tasks(
    owner: str,
    rows: list[TaskSummaryRecord],
) -> TaskSummaryResponse:
    by_status = Counter(row.status for row in rows)
    high_priority_open = sum(
        row.priority == HIGH_PRIORITY and row.status not in CLOSED_TASK_STATUSES
        for row in rows
    )
    return TaskSummaryResponse(
        owner=owner,
        total=len(rows),
        by_status=dict(by_status),
        high_priority_open=high_priority_open,
    )
