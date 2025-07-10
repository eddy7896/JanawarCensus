import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
import numpy as np
import librosa
import soundfile as sf
from birdnetlib import Recording
from birdnetlib.analyzer import Analyzer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.crud import crud_analysis, crud_recording
from app.schemas.analysis import AnalysisCreate, Analysis as AnalysisSchema

logger = logging.getLogger(__name__)

class AudioAnalysisService:
    def __init__(self, db: Session):
        self.db = db
        self.analyzer = None
        self._initialize_analyzer()
    
    def _initialize_analyzer(self):
        """Initialize the BirdNET analyzer with configuration."""
        try:
            self.analyzer = Analyzer(
                classifier_labels_path=settings.BIRDNET_CLASSIFIER_LABELS,
                model_path=settings.BIRDNET_MODEL_PATH,
                label_list_path=settings.BIRDNET_LABELS_PATH,
                sensitivity=settings.BIRDNET_SENSITIVITY,
                min_conf=settings.BIRDNET_MIN_CONFIDENCE,
                overlap=settings.BIRDNET_OVERLAP,
                use_gpu=settings.USE_GPU
            )
            logger.info("BirdNET analyzer initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize BirdNET analyzer: {e}")
            raise
    
    async def analyze_recording(self, recording_path: str, recording_id: int) -> Dict:
        """Analyze a single audio recording and save results to the database."""
        if not os.path.exists(recording_path):
            raise FileNotFoundError(f"Recording file not found: {recording_path}")
        
        try:
            # Get recording metadata
            recording = crud_recording.get(self.db, recording_id)
            if not recording:
                raise ValueError(f"Recording with ID {recording_id} not found")
            
            logger.info(f"Starting analysis for recording: {recording_path}")
            
            # Create a temporary WAV file if needed
            temp_wav_path = None
            if not recording_path.lower().endswith('.wav'):
                temp_wav_path = f"{os.path.splitext(recording_path)[0]}_temp.wav"
                self._convert_to_wav(recording_path, temp_wav_path)
                recording_path = temp_wav_path
            
            # Analyze the recording
            detection_list = self._analyze_audio(recording_path)
            
            # Save analysis results
            analysis_results = []
            for detection in detection_list:
                analysis_data = AnalysisCreate(
                    recording_id=recording_id,
                    species=detection['scientific_name'],
                    common_name=detection['common_name'],
                    confidence=float(detection['confidence']),
                    start_time=float(detection['start_time']),
                    end_time=float(detection['end_time']),
                    raw_data=json.dumps(detection)
                )
                analysis = crud_analysis.create(self.db, obj_in=analysis_data)
                analysis_results.append(analysis)
            
            # Update recording status
            recording.analysis_status = "completed"
            recording.analyzed_at = datetime.utcnow()
            self.db.commit()
            
            logger.info(f"Completed analysis for recording {recording_id}. Detected {len(analysis_results)} species.")
            
            return {
                "recording_id": recording_id,
                "detections": [AnalysisSchema.from_orm(r).dict() for r in analysis_results]
            }
            
        except Exception as e:
            logger.error(f"Error analyzing recording {recording_path}: {str(e)}", exc_info=True)
            # Update recording status to failed
            if 'recording' in locals():
                recording.analysis_status = "failed"
                recording.analysis_error = str(e)
                self.db.commit()
            raise
            
        finally:
            # Clean up temporary files
            if temp_wav_path and os.path.exists(temp_wav_path):
                os.remove(temp_wav_path)
    
    def _analyze_audio(self, audio_path: str) -> List[Dict]:
        """Analyze audio file using BirdNET and return detections."""
        if not self.analyzer:
            self._initialize_analyzer()
        
        # Create a Recording object
        recording = Recording(
            self.analyzer,
            audio_path,
            lat=settings.DEFAULT_LATITUDE,
            lon=settings.DEFAULT_LONGITUDE,
            date=datetime.utcnow().strftime("%Y-%m-%d"),
            min_conf=settings.BIRDNET_MIN_CONFIDENCE,
            overlap=settings.BIRDNET_OVERLAP,
            sensitivity=settings.BIRDNET_SENSITIVITY
        )
        
        # Run the analysis
        recording.analyze()
        
        # Process and return detections
        detections = []
        for detection in recording.detections:
            detections.append({
                "scientific_name": detection["scientific_name"],
                "common_name": detection["common_name"],
                "confidence": float(detection["confidence"]),
                "start_time": float(detection["start_time"]),
                "end_time": float(detection["end_time"])
            })
        
        return detections
    
    def _convert_to_wav(self, input_path: str, output_path: str, sample_rate: int = 44100):
        """Convert audio file to WAV format with the specified sample rate."""
        try:
            # Load audio file
            y, sr = librosa.load(input_path, sr=sample_rate, mono=True)
            
            # Save as WAV
            sf.write(output_path, y, sr, format='WAV', subtype='PCM_16')
            
        except Exception as e:
            logger.error(f"Error converting {input_path} to WAV: {str(e)}")
            raise
