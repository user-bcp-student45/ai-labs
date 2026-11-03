from __future__ import annotations

import unicodedata
from pathlib import Path, PurePosixPath

from fastapi import HTTPException, UploadFile

from app.models import RequirementUploadResponse
from app.security import Identity

MAX_UPLOAD_BYTES = 1_048_576
ALLOWED_UPLOAD_EXTENSIONS = frozenset({".txt", ".md"})
INVALID_UPLOAD_DETAIL = "Invalid requirement file"
UPLOAD_TOO_LARGE_DETAIL = "Requirement file exceeds the maximum size"


class RequirementUploadService:
    def __init__(self, upload_dir: Path) -> None:
        self._upload_dir = upload_dir
        self._resolved_upload_dir = upload_dir.resolve()

    async def save(
        self,
        file: UploadFile,
        identity: Identity,
    ) -> RequirementUploadResponse:
        safe_name = normalize_upload_name(file.filename)
        if Path(safe_name).suffix.lower() not in ALLOWED_UPLOAD_EXTENSIONS:
            raise HTTPException(status_code=400, detail=INVALID_UPLOAD_DETAIL)

        content = await file.read(MAX_UPLOAD_BYTES + 1)
        if len(content) > MAX_UPLOAD_BYTES:
            raise HTTPException(status_code=413, detail=UPLOAD_TOO_LARGE_DETAIL)

        target = self._upload_dir / safe_name
        if not target.resolve().is_relative_to(self._resolved_upload_dir):
            raise HTTPException(status_code=400, detail=INVALID_UPLOAD_DETAIL)

        target.write_bytes(content)
        return RequirementUploadResponse(
            owner=identity["username"],
            file_name=safe_name,
            stored_at=str(target),
            size=len(content),
        )


def normalize_upload_name(filename: str | None) -> str:
    if not filename:
        raise HTTPException(status_code=400, detail=INVALID_UPLOAD_DETAIL)
    normalized_name = unicodedata.normalize("NFKC", filename).replace("\\", "/")
    safe_name = PurePosixPath(normalized_name).name.strip()
    if safe_name in {"", ".", ".."}:
        raise HTTPException(status_code=400, detail=INVALID_UPLOAD_DETAIL)
    return safe_name
