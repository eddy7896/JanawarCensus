#!/usr/bin/env python3
"""
Bird Recorder Service

This is the main service that runs on the Raspberry Pi edge device to:
1. Record audio from the ReSpeaker microphone array
2. Track GPS location
3. Sync recordings to the VPS server on a daily basis
"""

import os
import time
import signal
import logging
import shutil
import threading
from datetime import datetime, time as dt_time, timedelta
from pathlib import Path
from dotenv import load_dotenv

# Import our modules
from audio_capture.audio_recorder import AudioRecorder
from gps_tracking.gps_tracker import GPSTracker
from upload_scripts.sync_to_server import ServerSynchronizer

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bird_recorder_service.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class BirdRecorderService:
    def __init__(self):
        """Initialize the bird recorder service with configurable storage."""
        # Load environment variables
        load_dotenv()
        
        # Set up base directories
        self.base_dir = Path(os.getenv('BASE_DATA_DIR', '/var/lib/bird_recorder'))
        self.log_dir = Path(os.getenv('LOG_DIR', '/var/log/bird_recorder'))
        
        # Create necessary directories
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Configure logging to use the log directory
        log_file = self.log_dir / 'bird_recorder_service.log'
        logging.basicConfig(
            level=os.getenv('LOG_LEVEL', 'INFO'),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        
        # Initialize components with configured paths
        self.audio_recorder = AudioRecorder()  # Uses default from environment
        self.gps_tracker = GPSTracker()  # Uses default from environment
        self.server_sync = ServerSynchronizer()
        
        # Storage management
        self._setup_storage_management()
        
        # Service control
        self.running = False
        self.recording_thread = None
        self.gps_thread = None
        self.sync_thread = None
        
        # Set up signal handlers for clean shutdown
        signal.signal(signal.SIGINT, self.handle_shutdown)
        signal.signal(signal.SIGTERM, self.handle_shutdown)
    
    def start_recording(self):
        """Start the audio recording thread."""
        logger.info("Starting audio recording...")
        self.audio_recorder.start()
    
    def start_gps_tracking(self):
        """Start the GPS tracking thread."""
        if self.gps_tracker.gps_available:
            logger.info("Starting GPS tracking...")
            self.gps_thread = threading.Thread(
                target=self.gps_tracker.start_tracking,
                kwargs={'interval': int(os.getenv('GPS_UPDATE_INTERVAL', '60'))}
            )
            self.gps_thread.daemon = True
            self.gps_thread.start()
        else:
            logger.warning("GPS is not available. GPS tracking will not be started.")
    
    def start_sync_scheduler(self):
        """Start the server sync scheduler thread."""
        sync_interval = int(os.getenv('SYNC_INTERVAL', '86400'))  # Default: 24 hours
        
        def sync_loop():
            while self.running:
                try:
                    # Calculate time until next sync (midnight local time)
                    now = datetime.now()
                    next_sync = (now + timedelta(days=1)).replace(
                        hour=0, minute=0, second=0, microsecond=0
                    )
                    wait_seconds = (next_sync - now).total_seconds()
                    
                    logger.info(f"Next sync scheduled for {next_sync} (in {wait_seconds/3600:.1f} hours)")
                    
                    # Wait until next sync time or until service is stopped
                    while wait_seconds > 0 and self.running:
                        time.sleep(min(60, wait_seconds))  # Sleep in chunks of max 60 seconds
                        wait_seconds = (next_sync - datetime.now()).total_seconds()
                    
                    if self.running:
                        logger.info("Starting scheduled sync with server...")
                        self.server_sync.sync_files()
                
                except Exception as e:
                    logger.error(f"Error in sync scheduler: {e}")
                    time.sleep(300)  # Wait 5 minutes before retrying on error
        
        self.sync_thread = threading.Thread(target=sync_loop)
        self.sync_thread.daemon = True
        self.sync_thread.start()
    
    def _setup_storage_management(self):
        """Set up storage management and monitoring."""
        # Check available storage
        total, used, free = shutil.disk_usage(self.base_dir)
        free_gb = free / (2**30)
        total_gb = total / (2**30)
        
        logger.info(f"Storage: {free_gb:.1f}GB free of {total_gb:.1f}GB ({free_gb/total_gb*100:.1f}% free)")
        
        if free_gb < 1:  # Less than 1GB free
            logger.warning("Low disk space! Consider freeing up space or reducing recording settings.")
    
    def start(self):
        """Start all service components with storage monitoring."""
        if self.running:
            logger.warning("Service is already running")
            return
        
        logger.info("Starting Bird Recorder Service...")
        logger.info(f"Data directory: {self.base_dir}")
        logger.info(f"Log directory: {self.log_dir}")
        
        # Check storage before starting
        try:
            self._setup_storage_management()
        except Exception as e:
            logger.error(f"Storage check failed: {e}")
        
        self.running = True
        
        try:
            # Start GPS tracking
            self.start_gps_tracking()
            
            # Start audio recording
            self.start_recording()
            
            # Start the sync scheduler
            self.start_sync_scheduler()
            
            logger.info("Bird Recorder Service started successfully")
            
            # Keep the main thread alive
            while self.running:
                time.sleep(1)
                
        except Exception as e:
            logger.critical(f"Critical error in service: {e}", exc_info=True)
            self.stop()
    
    def stop(self):
        """Stop all service components."""
        if not self.running:
            return
            
        logger.info("Stopping Bird Recorder Service...")
        self.running = False
        
        # Stop audio recording
        if hasattr(self.audio_recorder, 'stop'):
            self.audio_recorder.stop()
        
        # Stop GPS tracking
        if hasattr(self.gps_tracker, 'stop_tracking'):
            self.gps_tracker.stop_tracking()
        
        # Wait for threads to finish
        if self.gps_thread and self.gps_thread.is_alive():
            self.gps_thread.join(timeout=5)
        
        if self.sync_thread and self.sync_thread.is_alive():
            self.sync_thread.join(timeout=5)
        
        logger.info("Bird Recorder Service stopped")
    
    def handle_shutdown(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"Received shutdown signal {signum}")
        self.stop()

def main():
    """Main entry point for the service."""
    # Check if running as root (required for audio recording)
    if os.geteuid() != 0:
        logger.warning("This service should be run as root for best results")
    
    # Create and start the service
    service = BirdRecorderService()
    
    try:
        service.start()
    except KeyboardInterrupt:
        logger.info("Service stopped by user")
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
    finally:
        service.stop()

if __name__ == "__main__":
    main()
