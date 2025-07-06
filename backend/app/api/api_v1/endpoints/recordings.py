from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status, Query
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import shutil
import uuid
from pathlib import Path
import logging

from .... import crud, schemas, models
from ....core.config import settings
from ....db.session import get_db
from ....utils.audio import validate_audio_file, get_audio_duration

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/upload/", response_model=schemas.recording.FileUploadResponse)
async def upload_recording(
    file: UploadFile = File(...),
    device_id: str = Query(..., description="ID of the device uploading the file"),
    latitude: Optional[float] = Query(None, description="Latitude of the recording location"),
    longitude: Optional[float] = Query(None, description="Longitude of the recording location"),
    location_name: Optional[str] = Query(None, description="Human-readable location name"),
    db: Session = Depends(get_db)
):
    """
    Upload a new audio recording file.
    """
    try:
        # Validate file type
        if not validate_audio_file(file):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file type. Supported types: {', '.join(settings.ALLOWED_AUDIO_TYPES)}"
            )
        
        # Create upload directory if it doesn't exist
        upload_dir = Path(settings.AUDIO_UPLOAD_DIR)
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate unique filename
        file_ext = Path(file.filename).suffix.lower()
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        file_path = upload_dir / unique_filename
        
        # Save file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Get file size and duration
        file_size = os.path.getsize(file_path)
        duration = get_audio_duration(file_path)
        
        # Create recording in database
        recording_in = schemas.recording.RecordingCreate(
            file_name=file.filename,
            file_path=str(file_path),
            file_size=file_size,
            file_type=file_ext.lstrip("."),
            duration=duration,
            latitude=latitude,
            longitude=longitude,
            location_name=location_name,
            device_id=device_id
        )
        
        recording = crud.recording.create(db, obj_in=recording_in)
        
        return {
            "id": recording.id,
            "file_name": recording.file_name,
            "file_path": recording.file_path,
            "status": recording.status,
            "message": "File uploaded successfully"
        }
        
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}", exc_info=True)
        # Clean up file if it was partially uploaded
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading file: {str(e)}"
        )

@router.get("/", response_model=List[schemas.recording.Recording])
def list_recordings(
    skip: int = 0,
    limit: int = 100,
    status: Optional[schemas.recording.RecordingStatus] = None,
    device_id: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    min_confidence: Optional[float] = None,
    species: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    List all recordings with optional filtering.
    """
    filters = {}
    if status:
        filters["status"] = status
    if device_id:
        filters["device_id"] = device_id
    
    # Apply date range filter
    date_filters = {}
    if date_from:
        date_filters["date_from"] = date_from
    if date_to:
        date_filters["date_to"] = date_to
    
    return crud.recording.get_multi(
        db, 
        skip=skip, 
        limit=limit,
        filters=filters,
        date_filters=date_filters,
        min_confidence=min_confidence,
        species=species
    )

@router.get("/{recording_id}", response_model=schemas.recording.RecordingWithDetections)
def get_recording(
    recording_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a specific recording by ID with its detections.
    """
    recording = crud.recording.get(db, id=recording_id)
    if not recording:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recording not found"
        )
    return recording

@router.get("/{recording_id}/audio")
def get_recording_audio(
    recording_id: int,
    db: Session = Depends(get_db)
):
    """
    Stream the audio file for a recording.
    """
    recording = crud.recording.get(db, id=recording_id)
    if not recording or not os.path.exists(recording.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recording or audio file not found"
        )
    
    return FileResponse(
        recording.file_path,
        media_type=f"audio/{recording.file_type}",
        filename=recording.file_name
    )

@router.delete("/{recording_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_recording(
    recording_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a recording and its associated file.
    """
    recording = crud.recording.get(db, id=recording_id)
    if not recording:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recording not found"
        )
    
    # Delete the file if it exists
    if os.path.exists(recording.file_path):
        try:
            os.remove(recording.file_path)
        except Exception as e:
            logger.error(f"Error deleting file {recording.file_path}: {str(e)}")
    
    # Delete from database
    crud.recording.remove(db, id=recording_id)
    
    return None
