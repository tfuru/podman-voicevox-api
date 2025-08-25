from fastapi import APIRouter, Depends, FastAPI, Request
from fastapi.responses import JSONResponse

import store
from routers.admin import admin_router
from routers.synthesis import synthesis_router
from routers.tasks import tasks_router
from routers.origins import origins_router
from security import get_api_key

# Main app instance
app = FastAPI(
    title="Podman Voicevox API",
    description="A wrapper API for Voicevox Engine with additional features.",
    version="0.1.0",
)

@app.middleware("http")
async def cors_middleware(request: Request, call_next):
    if request.method == "OPTIONS" and "origin" in request.headers:
        return JSONResponse(
            content={"detail": "OK"},
            headers={
                "Access-Control-Allow-Origin": request.headers["origin"],
                "Access-Control-Allow-Methods": "POST, GET, OPTIONS, DELETE",
                "Access-Control-Allow-Headers": "X-API-KEY, Content-Type",
                "Access-Control-Allow-Credentials": "true",
            },
        )

    response = await call_next(request)
    if "origin" in request.headers:
        api_key = request.headers.get("x-api-key")
        if api_key:
            allowed_origins = store.get_origins_for_key(api_key)
            if request.headers["origin"] in allowed_origins:
                response.headers["Access-Control-Allow-Origin"] = request.headers["origin"]
                response.headers["Access-Control-Allow-Credentials"] = "true"

    return response

# API router with /api prefix and authentication for all endpoints
api_router = APIRouter(
    prefix="/api",
    dependencies=[Depends(get_api_key)],
)


@api_router.get("/")
def read_api_root():
    """Root endpoint for the API. Requires authentication."""
    return {"message": "Podman Voicevox API - Authenticated"}


# Admin router for managing keys, etc.
api_router.include_router(admin_router)

# Origins router for managing origins
api_router.include_router(origins_router)

# Synthesis router
api_router.include_router(synthesis_router)

# Tasks router
api_router.include_router(tasks_router)


# Include the main router in the app
app.include_router(api_router)

# The root of the app can be used for a simple health check if needed
@app.get("/", include_in_schema=False)
def read_root():
    return {"status": "ok"}