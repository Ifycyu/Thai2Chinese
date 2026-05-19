"""API Key authentication dependency."""
import os
from fastapi import Security, HTTPException
from fastapi.security import APIKeyHeader

_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
_server_api_key = os.environ.get("API_KEY", "")


def get_api_key(api_key: str | None = Security(_api_key_header)) -> str:
    """Validate API key from X-API-Key header.

    If API_KEY env var is not set, auth is disabled (returns empty string).
    """
    if not _server_api_key:
        return ""

    if not api_key or api_key != _server_api_key:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")

    return api_key
