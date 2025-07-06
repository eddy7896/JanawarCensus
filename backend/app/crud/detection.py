from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from ..models.recording import Detection
from .base import CRUDBase
from ..schemas.recording import DetectionCreate, DetectionUpdate

class CRUDDetection(CRUDBase[Detection, DetectionCreate, DetectionUpdate]):
    """CRUD operations for Detection model with additional methods specific to detections."""
    
    def get_multi_by_species(
        self, 
        db: Session, 
        species_name: str,
        *, 
        skip: int = 0, 
        limit: int = 100,
        min_confidence: float = 0.0,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        location: Optional[Tuple[float, float, float]] = None,
        **kwargs
    ) -> Tuple[List[Detection], int]:
        """
        Get detections for a specific species with optional filtering.
        
        Args:
            db: Database session
            species_name: Scientific or common name of the species (case-insensitive partial match)
            skip: Number of records to skip
            limit: Maximum number of records to return
            min_confidence: Minimum confidence score (0-1)
            date_from: Filter by detection date (inclusive)
            date_to: Filter by detection date (inclusive)
            location: Tuple of (latitude, longitude, radius_km) to filter by location
            **kwargs: Additional filters
            
        Returns:
            Tuple of (list of detections, total count)
        """
        query = db.query(Detection).join(Detection.recording)
        
        # Filter by species (case-insensitive partial match)
        query = query.filter(
            or_(
                Detection.species_scientific_name.ilike(f"%{species_name}%"),
                Detection.species_common_name.ilike(f"%{species_name}%")
            )
        )
        
        # Filter by confidence
        query = query.filter(Detection.confidence >= min_confidence)
        
        # Filter by date range
        if date_from:
            query = query.filter(Detection.created_at >= date_from)
        if date_to:
            # Add 1 day to include the entire end date
            query = query.filter(Detection.created_at < (date_to + timedelta(days=1)))
        
        # Filter by location (if provided)
        if location and len(location) == 3:
            lat, lon, radius_km = location
            # Simple bounding box filter for initial implementation
            # For production, consider using PostGIS for more accurate distance calculations
            lat_range = radius_km / 111.0  # Approx. 111km per degree latitude
            lon_range = radius_km / (111.0 * abs(cos(radians(lat))))
            
            query = query.filter(
                and_(
                    Detection.recording.has(latitude >= lat - lat_range),
                    Detection.recording.has(latitude <= lat + lat_range),
                    Detection.recording.has(longitude >= lon - lon_range),
                    Detection.recording.has(longitude <= lon + lon_range)
                )
            )
        
        # Apply additional filters
        for key, value in kwargs.items():
            if value is not None and hasattr(Detection, key):
                query = query.filter(getattr(Detection, key) == value)
        
        # Get total count before pagination
        total = query.count()
        
        # Apply pagination and ordering
        detections = (
            query.order_by(Detection.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        
        return detections, total
    
    def get_species_list(
        self,
        db: Session,
        min_confidence: float = 0.0,
        limit: int = 100,
        **filters
    ) -> List[Dict[str, Any]]:
        """
        Get a list of unique species with their detection counts.
        
        Args:
            db: Database session
            min_confidence: Minimum confidence score (0-1)
            limit: Maximum number of species to return
            **filters: Additional filters to apply
            
        Returns:
            List of dictionaries with species information and detection counts
        """
        query = db.query(
            Detection.species_scientific_name,
            Detection.species_common_name,
            func.count(Detection.id).label("detection_count"),
            func.avg(Detection.confidence).label("avg_confidence")
        )
        
        # Apply confidence filter
        query = query.filter(Detection.confidence >= min_confidence)
        
        # Apply additional filters
        for key, value in filters.items():
            if value is not None and hasattr(Detection, key):
                query = query.filter(getattr(Detection, key) == value)
        
        # Group by species and order by detection count
        results = (
            query.group_by(
                Detection.species_scientific_name,
                Detection.species_common_name
            )
            .order_by(func.count(Detection.id).desc())
            .limit(limit)
            .all()
        )
        
        return [
            {
                "scientific_name": r.species_scientific_name,
                "common_name": r.species_common_name,
                "detection_count": r.detection_count,
                "avg_confidence": float(r.avg_confidence or 0)
            }
            for r in results
        ]
    
    def get_detection_timeline(
        self,
        db: Session,
        time_window: str = "day",
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        species: Optional[str] = None,
        **filters
    ) -> List[Dict[str, Any]]:
        """
        Get detection counts over time.
        
        Args:
            db: Database session
            time_window: Time window for grouping ('hour', 'day', 'week', 'month')
            date_from: Start date for the timeline
            date_to: End date for the timeline
            species: Filter by species (scientific or common name)
            **filters: Additional filters to apply
            
        Returns:
            List of dictionaries with time intervals and detection counts
        """
        # Validate time window
        valid_windows = ["hour", "day", "week", "month"]
        if time_window not in valid_windows:
            raise ValueError(f"time_window must be one of {valid_windows}")
        
        # Base query
        query = db.query(
            func.date_trunc(time_window, Detection.created_at).label("time_interval"),
            func.count(Detection.id).label("detection_count")
        )
        
        # Filter by species if provided
        if species:
            query = query.filter(
                or_(
                    Detection.species_scientific_name.ilike(f"%{species}%"),
                    Detection.species_common_name.ilike(f"%{species}%")
                )
            )
        
        # Apply date range
        if date_from:
            query = query.filter(Detection.created_at >= date_from)
        if date_to:
            query = query.filter(Detection.created_at <= date_to)
        
        # Apply additional filters
        for key, value in filters.items():
            if value is not None and hasattr(Detection, key):
                query = query.filter(getattr(Detection, key) == value)
        
        # Group by time interval and order chronologically
        results = (
            query.group_by("time_interval")
            .order_by("time_interval")
            .all()
        )
        
        return [
            {
                "time_interval": r.time_interval.isoformat(),
                "detection_count": r.detection_count
            }
            for r in results
        ]

# Create an instance of CRUDDetection
detection = CRUDDetection(Detection)
