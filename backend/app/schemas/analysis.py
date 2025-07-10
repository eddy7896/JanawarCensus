from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

class AnalysisBase(BaseModel):
    """Base schema for analysis data."""
    recording_id: int
    species: str = Field(..., description="Scientific name of the detected species")
    common_name: Optional[str] = Field(None, description="Common name of the species")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score (0-1)")
    start_time: float = Field(..., ge=0.0, description="Start time in seconds")
    end_time: float = Field(..., ge=0.0, description="End time in seconds")
    raw_data: Optional[Dict[str, Any]] = Field(None, description="Raw detection data from BirdNET")

class AnalysisCreate(AnalysisBase):
    """Schema for creating a new analysis record."""
    pass

class AnalysisUpdate(BaseModel):
    """Schema for updating an analysis record."""
    species: Optional[str] = None
    common_name: Optional[str] = None
    confidence: Optional[float] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    raw_data: Optional[Dict[str, Any]] = None

class AnalysisInDBBase(AnalysisBase):
    """Base schema for analysis stored in the database."""
    id: int
    created_at: datetime

    class Config:
        orm_mode = True

class Analysis(AnalysisInDBBase):
    """Schema for returning analysis data through the API."""
    pass

class AnalysisInDB(AnalysisInDBBase):
    """Schema for analysis data stored in the database."""
    pass

class AnalysisResults(BaseModel):
    """Schema for analysis results with recording information."""
    recording_id: int
    total_detections: int
    detections: list[Analysis]
    analysis_time: datetime = Field(default_factory=datetime.utcnow)

class BatchAnalysisResults(BaseModel):
    """Schema for batch analysis results."""
    total_recordings: int
    successful_analyses: int
    failed_analyses: int
    results: list[AnalysisResults] = []
