from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session

from app.models.analysis import Analysis
from app.schemas.analysis import AnalysisCreate, AnalysisUpdate
from app.crud.base import CRUDBase

class CRUDAnalysis(CRUDBase[Analysis, AnalysisCreate, AnalysisUpdate]):
    """CRUD operations for Analysis model"""
    
    def get_by_species(
        self, db: Session, *, species: str, skip: int = 0, limit: int = 100
    ) -> List[Analysis]:
        """Get all analyses for a specific species."""
        return (
            db.query(self.model)
            .filter(self.model.species == species)
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_by_recording(
        self, db: Session, *, recording_id: int, skip: int = 0, limit: int = 100
    ) -> List[Analysis]:
        """Get all analyses for a specific recording."""
        return (
            db.query(self.model)
            .filter(self.model.recording_id == recording_id)
            .order_by(self.model.confidence.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_detected_species(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get a list of all detected species with their detection counts."""
        return (
            db.query(
                self.model.species,
                self.model.common_name,
                db.func.count(self.model.id).label("detection_count")
            )
            .group_by(self.model.species, self.model.common_name)
            .order_by(db.desc("detection_count"))
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_confidence_distribution(
        self, db: Session, *, species: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get confidence score distribution for analyses."""
        query = db.query(
            db.func.round(self.model.confidence * 10) / 10,  # Round to 1 decimal
            db.func.count(self.model.id)
        )
        
        if species:
            query = query.filter(self.model.species == species)
        
        return (
            query.group_by(db.func.round(self.model.confidence * 10) / 10)
            .order_by(db.func.round(self.model.confidence * 10) / 10)
            .all()
        )

# Create a singleton instance
analysis = CRUDAnalysis(Analysis)
