import secrets
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

import store
from security import get_admin_api_key

admin_router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
    dependencies=[Depends(get_admin_api_key)],
)

# --- API Key Management ---


@admin_router.get("/keys", response_model=List[str], summary="List API Keys")
def get_all_api_keys():
    """List all generated API keys."""
    return store.get_api_keys()


@admin_router.post(
    "/keys", response_model=str, status_code=status.HTTP_201_CREATED, summary="Create API Key"
)
def create_api_key():
    """Generate and store a new API key."""
    new_key = secrets.token_urlsafe(32)
    store.add_api_key(new_key)
    return new_key


@admin_router.delete(
    "/keys/{api_key}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete API Key"
)
def delete_api_key(api_key: str):
    """Delete an API key."""
    keys = store.get_api_keys()
    if api_key not in keys:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API Key not found",
        )
    store.delete_api_key(api_key)
    return
