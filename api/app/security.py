from __future__ import annotations

import os
from typing import Annotated, TypedDict

import jwt
from fastapi import Header, HTTPException

JWT_ALGORITHM = "HS256"
JWT_SECRET_ENV = "WORKSHOP_JWT_SECRET"
JWT_ISSUER_ENV = "WORKSHOP_JWT_ISSUER"
JWT_AUDIENCE_ENV = "WORKSHOP_JWT_AUDIENCE"
INVALID_TOKEN_DETAIL = "Invalid token"
AUTH_CONFIGURATION_DETAIL = "Authentication is not configured"


class Identity(TypedDict):
    username: str
    role: str


def _required_setting(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise HTTPException(status_code=503, detail=AUTH_CONFIGURATION_DETAIL)
    return value


def get_identity(authorization: Annotated[str, Header()] = "") -> Identity:
    scheme, separator, token = authorization.partition(" ")
    if not separator or scheme.lower() != "bearer" or not token:
        raise HTTPException(
            status_code=401,
            detail=INVALID_TOKEN_DETAIL,
            headers={"WWW-Authenticate": "Bearer"},
        )

    secret = _required_setting(JWT_SECRET_ENV)
    issuer = _required_setting(JWT_ISSUER_ENV)
    audience = _required_setting(JWT_AUDIENCE_ENV)

    try:
        claims = jwt.decode(
            token,
            secret,
            algorithms=[JWT_ALGORITHM],
            issuer=issuer,
            audience=audience,
            options={"require": ["exp", "iss", "aud", "sub", "role"]},
        )
    except jwt.InvalidTokenError as error:
        raise HTTPException(
            status_code=401,
            detail=INVALID_TOKEN_DETAIL,
            headers={"WWW-Authenticate": "Bearer"},
        ) from error

    username = claims.get("sub")
    role = claims.get("role")
    if not isinstance(username, str) or not username or not isinstance(role, str):
        raise HTTPException(status_code=401, detail=INVALID_TOKEN_DETAIL)
    return {"username": username, "role": role}
