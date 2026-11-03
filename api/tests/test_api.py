import json
import time
from pathlib import Path

import jwt
import pytest
from fastapi.testclient import TestClient

import app.health_service as health_module
from app.main import create_app
from app.upload_service import MAX_UPLOAD_BYTES

TEST_JWT_SECRET = "isolated-test-signing-key-not-for-production-only"
TEST_JWT_ISSUER = "https://issuer.test"
TEST_JWT_AUDIENCE = "workshop-api-test"
TEST_TOKEN_LIFETIME_SECONDS = 3600
EXPIRED_TOKEN_OFFSET_SECONDS = 1


@pytest.fixture(autouse=True)
def configure_test_jwt(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("WORKSHOP_JWT_SECRET", TEST_JWT_SECRET)
    monkeypatch.setenv("WORKSHOP_JWT_ISSUER", TEST_JWT_ISSUER)
    monkeypatch.setenv("WORKSHOP_JWT_AUDIENCE", TEST_JWT_AUDIENCE)


def token(
    username: str = "student",
    role: str = "STUDENT",
    **claims: str | int,
) -> str:
    token_claims: dict[str, str | int] = {
        "sub": username,
        "role": role,
        "iss": TEST_JWT_ISSUER,
        "aud": TEST_JWT_AUDIENCE,
        "exp": int(time.time()) + TEST_TOKEN_LIFETIME_SECONDS,
    }
    token_claims.update(claims)
    return jwt.encode(token_claims, TEST_JWT_SECRET, algorithm="HS256")


def headers(username: str = "student", role: str = "STUDENT") -> dict[str, str]:
    return {"Authorization": f"Bearer {token(username, role)}"}


def test_lists_seeded_tasks(tmp_path: Path) -> None:
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        response = client.get("/api/tasks", headers=headers())
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_creates_task_and_summary(tmp_path: Path) -> None:
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        created = client.post(
            "/api/tasks",
            headers=headers(),
            json={"title": "Add tests", "description": "Improve coverage", "status": "TODO", "priority": "HIGH"},
        )
        summary = client.get("/api/summary", headers=headers())
    assert created.status_code == 201
    assert created.json()["owner"] == "student"
    assert summary.json()["total"] == 3


def test_uploads_requirement(tmp_path: Path) -> None:
    upload_dir = tmp_path / "uploads"
    app = create_app(str(tmp_path / "workshop.db"), str(upload_dir))
    with TestClient(app) as client:
        response = client.post(
            "/api/requirements",
            headers=headers(),
            files={"file": ("requirements.txt", b"Login must be accessible", "text/plain")},
        )
    assert response.status_code == 201
    assert (upload_dir / "requirements.txt").exists()


def test_rejects_invalid_token(tmp_path: Path) -> None:
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        response = client.get("/api/tasks", headers={"Authorization": "Bearer invalid"})
    assert response.status_code == 401


def test_task_access_is_bound_to_authenticated_identity(tmp_path: Path) -> None:
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        student_tasks = client.get("/api/tasks", headers=headers())
        trainer_tasks = client.get("/api/tasks?owner=trainer", headers=headers())
        trainer_summary = client.get("/api/summary?owner=trainer", headers=headers())
        created = client.post(
            "/api/tasks",
            headers=headers(),
            json={
                "title": "Characterization",
                "description": "Observe task response",
                "owner": "trainer",
            },
        )

    assert student_tasks.status_code == 200
    assert [task["id"] for task in student_tasks.json()] == [1, 2]
    assert set(student_tasks.json()[0]) == {
        "id", "title", "description", "status", "owner", "priority", "createdAt"
    }
    assert [task["owner"] for task in trainer_tasks.json()] == ["student"] * 2
    assert trainer_summary.json()["owner"] == "student"
    assert trainer_summary.json()["total"] == 2
    assert created.status_code == 201
    assert created.json()["owner"] == "student"


def test_characterizes_summary_and_task_defaults(tmp_path: Path) -> None:
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        created = client.post(
            "/api/tasks",
            headers=headers(),
            json={"title": "Defaults", "description": "Current defaults"},
        )
        summary = client.get("/api/summary", headers=headers())

    assert created.status_code == 201
    assert created.json()["status"] == "TODO"
    assert created.json()["priority"] == "MEDIUM"
    assert created.json()["owner"] == "student"
    assert summary.json() == {
        "owner": "student",
        "total": 3,
        "byStatus": {"TODO": 2, "IN_PROGRESS": 1},
        "highPriorityOpen": 1,
    }


def test_characterizes_upload_response_and_saved_content(tmp_path: Path) -> None:
    upload_dir = tmp_path / "uploads"
    app = create_app(str(tmp_path / "workshop.db"), str(upload_dir))
    with TestClient(app) as client:
        response = client.post(
            "/api/requirements",
            headers=headers(),
            files={"file": ("requirements.txt", b"Keep this content", "text/plain")},
        )

    assert response.status_code == 201
    assert set(response.json()) == {"owner", "fileName", "storedAt", "size"}
    assert response.json()["owner"] == "student"
    assert response.json()["fileName"] == "requirements.txt"
    assert response.json()["size"] == len(b"Keep this content")
    assert (upload_dir / "requirements.txt").read_bytes() == b"Keep this content"


def test_characterizes_backend_health_response(monkeypatch, tmp_path: Path) -> None:
    class FakeResponse:
        status = 200
        data = json.dumps({"status": "UP"}).encode()

    class FakePoolManager:
        def request(self, method: str, url: str, timeout: float):
            assert method == "GET"
            assert url == "http://auth.test/health"
            assert timeout == health_module.HEALTH_TIMEOUT_SECONDS
            return FakeResponse()

    monkeypatch.setattr(health_module.urllib3, "PoolManager", FakePoolManager)
    monkeypatch.setenv("AUTH_HEALTH_URL", "http://auth.test/health")
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        response = client.get("/api/backend-health", headers=headers())

    assert response.status_code == 200
    assert response.json() == {
        "requestedBy": "student",
        "status": 200,
        "body": '{"status": "UP"}',
    }


def test_rejects_jwt_with_invalid_signature_issuer_audience_or_expiry(
    tmp_path: Path,
) -> None:
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    valid_token = token()
    signature_parts = valid_token.split(".")
    signature_parts[2] = (
        "A" if signature_parts[2][0] != "A" else "B"
    ) + signature_parts[2][1:]
    invalid_tokens = [
        ".".join(signature_parts),
        jwt.encode(
            {
                "sub": "student",
                "role": "STUDENT",
                "iss": TEST_JWT_ISSUER,
                "aud": TEST_JWT_AUDIENCE,
                "exp": int(time.time()) + TEST_TOKEN_LIFETIME_SECONDS,
            },
            TEST_JWT_SECRET,
            algorithm="HS384",
        ),
        token(iss="https://other-issuer.test"),
        token(aud="other-api"),
        token(exp=int(time.time()) - EXPIRED_TOKEN_OFFSET_SECONDS),
    ]

    with TestClient(app) as client:
        responses = [
            client.get("/api/tasks", headers={"Authorization": f"Bearer {value}"})
            for value in invalid_tokens
        ]

    assert [response.status_code for response in responses] == [401] * 5
    assert {response.json()["detail"] for response in responses} == {"Invalid token"}


def test_requires_authentication_configuration(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.delenv("WORKSHOP_JWT_SECRET")
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))

    with TestClient(app) as client:
        response = client.get("/api/tasks", headers=headers())

    assert response.status_code == 503
    assert response.json()["detail"] == "Authentication is not configured"


