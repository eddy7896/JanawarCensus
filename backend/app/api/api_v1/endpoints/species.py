from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime

from .... import crud, schemas, models
from ....core.config import settings
from ....db.session import get_db
from ....core.security import get_current_active_user
from ....schemas.species import Species, SpeciesCreate, SpeciesUpdate

router = APIRouter()

@router.get("/", response_model=List[schemas.species.Species])
def list_species(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    order_by: str = "scientific_name",
    order: str = "asc",
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    List all bird species with optional search and ordering.
    """
    if search:
        # Search by scientific or common name
        species_list, total = crud.species.search(
            db,
            query=search,
            skip=skip,
            limit=limit
        )
    else:
        # Get all species with pagination
        species_list, total = crud.species.get_multi(
            db,
            skip=skip,
            limit=limit
        )
    
    # Apply ordering
    reverse_order = order.lower() == "desc"
    
    def get_sort_key(species):
        if order_by == "scientific_name":
            return species.scientific_name.lower()
        elif order_by == "common_name":
            return (species.common_name or "").lower()
        elif order_by == "family":
            return (species.family or "").lower()
        elif order_by == "iucn_status":
            return (species.iucn_status or "").lower()
        else:
            return species.id
    
    # Sort the list
    species_list = sorted(
        species_list,
        key=get_sort_key,
        reverse=reverse_order
    )
    
    return species_list

@router.post("/", response_model=schemas.species.Species, status_code=status.HTTP_201_CREATED)
def create_species(
    species_in: SpeciesCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Create a new bird species.
    
    Only admin users can create new species.
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to create species"
        )
    
    # Check if species with this scientific name already exists
    existing_species = crud.species.get_by_scientific_name(
        db, 
        scientific_name=species_in.scientific_name
    )
    
    if existing_species:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A species with this scientific name already exists"
        )
    
    # Create the species
    species = crud.species.create(db, obj_in=species_in)
    return species

@router.get("/{species_id}", response_model=schemas.species.SpeciesWithStats)
def get_species(
    species_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Get detailed information about a specific species.
    """
    species = crud.species.get(db, id=species_id)
    if not species:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Species not found"
        )
    
    # Get detection statistics for this species
    detection_stats = crud.detection.get_species_detection_stats(
        db, 
        species_scientific_name=species.scientific_name
    )
    
    # Get recent detections
    recent_detections, _ = crud.detection.get_multi(
        db,
        skip=0,
        limit=10,
        species=species.scientific_name,
        order_by="created_at",
        order="desc"
    )
    
    # Get detection timeline (last 30 days)
    timeline = crud.detection.get_detection_timeline(
        db,
        time_window="day",
        species=species.scientific_name,
        date_from=datetime.utcnow() - timedelta(days=30)
    )
    
    # Get detection locations
    locations = crud.detection.get_detection_locations(
        db,
        species_scientific_name=species.scientific_name,
        limit=100  # Limit number of points for performance
    )
    
    return {
        **species.__dict__,
        "detection_stats": detection_stats,
        "recent_detections": recent_detections,
        "timeline": timeline,
        "locations": locations
    }

@router.put("/{species_id}", response_model=schemas.species.Species)
def update_species(
    species_id: int,
    species_in: SpeciesUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Update species information.
    
    Only admin users can update species.
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to update species"
        )
    
    species = crud.species.get(db, id=species_id)
    if not species:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Species not found"
        )
    
    # Check if scientific name is being changed to one that already exists
    if species_in.scientific_name and species_in.scientific_name != species.scientific_name:
        existing = crud.species.get_by_scientific_name(
            db, 
            scientific_name=species_in.scientific_name
        )
        if existing and existing.id != species_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A species with this scientific name already exists"
            )
    
    return crud.species.update(db, db_obj=species, obj_in=species_in)

@router.delete("/{species_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_species(
    species_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Delete a species.
    
    Only admin users can delete species.
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to delete species"
        )
    
    species = crud.species.get(db, id=species_id)
    if not species:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Species not found"
        )
    
    # Check if there are any detections for this species
    detection_count = db.query(models.Detection).filter(
        models.Detection.species_scientific_name == species.scientific_name
    ).count()
    
    if detection_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete species with {detection_count} associated detections"
        )
    
    crud.species.remove(db, id=species_id)
    return None

@router.get("/{scientific_name}/detections/", response_model=List[schemas.detection.Detection])
def get_species_detections(
    scientific_name: str = Path(..., description="Scientific name of the species"),
    skip: int = 0,
    limit: int = 100,
    min_confidence: float = Query(0.0, ge=0.0, le=1.0, description="Minimum confidence score (0-1)"),
    date_from: Optional[datetime] = Query(None, description="Filter by start date"),
    date_to: Optional[datetime] = Query(None, description="Filter by end date"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Get detections for a specific species.
    """
    # Check if species exists
    species = crud.species.get_by_scientific_name(db, scientific_name=scientific_name)
    if not species:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Species not found"
        )
    
    # Get detections for this species
    detections, total = crud.detection.get_multi(
        db,
        skip=skip,
        limit=limit,
        min_confidence=min_confidence,
        species_scientific_name=scientific_name,
        date_from=date_from,
        date_to=date_to,
        order_by="created_at",
        order="desc"
    )
    
    return detections

@router.get("/{scientific_name}/stats/", response_model=Dict[str, Any])
def get_species_stats(
    scientific_name: str = Path(..., description="Scientific name of the species"),
    days: int = Query(30, ge=1, le=365, description="Number of days of history to include"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Get statistics for a specific species.
    """
    # Check if species exists
    species = crud.species.get_by_scientific_name(db, scientific_name=scientific_name)
    if not species:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Species not found"
        )
    
    # Calculate date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Get detection statistics
    stats = crud.detection.get_species_detection_stats(
        db,
        species_scientific_name=scientific_name,
        date_from=start_date,
        date_to=end_date
    )
    
    # Get detection timeline
    timeline = crud.detection.get_detection_timeline(
        db,
        time_window="day",
        species=scientific_name,
        date_from=start_date,
        date_to=end_date
    )
    
    # Get detection locations
    locations = crud.detection.get_detection_locations(
        db,
        species_scientific_name=scientific_name,
        limit=1000  # Increase limit for better map coverage
    )
    
    # Get devices that have detected this species
    device_query = db.query(
        models.Recording.device_id,
        func.count(models.Detection.id).label("detection_count")
    ).join(
        models.Detection,
        models.Detection.recording_id == models.Recording.id
    ).filter(
        models.Detection.species_scientific_name == scientific_name
    ).group_by(
        models.Recording.device_id
    ).order_by(
        func.count(models.Detection.id).desc()
    ).limit(10)
    
    devices = [
        {
            "device_id": device_id,
            "detection_count": count
        }
        for device_id, count in device_query.all()
    ]
    
    return {
        "species": species,
        "stats": stats,
        "timeline": timeline,
        "locations": locations,
        "devices": devices
    }
