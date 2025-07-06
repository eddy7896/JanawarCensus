from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from .... import crud, schemas, models
from ....core.config import settings
from ....db.session import get_db
from ....core.security import get_current_active_user

router = APIRouter()

@router.get("/", response_model=List[schemas.detection.Detection])
def list_detections(
    skip: int = 0,
    limit: int = 100,
    min_confidence: float = Query(0.0, ge=0.0, le=1.0, description="Minimum confidence score (0-1)"),
    species: Optional[str] = Query(None, description="Filter by species (scientific or common name)"),
    date_from: Optional[datetime] = Query(None, description="Filter by start date"),
    date_to: Optional[datetime] = Query(None, description="Filter by end date"),
    recording_id: Optional[int] = Query(None, description="Filter by recording ID"),
    device_id: Optional[str] = Query(None, description="Filter by device ID"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    List all detections with optional filtering.
    """
    # Build filters
    filters = {}
    if recording_id is not None:
        filters["recording_id"] = recording_id
    
    # Get detections with filters
    detections, total = crud.detection.get_multi(
        db,
        skip=skip,
        limit=limit,
        min_confidence=min_confidence,
        species=species,
        date_from=date_from,
        date_to=date_to,
        device_id=device_id,
        **filters
    )
    
    return detections

@router.get("/{detection_id}", response_model=schemas.detection.DetectionWithRecording)
def get_detection(
    detection_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Get a specific detection by ID.
    """
    detection = crud.detection.get(db, id=detection_id)
    if not detection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Detection not found"
        )
    
    # Get the associated recording
    detection.recording = crud.recording.get(db, id=detection.recording_id)
    
    return detection

@router.get("/species/", response_model=List[Dict[str, Any]])
def list_species(
    min_confidence: float = Query(0.0, ge=0.0, le=1.0, description="Minimum confidence score (0-1)"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of species to return"),
    date_from: Optional[datetime] = Query(None, description="Filter by start date"),
    date_to: Optional[datetime] = Query(None, description="Filter by end date"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Get a list of detected species with their detection counts.
    """
    return crud.detection.get_species_list(
        db,
        min_confidence=min_confidence,
        limit=limit,
        date_from=date_from,
        date_to=date_to
    )

@router.get("/timeline/", response_model=List[Dict[str, Any]])
def get_detection_timeline(
    time_window: str = Query("day", description="Time window for grouping ('hour', 'day', 'week', 'month')"),
    species: Optional[str] = Query(None, description="Filter by species (scientific or common name)"),
    date_from: Optional[datetime] = Query(None, description="Filter by start date"),
    date_to: Optional[datetime] = Query(None, description="Filter by end date"),
    device_id: Optional[str] = Query(None, description="Filter by device ID"),
    min_confidence: float = Query(0.0, ge=0.0, le=1.0, description="Minimum confidence score (0-1)"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Get a timeline of detections over time.
    """
    # Build filters
    filters = {"min_confidence": min_confidence}
    if device_id:
        filters["device_id"] = device_id
    
    return crud.detection.get_detection_timeline(
        db,
        time_window=time_window,
        species=species,
        date_from=date_from,
        date_to=date_to,
        **filters
    )

@router.get("/map/", response_model=List[Dict[str, Any]])
def get_detection_map(
    species: Optional[str] = Query(None, description="Filter by species (scientific or common name)"),
    date_from: Optional[datetime] = Query(None, description="Filter by start date"),
    date_to: Optional[datetime] = Query(None, description="Filter by end date"),
    min_confidence: float = Query(0.0, ge=0.0, le=1.0, description="Minimum confidence score (0-1)"),
    limit: int = Query(1000, ge=1, le=10000, description="Maximum number of points to return"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Get detections with geographic coordinates for mapping.
    """
    # Build the base query
    query = db.query(
        models.Detection,
        models.Recording.latitude,
        models.Recording.longitude
    ).join(
        models.Recording,
        models.Detection.recording_id == models.Recording.id
    ).filter(
        models.Recording.latitude.isnot(None),
        models.Recording.longitude.isnot(None),
        models.Detection.confidence >= min_confidence
    )
    
    # Apply species filter
    if species:
        query = query.filter(
            or_(
                models.Detection.species_scientific_name.ilike(f"%{species}%"),
                models.Detection.species_common_name.ilike(f"%{species}%")
            )
        )
    
    # Apply date range
    if date_from:
        query = query.filter(models.Detection.created_at >= date_from)
    if date_to:
        query = query.filter(models.Detection.created_at <= date_to)
    
    # Apply limit and order
    results = query.order_by(
        models.Detection.created_at.desc()
    ).limit(limit).all()
    
    # Format results for mapping
    return [
        {
            "id": detection.id,
            "scientific_name": detection.species_scientific_name,
            "common_name": detection.species_common_name,
            "confidence": detection.confidence,
            "detected_at": detection.created_at.isoformat(),
            "latitude": lat,
            "longitude": lon,
            "recording_id": detection.recording_id
        }
        for detection, lat, lon in results
    ]

@router.get("/stats/species/", response_model=Dict[str, Any])
def get_species_stats(
    top_n: int = Query(10, ge=1, le=50, description="Number of top species to return"),
    min_confidence: float = Query(0.7, ge=0.0, le=1.0, description="Minimum confidence score (0-1)"),
    date_from: Optional[datetime] = Query(None, description="Filter by start date"),
    date_to: Optional[datetime] = Query(None, description="Filter by end date"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Get statistics about detected species.
    """
    # Get species list with detection counts
    species_list = crud.detection.get_species_list(
        db,
        min_confidence=min_confidence,
        limit=top_n,
        date_from=date_from,
        date_to=date_to
    )
    
    # Get total detection count
    total_detections = db.query(func.count(models.Detection.id)).scalar()
    
    # Get detection timeline for the top species
    top_species = [s["scientific_name"] for s in species_list[:5]]  # Top 5 for timeline
    
    timeline_data = {}
    for sp in top_species:
        timeline = crud.detection.get_detection_timeline(
            db,
            time_window="day",
            species=sp,
            date_from=date_from,
            date_to=date_to,
            min_confidence=min_confidence
        )
        timeline_data[sp] = timeline
    
    return {
        "total_species": len(species_list),
        "total_detections": total_detections,
        "top_species": species_list,
        "timeline_data": timeline_data
    }
