from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class TaskCreateRequest(BaseModel):
    title: str = ""
    description: str = ""
    status: str = "TODO"
    owner: str | None = None
    priority: str = "MEDIUM"


class TaskResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: int
    title: str
    description: str
    status: str
    owner: str
    priority: str
    created_at: str = Field(serialization_alias="createdAt")


class TaskSummaryResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    owner: str
    total: int
    by_status: dict[str, int] = Field(serialization_alias="byStatus")
    high_priority_open: int = Field(serialization_alias="highPriorityOpen")


class RequirementUploadResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    owner: str
    file_name: str = Field(serialization_alias="fileName")
    stored_at: str = Field(serialization_alias="storedAt")
    size: int


class BackendHealthResponse(BaseModel):
    requested_by: str = Field(serialization_alias="requestedBy")
    status: int
    body: str
