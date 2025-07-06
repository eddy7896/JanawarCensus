from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from ..models.recording import Recording, Detection, RecordingStatus
from .base import CRUDBase
from ..schemas.recording import RecordingCreate, RecordingUpdate, RecordingFilter

class CRUDRecording(CRUDBase[Recording, RecordingCreate, RecordingUpdate]):
    """CRUD operations for Recording model with additional methods specific to recordings."""
    
    def get_multi_with_detections(
        self, 
        db: Session, 
        *, 
        skip: int = 0, 
        limit: int = 100,
        filters: Optional[Dict] = None,
        date_filters: Optional[Dict] = None,
        min_confidence: Optional[float] = None,
        species: Optional[str] = None,
        **kwargs
    ) -> Tuple[List[Recording], int]:
        """
        Get multiple recordings with optional filtering and include their detections.
        """
        query = db.query(Recording)
        
        # Apply filters
        if filters:
            for field, value in filters.items():
                if hasattr(Recording, field):
                    query = query.filter(getattr(Recording, field) == value)
        
        # Apply date range filters
        if date_filters:
            if 'date_from' in date_filters:
                query = query.filter(Recording.created_at >= date_filters['date_from'])
            if 'date_to' in date_filters:
                query = query.filter(Recording.created_at <= date_filters['date_to'])
        
        # Apply species filter through detections
        if species:
            query = query.join(Recording.detections).filter(
                or_(
                    Detection.species_scientific_name.ilike(f"%{species}%"),
                    Detection.species_common_name.ilike(f"%{species}%")
                )
            )
        
        # Apply minimum confidence filter
        if min_confidence is not None:
            query = query.join(Recording.detections).filter(
                Detection.confidence >= min_confidence
            )
        
        # Apply additional filters from kwargs
        for key, value in kwargs.items():
            if value is not None and hasattr(Recording, key):
                query = query.filter(getattr(Recording, key) == value)
        
        # Get total count before pagination
        total = query.distinct().count()
        
        # Apply pagination and eager loading of detections
        recordings = (
            query.options(joinedload(Recording.detections))
            .distinct()
            .offset(skip)
            .limit(limit)
            .all()
        )
        
        return recordings, total
    
    def get_with_detections(
        self, 
        db: Session, 
        id: int
    ) -> Optional[Recording]:
        """Get a single recording by ID with its detections."""
        return (
            db.query(Recording)
            .options(joinedload(Recording.detections))
            .filter(Recording.id == id)
            .first()
        )
    
    def get_detection_stats(
        self,
        db: Session,
        recording_id: int
    ) -> Dict[str, Any]:
        """Get statistics about detections for a specific recording."""
        stats = db.query(
            func.count(Detection.id).label("total_detections"),
            func.avg(Detection.confidence).label("avg_confidence"),
            func.min(Detection.confidence).label("min_confidence"),
            func.max(Detection.confidence).label("max_confidence")
        ).filter(
            Detection.recording_id == recording_id
        ).first()
        
        species_count = db.query(
            Detection.species_scientific_name,
            func.count(Detection.id).label("count")
        ).filter(
            Detection.recording_id == recording_id
        ).group_by(
            Detection.species_scientific_name
        ).all()
        
        return {
            "total_detections": stats.total_detections or 0,
            "avg_confidence": float(stats.avg_confidence or 0),
            "min_confidence": float(stats.min_confidence or 0),
            "max_confidence": float(stats.max_confidence or 0),
            "species_count": [
                {"species": s.species_scientific_name, "count": s.count}
                for s in species_count
            ]
        }
    
    def update_status(
        self,
        db: Session,
        *,
        db_obj: Recording,
        status: RecordingStatus,
        error: Optional[str] = None
    ) -> Recording:
        """Update the status of a recording."""
        update_data = {"status": status}
        
        if status == RecordingStatus.PROCESSED:
            update_data["processed_at"] = datetime.utcnow()
        
        if error:
            update_data["processing_errors"] = error
        
        return self.update(db, db_obj=db_obj, obj_in=update_data)
    
    def get_by_device(
        self,
        db: Session,
        device_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[Recording], int]:
        """Get recordings by device ID."""
        query = db.query(Recording).filter(Recording.device_id == device_id)
        total = query.count()
        recordings = query.offset(skip).limit(limit).all()
        return recordings, total

# Create an instance of CRUDRecording
recording = CRUDRecording(Recording)
