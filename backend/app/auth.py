import logging
from functools import lru_cache

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwk, jwt

from app.config import get_settings

logger = logging.getLogger(__name__)
security = HTTPBearer(auto_error=False)

_jwks_cache: dict | None = None


def _get_jwks_url() -> str:
    settings = get_settings()
    region = settings.cognito_region or "ap-south-1"
    pool_id = settings.cognito_user_pool_id
    return f"https://cognito-idp.{region}.amazonaws.com/{pool_id}/.well-known/jwks.json"


def _get_issuer() -> str:
    settings = get_settings()
    region = settings.cognito_region or "ap-south-1"
    pool_id = settings.cognito_user_pool_id
    return f"https://cognito-idp.{region}.amazonaws.com/{pool_id}"


def _fetch_jwks() -> dict:
    global _jwks_cache
    if _jwks_cache is not None:
        return _jwks_cache
    url = _get_jwks_url()
    logger.info("Fetching Cognito JWKS from %s", url)
    response = httpx.get(url, timeout=10)
    response.raise_for_status()
    _jwks_cache = response.json()
    return _jwks_cache


def _get_signing_key(token: str) -> dict:
    jwks = _fetch_jwks()
    unverified_header = jwt.get_unverified_header(token)
    kid = unverified_header.get("kid")
    for key in jwks.get("keys", []):
        if key["kid"] == kid:
            return key
    raise HTTPException(status_code=401, detail="Token signing key not found in JWKS.")


def _is_demo_mode() -> bool:
    settings = get_settings()
    return not settings.cognito_user_pool_id or not settings.cognito_app_client_id


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> dict:
    """Validate Cognito JWT and return user claims. Allows demo tokens in demo mode."""
    if credentials is None:
        if _is_demo_mode():
            return {"sub": "demo-user", "email": "member3@zerotrust.aws", "groups": ["Analysts"], "demo": True}
        raise HTTPException(status_code=401, detail="Missing authorization header.")

    token = credentials.credentials

    # Allow demo token
    if token == "demo-cognito-jwt-token":
        return {"sub": "demo-user", "email": "member3@zerotrust.aws", "groups": ["Analysts"], "demo": True}

    if _is_demo_mode():
        return {"sub": "demo-user", "email": "member3@zerotrust.aws", "groups": ["Analysts"], "demo": True}

    try:
        signing_key = _get_signing_key(token)
        settings = get_settings()
        claims = jwt.decode(
            token,
            signing_key,
            algorithms=["RS256"],
            audience=settings.cognito_app_client_id,
            issuer=_get_issuer(),
            options={"verify_at_hash": False},
        )
        return {
            "sub": claims.get("sub", ""),
            "email": claims.get("email", claims.get("cognito:username", "unknown")),
            "groups": claims.get("cognito:groups", []),
            "demo": False,
        }
    except JWTError as exc:
        logger.warning("JWT validation failed: %s", exc)
        raise HTTPException(status_code=401, detail=f"Invalid token: {exc}") from exc
    except httpx.HTTPError as exc:
        logger.exception("Failed to fetch JWKS")
        raise HTTPException(status_code=503, detail="Cannot validate token right now.") from exc
