import requests
from fastapi import APIRouter, Depends, HTTPException, status

from config import settings
from security import get_api_key

speakers_router = APIRouter(
    prefix="/speakers",
    tags=["Speakers"],
    dependencies=[Depends(get_api_key)],
)

@speakers_router.get(
    "",
    summary="Get Speakers",
    description="Get list of available speakers from Voicevox Engine."
)
def get_speakers():
    """
    Fetch the list of speakers (characters) from the Voicevox Engine.
    """
    try:
        response = requests.get(f"{settings.VOICEVOX_ENGINE_URL}/speakers")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error communicating with Voicevox Engine: {e}",
        )