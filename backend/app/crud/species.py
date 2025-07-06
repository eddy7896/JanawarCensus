from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, or_

from ..models.recording import Species
from .base import CRUDBase
from ..schemas.species import SpeciesCreate, SpeciesUpdate

class CRUDSpecies(CRUDBase[Species, SpeciesCreate, SpeciesUpdate]):
    """CRUD operations for Species model with additional methods specific to species."""
    
    def get_by_scientific_name(
        self, 
        db: Session, 
        scientific_name: str
    ) -> Optional[Species]:
        """Get a species by its scientific name (case-insensitive)."""
        return (
            db.query(Species)
            .filter(func.lower(Species.scientific_name) == func.lower(scientific_name))
            .first()
        )
    
    def get_by_common_name(
        self, 
        db: Session, 
        common_name: str
    ) -> Optional[Species]:
        """Get a species by its common name (case-insensitive partial match)."""
        return (
            db.query(Species)
            .filter(Species.common_name.ilike(f"%{common_name}%"))
            .first()
        )
    
    def search(
        self, 
        db: Session, 
        query: str,
        *, 
        skip: int = 0, 
        limit: int = 100
    ) -> Tuple[List[Species], int]:
        """
        Search for species by scientific or common name (case-insensitive partial match).
        
        Args:
            db: Database session
            query: Search term
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            Tuple of (list of species, total count)
        """
        search = f"%{query}%"
        
        # Base query
        base_query = db.query(Species).filter(
            or_(
                Species.scientific_name.ilike(search),
                Species.common_name.ilike(search)
            )
        )
        
        # Get total count
        total = base_query.count()
        
        # Apply pagination
        species = (
            base_query
            .order_by(Species.scientific_name)
            .offset(skip)
            .limit(limit)
            .all()
        )
        
        return species, total
    
    def get_with_detection_stats(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
        min_confidence: float = 0.0,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        location: Optional[Tuple[float, float, float]] = None,
        **filters
    ) -> List[Dict[str, Any]]:
        """
        Get species with their detection statistics.
        
        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            min_confidence: Minimum confidence score (0-1)
            date_from: Filter by detection date (inclusive)
            date_to: Filter by detection date (inclusive)
            location: Tuple of (latitude, longitude, radius_km) to filter by location
            **filters: Additional filters to apply
            
        Returns:
            List of dictionaries with species information and detection statistics
        """
        from ..models.recording import Detection
        
        # Start with a subquery for detection statistics
        detection_subq = db.query(
            Detection.species_scientific_name,
            func.count(Detection.id).label("detection_count"),
            func.avg(Detection.confidence).label("avg_confidence"),
            func.min(Detection.created_at).label("first_detected"),
            func.max(Detection.created_at).label("last_detected")
        )
        
        # Apply confidence filter
        detection_subq = detection_subq.filter(Detection.confidence >= min_confidence)
        
        # Apply date range
        if date_from:
            detection_subq = detection_subq.filter(Detection.created_at >= date_from)
        if date_to:
            detection_subq = detection_subq.filter(Detection.created_at <= date_to)
        
        # Filter by location if provided
        if location and len(location) == 3:
            lat, lon, radius_km = location
            # Simple bounding box filter
            lat_range = radius_km / 111.0
            lon_range = radius_km / (111.0 * abs(cos(radians(lat))))
            
            detection_subq = detection_subq.join(
                Detection.recording
            ).filter(
                and_(
                    Detection.recording.has(latitude >= lat - lat_range),
                    Detection.recording.has(latitude <= lat + lat_range),
                    Detection.recording.has(longitude >= lon - lon_range),
                    Detection.recording.has(longitude <= lon + lon_range)
                )
            )
        
        # Apply additional filters
        for key, value in filters.items():
            if value is not None and hasattr(Detection, key):
                detection_subq = detection_subq.filter(getattr(Detection, key) == value)
        
        # Group by species
        detection_subq = detection_subq.group_by(Detection.species_scientific_name)
        
        # Create a subquery
        detection_stats = detection_subq.subquery()
        
        # Join with species table
        query = db.query(
            Species,
            detection_stats.c.detection_count,
            detection_stats.c.avg_confidence,
            detection_stats.c.first_detected,
            detection_stats.c.last_detected
        ).outerjoin(
            detection_stats,
            Species.scientific_name == detection_stats.c.species_scientific_name
        )
        
        # Filter out species with no detections
        query = query.filter(detection_stats.c.detection_count.isnot(None))
        
        # Apply ordering
        query = query.order_by(detection_stats.c.detection_count.desc())
        
        # Apply pagination
        results = query.offset(skip).limit(limit).all()
        
        # Format results
        return [
            {
                "species": species,
                "detection_count": detection_count or 0,
                "avg_confidence": float(avg_confidence or 0),
                "first_detected": first_detected,
                "last_detected": last_detected
            }
            for species, detection_count, avg_confidence, first_detected, last_detected in results
        ]
    
    def get_rare_species(
        self,
        db: Session,
        *,
        threshold_days: int = 30,
        limit: int = 50,
        **filters
    ) -> List[Dict[str, Any]]:
        """
        Get rarely detected species (those with few detections or not seen recently).
        
        Args:
            db: Database session
            threshold_days: Consider species rare if not seen in this many days
            limit: Maximum number of species to return
            **filters: Additional filters to apply
            
        Returns:
            List of rarely detected species with their statistics
        """
        from ..models.recording import Detection
        from sqlalchemy import func, case, text
        from datetime import datetime, timedelta
        
        # Calculate the date threshold
        threshold_date = datetime.utcnow() - timedelta(days=threshold_days)
        
        # Subquery for detection counts
        detection_counts = db.query(
            Detection.species_scientific_name,
            func.count(Detection.id).label("detection_count"),
            func.max(Detection.created_at).label("last_detected")
        ).group_by(Detection.species_scientific_name).subquery()
        
        # Query for rare species
        query = db.query(
            Species,
            detection_counts.c.detection_count,
            detection_counts.c.last_detected,
            case(
                [
                    (detection_counts.c.last_detected.is_(None), True),
                    (detection_counts.c.last_detected < threshold_date, True)
                ],
                else_=False
            ).label("is_rare")
        ).join(
            detection_counts,
            Species.scientific_name == detection_counts.c.species_scientific_name,
            isouter=True
        ).filter(
            or_(
                detection_counts.c.detection_count.is_(None),
                detection_counts.c.detection_count < 5,  # Fewer than 5 detections
                detection_counts.c.last_detected < threshold_date  # Not seen in threshold_days
            )
        )
        
        # Apply additional filters
        for key, value in filters.items():
            if value is not None and hasattr(Species, key):
                query = query.filter(getattr(Species, key) == value)
        
        # Order by detection count and last seen
        query = query.order_by(
            detection_counts.c.detection_count.asc(),
            detection_counts.c.last_detected.asc()
        )
        
        # Apply limit
        results = query.limit(limit).all()
        
        # Format results
        return [
            {
                "species": species,
                "detection_count": detection_count or 0,
                "last_detected": last_detected,
                "is_rare": is_rare
            }
            for species, detection_count, last_detected, is_rare in results
        ]

# Create an instance of CRUDSpecies
species = CRUDSpecies(Species)
