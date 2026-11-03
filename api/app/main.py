from __future__ import annotations

import os
import sqlite3
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.repository import TaskRepository
from app.routes import create_router
from app.services import TaskService
from app.upload_service import RequirementUploadService

DEFAULT_DATABASE_PATH = "./data/workshop.db"
DEFAULT_UPLOAD_DIRECTORY = "./uploads"


def create_app(
    db_path: str | None = None,
    upload_dir: str | None = None,
) -> FastAPI:
    selected_db = db_path or os.getenv("WORKSHOP_DB_PATH", DEFAULT_DATABASE_PATH)
    selected_uploads = upload_dir or os.getenv(
        "WORKSHOP_UPLOAD_DIR",
        DEFAULT_UPLOAD_DIRECTORY,
    )
    Path(selected_db).parent.mkdir(parents=True, exist_ok=True)
    upload_path = Path(selected_uploads)
    upload_path.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(selected_db, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    repository = TaskRepository(connection)
    repository.initialize()
    task_service = TaskService(repository)
    upload_service = RequirementUploadService(upload_path)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        try:
            yield
        finally:
            connection.close()

    app = FastAPI(
        title="Workshop Requirements API",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.state.connection = connection
    app.state.upload_dir = str(upload_path)
    app.include_router(create_router(task_service, upload_service))
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    return app


app = create_app()
