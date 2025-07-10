from sqlalchemy import Column, Integer, String, Float, ForeignKey, Text, DateTime, JSON
from sqlalchemy.orm import relationship
from datetime import datetime

from app.models.base import Base

class Analysis(Base):
    """Database model for storing bird sound analysis results."""
    __tablename__ = "analyses"

    id = Column(Integer, primary_key=True, index=True)
    recording_id = Column(Integer, ForeignKey("recordings.id", ondelete="CASCADE"), nullable=False)
    
    # Detection details
    species = Column(String, index=True, nullable=False)  # Scientific name
    common_name = Column(String, index=True)  # Common name
    confidence = Column(Float, nullable=False)  # Detection confidence (0-1)
    start_time = Column(Float, nullable=False)  # Start time in seconds
    end_time = Column(Float, nullable=False)    # End time in seconds
    
    # Additional metadata
    raw_data = Column(JSON)  # Raw detection data from BirdNET
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    recording = relationship("Recording", back_populates="analyses")
    
    def __repr__(self):
        return f"<Analysis {self.id}: {self.species} ({self.confidence:.2f})>"
    
    def to_dict(self):
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "recording_id": self.recording_id,
            "species": self.species,
            "common_name": self.common_name,
            "confidence": self.confidence,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "raw_data": self.raw_data
        }
