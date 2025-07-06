from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator
from enum import Enum

# Enums
class RecordingStatus(str, Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"

# Base schemas
class RecordingBase(BaseModel):
    file_name: str = Field(..., description="Name of the audio file")
    file_size: int = Field(..., description="Size of the file in bytes")
    file_type: str = Field(..., description="File type/extension (e.g., 'wav', 'mp3')")
    duration: Optional[float] = Field(None, description="Duration of the recording in seconds")
    
    # Location information
    latitude: Optional[float] = Field(None, description="Latitude of the recording location")
    longitude: Optional[float] = Field(None, description="Longitude of the recording location")
    location_name: Optional[str] = Field(None, description="Human-readable location name")
    
    # Device information
    device_id: str = Field(..., description="ID of the device that made the recording")
    device_name: Optional[str] = Field(None, description="Name of the recording device")
    
    class Config:
        orm_mode = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

# Request schemas
class RecordingCreate(RecordingBase):
    file_path: str = Field(..., description="Path where the file is stored on the server")

class RecordingUpdate(BaseModel):
    status: Optional[RecordingStatus] = None
    processing_errors: Optional[Dict[str, Any]] = None
    processed_at: Optional[datetime] = None

# Response schemas
class Recording(RecordingBase):
    id: int
    status: RecordingStatus = Field(default=RecordingStatus.UPLOADED)
    created_at: datetime
    updated_at: datetime
    processed_at: Optional[datetime] = None
    processing_errors: Optional[Dict[str, Any]] = None

# Detection schemas
class DetectionBase(BaseModel):
    species_scientific_name: str = Field(..., description="Scientific name of the detected species")
    species_common_name: Optional[str] = Field(None, description="Common name of the species")
    confidence: float = Field(..., ge=0, le=1, description="Confidence score from 0 to 1")
    start_time: float = Field(..., description="Start time of the detection in seconds")
    end_time: float = Field(..., description="End time of the detection in seconds")
    frequency_min: Optional[float] = Field(None, description="Minimum frequency in Hz")
    frequency_max: Optional[float] = Field(None, description="Maximum frequency in Hz")

class DetectionCreate(DetectionBase):
    recording_id: int = Field(..., description="ID of the parent recording")

class Detection(DetectionBase):
    id: int
    recording_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

# Combined schemas
class RecordingWithDetections(Recording):
    detections: List[Detection] = []

# Query parameters
class RecordingFilter(BaseModel):
    status: Optional[RecordingStatus] = None
    device_id: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    min_confidence: Optional[float] = None
    species: Optional[str] = None
    
    @validator('min_confidence')
    def validate_confidence(cls, v):
        if v is not None and (v < 0 or v > 1):
            raise ValueError("Confidence must be between 0 and 1")
        return v

# File upload
class FileUploadResponse(BaseModel):
    id: int
    file_name: str
    file_path: str
    status: str
    message: Optional[str] = None
