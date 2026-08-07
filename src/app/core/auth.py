import secrets

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.app.core.config import settings

_scheme = HTTPBearer()


def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(_scheme),
) -> str:
    """Validate the Bearer token against the configured ``API_BEARER_TOKEN``."""
    if not settings.API_BEARER_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="API_BEARER_TOKEN is not configured",
        )
    if not secrets.compare_digest(credentials.credentials, settings.API_BEARER_TOKEN):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid bearer token",
        )
    return credentials.credentials
