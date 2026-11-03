from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, File, Query, UploadFile

from app.health_service import get_backend_health
from app.models import (
    BackendHealthResponse,
    RequirementUploadResponse,
    TaskCreateRequest,
    TaskResponse,
    TaskSummaryResponse,
)
from app.security import Identity, get_identity
from app.services import TaskService
from app.upload_service import RequirementUploadService


def create_router(
    task_service: TaskService,
    upload_service: RequirementUploadService,
) -> APIRouter:
    router = APIRouter()

    @router.get("/api/tasks", response_model=list[TaskResponse])
    def list_tasks(
        _owner: Annotated[str | None, Query(alias="owner")] = None,
        identity: Identity = Depends(get_identity),
    ) -> list[TaskResponse]:
        return task_service.list_tasks(identity)

    @router.post(
        "/api/tasks",
        status_code=201,
        response_model=TaskResponse,
    )
    def create_task(
        payload: TaskCreateRequest,
        identity: Identity = Depends(get_identity),
    ) -> TaskResponse:
        return task_service.create_task(payload, identity)

    @router.get("/api/summary", response_model=TaskSummaryResponse)
    def summary(
        _owner: Annotated[str | None, Query(alias="owner")] = None,
        identity: Identity = Depends(get_identity),
    ) -> TaskSummaryResponse:
        return task_service.summarize_tasks(identity)

    @router.post(
        "/api/requirements",
        status_code=201,
        response_model=RequirementUploadResponse,
    )
    async def upload_requirement(
        file: Annotated[UploadFile, File()],
        identity: Identity = Depends(get_identity),
    ) -> RequirementUploadResponse:
        return await upload_service.save(file, identity)

    @router.get("/api/backend-health", response_model=BackendHealthResponse)
    def backend_health(
        identity: Identity = Depends(get_identity),
    ) -> BackendHealthResponse:
        return get_backend_health(identity["username"])

    return router
