from fastapi import APIRouter
from .endpoints import recordings, detections, species, devices, auth

api_router = APIRouter()

# Include all API endpoints
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(recordings.router, prefix="/recordings", tags=["Recordings"])
api_router.include_router(detections.router, prefix="/detections", tags=["Detections"])
api_router.include_router(species.router, prefix="/species", tags=["Species"])
api_router.include_router(devices.router, prefix="/devices", tags=["Devices"])
