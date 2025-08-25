from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader

from config import settings
import store

api_key_header = APIKeyHeader(name="X-API-KEY", auto_error=False)

def get_valid_api_keys() -> set[str]:
    """Returns a set of all valid API keys, including the admin key."""
    keys_from_db = set(store.get_api_keys())
    keys_from_db.add(settings.ADMIN_API_KEY)
    return keys_from_db

def get_api_key(key: str = Security(api_key_header)):
    """Dependency to check for a valid API key in the X-API-KEY header."""
    if key and key in get_valid_api_keys():
        return key
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing API Key",
    )

def get_admin_api_key(key: str = Security(get_api_key)):
    """
    Dependency to check for admin privileges.
    Relies on get_api_key to ensure the key is valid first.
    """
    if key == settings.ADMIN_API_KEY:
        return key
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Admin privileges required",
    )
