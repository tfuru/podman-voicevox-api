import requests
from fastapi import APIRouter, HTTPException, status, Response
from pydantic import BaseModel
from pydub import AudioSegment
import io

from config import settings

synthesis_router = APIRouter()

class SynthesisRequest(BaseModel):
    text: str
    speaker: int
    format: str = "wav" # New optional format field

@synthesis_router.post(
    "/synthesis",
    tags=["Synthesis"],
    summary="Synthesize Audio",
    response_class=Response,
    responses={
        200: {
            "content": {
                "audio/wav": {},
                "audio/mpeg": {}, # For MP3
                "audio/mp4": {},  # For MP4
            },
            "description": "Successful synthesis, returning audio in specified format.",
        },
        400: {"description": "Invalid audio format requested."},
        500: {"description": "Internal server error or error communicating with Voicevox Engine."},
    },
)
def simplified_synthesis(payload: SynthesisRequest):
    """
    Synthesizes audio from text in a single API call, with optional format conversion.
    Supported formats: wav, mp3, mp4.
    """
    if payload.format not in ["wav", "mp3", "mp4"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid audio format requested. Supported formats: wav, mp3, mp4.",
        )

    try:
        # 1. Create audio query
        query_params = {"text": payload.text, "speaker": payload.speaker}
        query_response = requests.post(
            f"{settings.VOICEVOX_ENGINE_URL}/audio_query", params=query_params
        )
        query_response.raise_for_status()
        audio_query = query_response.json()

        # 2. Synthesize audio (always get WAV from Voicevox Engine)
        synthesis_params = {"speaker": payload.speaker}
        synthesis_response = requests.post(
            f"{settings.VOICEVOX_ENGINE_URL}/synthesis",
            params=synthesis_params,
            json=audio_query,
        )
        synthesis_response.raise_for_status()

        audio_content = synthesis_response.content
        media_type = "audio/wav"

        # 3. Convert if requested format is not WAV
        if payload.format != "wav":
            audio_segment = AudioSegment.from_wav(io.BytesIO(audio_content))
            output_buffer = io.BytesIO()
            audio_segment.export(output_buffer, format=payload.format)
            audio_content = output_buffer.getvalue()
            if payload.format == "mp3":
                media_type = "audio/mpeg"
            elif payload.format == "mp4":
                media_type = "audio/mp4"

        # 4. Return audio content
        return Response(
            content=audio_content,
            media_type=media_type,
            status_code=status.HTTP_200_OK,
        )

    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error communicating with Voicevox Engine: {e}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error during audio processing: {e}",
        )
