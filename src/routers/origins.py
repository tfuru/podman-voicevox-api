from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

import store
from security import get_api_key

origins_router = APIRouter(
    prefix="/origins",
    tags=["Origins"],
    dependencies=[Depends(get_api_key)],
)

class OriginPayload(BaseModel):
    origin: str


@origins_router.get("", response_model=List[str], summary="List CORS Origins for API Key")
def get_origins_for_key_route(api_key: str = Depends(get_api_key)):
    """List all allowed CORS origins for the authenticated API key."""
    return store.get_origins_for_key(api_key)


@origins_router.post(
    "", status_code=status.HTTP_201_CREATED, summary="Add CORS Origin for API Key"
)
def add_origin_for_key_route(payload: OriginPayload, api_key: str = Depends(get_api_key)):
    """Add a new allowed CORS origin for the authenticated API key."""
    store.add_origin_for_key(api_key, payload.origin)
    return {"message": f"Origin '{payload.origin}' added to key."}


@origins_router.delete(
    "", status_code=status.HTTP_204_NO_CONTENT, summary="Delete CORS Origin for API Key"
)
def delete_origin_for_key_route(payload: OriginPayload, api_key: str = Depends(get_api_key)):
    """Delete an allowed CORS origin for the authenticated API key."""
    origins = store.get_origins_for_key(api_key)
    if payload.origin not in origins:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Origin not found for this API key",
        )
    store.delete_origin_for_key(api_key, payload.origin)
    return
