from datetime import datetime
from sqlalchemy import Column, String, Float, ForeignKey, DateTime, Integer, JSON, Enum
from sqlalchemy.orm import relationship
from ..db.session import Base
from .base import BaseModel
import enum

class RecordingStatus(str, enum.Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"

class Recording(BaseModel):
    """Model for storing audio recording metadata"""
    __tablename__ = "recordings"
    
    # File information
    file_path = Column(String, nullable=False, index=True)
    file_name = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)  # Size in bytes
    file_type = Column(String(10), nullable=False)  # e.g., 'wav', 'mp3'
    duration = Column(Float, nullable=True)  # Duration in seconds
    
    # Location information
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    location_name = Column(String, nullable=True)
    
    # Device information
    device_id = Column(String, nullable=False, index=True)
    device_name = Column(String, nullable=True)
    
    # Processing information
    status = Column(Enum(RecordingStatus), default=RecordingStatus.UPLOADED, nullable=False)
    processed_at = Column(DateTime, nullable=True)
    processing_errors = Column(JSON, nullable=True)
    
    # Relationships
    detections = relationship("Detection", back_populates="recording", cascade="all, delete-orphan")
    analyses = relationship("Analysis", back_populates="recording", cascade="all, delete-orphan")
    
    # Analysis status
    analysis_status = Column(String(20), default="pending", nullable=False)  # pending, processing, completed, failed
    analyzed_at = Column(DateTime, nullable=True)
    analysis_error = Column(String, nullable=True)
    
    def __repr__(self):
        return f"<Recording {self.file_name} ({self.status})>"


class Detection(BaseModel):
    """Model for storing bird species detections in recordings"""
    __tablename__ = "detections"
    
    # Foreign key to recording
    recording_id = Column(Integer, ForeignKey("recordings.id", ondelete="CASCADE"), nullable=False)
    
    # Detection information
    species_scientific_name = Column(String, nullable=False, index=True)
    species_common_name = Column(String, nullable=True)
    confidence = Column(Float, nullable=False)  # Confidence score from 0 to 1
    start_time = Column(Float, nullable=False)  # Start time in seconds
    end_time = Column(Float, nullable=False)    # End time in seconds
    
    # Additional metadata
    frequency_min = Column(Float, nullable=True)  # Minimum frequency in Hz
    frequency_max = Column(Float, nullable=True)  # Maximum frequency in Hz
    
    # Relationships
    recording = relationship("Recording", back_populates="detections")
    
    def __repr__(self):
        return f"<Detection {self.species_common_name or self.species_scientific_name} ({self.confidence:.2f})>"


class Species(BaseModel):
    """Model for storing bird species information"""
    __tablename__ = "species"
    
    scientific_name = Column(String, unique=True, nullable=False, index=True)
    common_name = Column(String, nullable=True, index=True)
    family = Column(String, nullable=True)
    order = Column(String, nullable=True)
    iucn_status = Column(String, nullable=True)  # e.g., 'LC', 'NT', 'VU', 'EN', 'CR'
    
    # Additional metadata
    description = Column(String, nullable=True)
    image_url = Column(String, nullable=True)
    audio_url = Column(String, nullable=True)
    
    def __repr__(self):
        return f"<Species {self.common_name} ({self.scientific_name})>"


class Device(BaseModel):
    """Model for storing edge device information"""
    __tablename__ = "devices"
    
    device_id = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=True)
    description = Column(String, nullable=True)
    location_name = Column(String, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    last_seen = Column(DateTime, nullable=True)
    
    # Hardware information
    hardware_version = Column(String, nullable=True)
    firmware_version = Column(String, nullable=True)
    
    def __repr__(self):
        return f"<Device {self.name or self.device_id}>"
