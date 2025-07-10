from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.services.audio_analysis import AudioAnalysisService

router = APIRouter()

@router.post("/recordings/{recording_id}/analyze", response_model=schemas.analysis.AnalysisResults)
async def analyze_recording(
    recording_id: int,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
):
    """
    Analyze a specific recording.
    """
    # Get recording from database
    recording = crud.recording.get(db, id=recording_id)
    if not recording:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recording not found",
        )
    
    # Check if user has permission to access this recording
    if recording.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to access this recording",
        )
    
    # Initialize analysis service
    analysis_service = AudioAnalysisService(db)
    
    try:
        # Run analysis
        result = await analysis_service.analyze_recording(recording.file_path, recording.id)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error analyzing recording: {str(e)}",
        )

@router.get("/analyses/", response_model=List[schemas.analysis.Analysis])
def read_analyses(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve analyses.
    """
    if current_user.is_superuser:
        analyses = crud.analysis.get_multi(db, skip=skip, limit=limit)
    else:
        analyses = crud.analysis.get_multi_by_owner(
            db=db, owner_id=current_user.id, skip=skip, limit=limit
        )
    return analyses

@router.get("/analyses/species/", response_model=List[Dict[str, Any]])
def get_detected_species(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get list of all detected species with their detection counts.
    """
    if current_user.is_superuser:
        return crud.analysis.get_detected_species(db, skip=skip, limit=limit)
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )

@router.get("/analyses/recording/{recording_id}", response_model=List[schemas.analysis.Analysis])
def get_analyses_for_recording(
    recording_id: int,
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    min_confidence: Optional[float] = Query(0.0, ge=0.0, le=1.0),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get all analyses for a specific recording.
    """
    # Get recording to check permissions
    recording = crud.recording.get(db, id=recording_id)
    if not recording:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recording not found",
        )
    
    # Check permissions
    if recording.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to access this recording's analyses",
        )
    
    # Get analyses
    analyses = crud.analysis.get_by_recording(
        db, 
        recording_id=recording_id, 
        skip=skip, 
        limit=limit
    )
    
    # Filter by confidence if needed
    if min_confidence > 0:
        analyses = [a for a in analyses if a.confidence >= min_confidence]
    
    return analyses

@router.get("/analyses/confidence-distribution/", response_model=List[Dict[str, float]])
def get_confidence_distribution(
    species: Optional[str] = None,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get confidence score distribution for analyses.
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    results = crud.analysis.get_confidence_distribution(db, species=species)
    return [{"confidence": float(conf), "count": count} for conf, count in results]
