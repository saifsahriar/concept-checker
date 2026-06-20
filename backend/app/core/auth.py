from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse

import httpx

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwk, jwt
from jose.utils import base64url_decode

from app.core.config import Settings, get_settings

bearer_scheme = HTTPBearer(auto_error=False)


@dataclass(slots=True)
class AuthenticatedUser:
    id: str
    email: str | None = None


def _decode_supabase_jwt(token: str, settings: Settings) -> dict[str, str]:
    payload = _try_shared_secret_decode(token, settings)
    if payload is not None:
        return payload

    payload = _try_jwks_decode(token, settings)
    if payload is not None:
        return payload

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication token")


def _try_shared_secret_decode(token: str, settings: Settings) -> dict[str, str] | None:
    if not settings.supabase_jwt_secret:
        return None

    try:
        return jwt.decode(token, settings.supabase_jwt_secret, algorithms=["HS256"], options={"verify_aud": False})
    except JWTError:
        return None


def _try_jwks_decode(token: str, settings: Settings) -> dict[str, str] | None:
    supabase_url = _resolve_supabase_url(settings)
    if not supabase_url:
        return None

    try:
        header = jwt.get_unverified_header(token)
    except JWTError:
        return None

    kid = header.get("kid")
    alg = header.get("alg")
    if not kid or not alg:
        return None

    jwks_url = f"{supabase_url.rstrip('/')}/auth/v1/.well-known/jwks.json"
    try:
        response = httpx.get(jwks_url, timeout=10.0)
        response.raise_for_status()
        jwks = response.json().get("keys", [])
    except Exception:
        return None

    key_data = next((item for item in jwks if item.get("kid") == kid and item.get("alg") == alg), None)
    if not key_data:
        return None

    try:
        key = jwk.construct(key_data)
        message, encoded_signature = token.rsplit(".", 1)
        if not key.verify(message.encode("utf-8"), base64url_decode(encoded_signature.encode("utf-8"))):
            return None
        payload = jwt.get_unverified_claims(token)
    except Exception:
        return None

    subject = payload.get("sub")
    if not subject:
        return None

    return payload


def _resolve_supabase_url(settings: Settings) -> str | None:
    if settings.supabase_url:
        return settings.supabase_url

    if not settings.database_url:
        return None

    parsed = urlparse(settings.database_url)
    host = parsed.hostname or ""
    if host.startswith("db.") and host.endswith(".supabase.co"):
        ref = host.removeprefix("db.").removesuffix(".supabase.co")
        if ref:
            return f"https://{ref}.supabase.co"
    return None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    settings: Settings = Depends(get_settings),
) -> AuthenticatedUser:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")

    payload = _decode_supabase_jwt(credentials.credentials, settings)
    return AuthenticatedUser(id=payload["sub"], email=payload.get("email"))
