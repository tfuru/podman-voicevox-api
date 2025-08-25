import uuid
import base64
from typing import Optional
from fastapi import APIRouter, BackgroundTasks, HTTPException, status, Response
from pydantic import BaseModel

import store
from routers.synthesis import simplified_synthesis, SynthesisRequest # Re-use logic

tasks_router = APIRouter(
    prefix="/tasks",
    tags=["Tasks"],
)

class JobCreationResponse(BaseModel):
    job_id: str
    status: str

class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    error: Optional[str] = None

# This function will run in the background
def async_synthesis_task(job_id: str, payload: SynthesisRequest):
    try:
        store.update_job_status(job_id, store.JOB_STATUS_RUNNING)
        # Call the existing simplified_synthesis logic
        # This will return a FastAPI Response object, we need its content
        response = simplified_synthesis(payload)
        if response.status_code == status.HTTP_200_OK:
            store.update_job_status(job_id, store.JOB_STATUS_COMPLETED, result=response.body)
        else:
            # Assuming simplified_synthesis raises HTTPException on error
            # If it returns an error response, we need to parse it
            store.update_job_status(job_id, store.JOB_STATUS_FAILED, error=response.body.decode('utf-8'))
    except HTTPException as e:
        store.update_job_status(job_id, store.JOB_STATUS_FAILED, error=e.detail)
    except Exception as e:
        store.update_job_status(job_id, store.JOB_STATUS_FAILED, error=str(e))


@tasks_router.post("/synthesis", response_model=JobCreationResponse, status_code=status.HTTP_202_ACCEPTED)
def submit_synthesis_job(payload: SynthesisRequest, background_tasks: BackgroundTasks):
    """
    Submits an audio synthesis job to be processed asynchronously.
    Returns a job ID to check the status.
    """
    job_id = str(uuid.uuid4())
    store.add_job(job_id, store.JOB_STATUS_PENDING, payload.dict())
    background_tasks.add_task(async_synthesis_task, job_id, payload)
    return {"job_id": job_id, "status": store.JOB_STATUS_PENDING}


@tasks_router.get("/{job_id}/status", response_model=JobStatusResponse)
def get_synthesis_job_status(job_id: str):
    """
    Retrieves the status of an asynchronous synthesis job.
    """
    job = store.get_job(job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    response_data = {
        "job_id": job_id,
        "status": job["status"],
    }
    if "error" in job:
        response_data["error"] = job["error"]

    return response_data

@tasks_router.get("/{job_id}/result", response_class=Response,
                  responses={
                      200: {"content": {"audio/wav": {}, "audio/mpeg": {}, "audio/mp4": {}}},
                      404: {"description": "Job not found or result not ready."},
                      400: {"description": "Job failed."},
                  })
def get_synthesis_job_result(job_id: str):
    """
    Retrieves the result (audio file) of a completed synthesis job.
    """
    job = store.get_job(job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    if job["status"] == store.JOB_STATUS_COMPLETED:
        if "result" in job:
            audio_content = base64.b64decode(job["result"])
            # Determine media type from original payload format
            original_payload = job.get("payload", {})
            requested_format = original_payload.get("format", "wav")
            media_type = "audio/wav"
            if requested_format == "mp3":
                media_type = "audio/mpeg"
            elif requested_format == "mp4":
                media_type = "audio/mp4"

            return Response(content=audio_content, media_type=media_type)
        else:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job completed but result not found.")
    elif job["status"] == store.JOB_STATUS_FAILED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Job failed: {job.get('error', 'Unknown error')}")
    else:
        raise HTTPException(status_code=status.HTTP_202_ACCEPTED, detail="Job not yet completed.")