def test_sql_values_are_stored_as_literals(tmp_path: Path) -> None:
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        created = client.post(
            "/api/tasks",
            headers=headers(),
            json={"title": "Owner's task", "description": "Value stays literal"},
        )
        tasks = client.get("/api/tasks", headers=headers())

    assert created.status_code == 201
    assert created.json()["title"] == "Owner's task"
    assert tasks.json()[-1]["title"] == "Owner's task"


def test_upload_normalizes_filename_and_rejects_unsafe_files(
    tmp_path: Path,
) -> None:
    upload_dir = tmp_path / "uploads"
    app = create_app(str(tmp_path / "workshop.db"), str(upload_dir))
    with TestClient(app) as client:
        normalized = client.post(
            "/api/requirements",
            headers=headers(),
            files={"file": ("..\\outside\\notes.txt", b"Safe content", "text/plain")},
        )
        rejected_extension = client.post(
            "/api/requirements",
            headers=headers(),
            files={"file": ("script.py", b"not allowed", "text/plain")},
        )
        rejected_size = client.post(
            "/api/requirements",
            headers=headers(),
            files={
                "file": (
                    "large.txt",
                    b"x" * (MAX_UPLOAD_BYTES + 1),
                    "text/plain",
                )
            },
        )

    assert normalized.status_code == 201
    assert normalized.json()["fileName"] == "notes.txt"
    assert (upload_dir / "notes.txt").read_bytes() == b"Safe content"
    assert not (tmp_path / "outside" / "notes.txt").exists()
    assert rejected_extension.status_code == 400
    assert rejected_size.status_code == 413


def test_backend_health_hides_transport_exception(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    class FailedPoolManager:
        def request(self, method: str, url: str, timeout: float):
            raise health_module.urllib3.exceptions.TimeoutError("private diagnostic")

    monkeypatch.setattr(health_module.urllib3, "PoolManager", FailedPoolManager)
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        response = client.get("/api/backend-health", headers=headers())

    assert response.status_code == 200
    assert response.json() == {
        "requestedBy": "student",
        "status": 0,
        "body": "Backend health check failed",
    }
