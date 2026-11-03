from __future__ import annotations

import os

import urllib3

from app.models import BackendHealthResponse

DEFAULT_AUTH_HEALTH_URL = "http://localhost:8080/q/health"
HEALTH_TIMEOUT_SECONDS = 3.0
HEALTH_FAILURE_BODY = "Backend health check failed"


def get_backend_health(username: str) -> BackendHealthResponse:
    url = os.getenv("AUTH_HEALTH_URL", DEFAULT_AUTH_HEALTH_URL)
    try:
        response = urllib3.PoolManager().request(
            "GET",
            url,
            timeout=HEALTH_TIMEOUT_SECONDS,
        )
    except urllib3.exceptions.HTTPError:
        return BackendHealthResponse(
            requested_by=username,
            status=0,
            body=HEALTH_FAILURE_BODY,
        )

    return BackendHealthResponse(
        requested_by=username,
        status=response.status,
        body=response.data.decode("utf-8"),
    )
