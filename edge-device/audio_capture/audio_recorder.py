import os
import time
import wave
import json
import pyaudio
import threading
import logging
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('audio_recorder.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AudioRecorder:
    def __init__(self, output_dir=None):
        """Initialize the audio recorder with SSD storage support."""
        # Load environment variables
        load_dotenv()
        
        # Set up directories
        self.ssd_mount_point = Path(os.getenv('SSD_MOUNT_POINT', '/mnt/ssd'))
        self.base_dir = Path(os.getenv('BASE_DATA_DIR', self.ssd_mount_point / 'bird_recorder'))
        self.output_dir = Path(output_dir) if output_dir else Path(os.getenv('RECORDINGS_DIR', self.base_dir / 'recordings'))
        
        # Ensure directories exist with proper permissions
        try:
            self.output_dir.mkdir(parents=True, exist_ok=True, mode=0o755)
            # Set ownership to the current user if not root
            if os.geteuid() != 0:  # Not running as root
                import pwd, grp
                uid = os.getuid()
                gid = os.getgid()
                os.chown(self.output_dir, uid, gid)
        except Exception as e:
            logger.error(f"Error setting up recording directory: {e}")
            raise
        
        # Storage management
        self.max_storage_gb = float(os.getenv('MAX_STORAGE_GB', '400'))
        self.min_free_space_gb = float(os.getenv('SSD_MIN_FREE_GB', '10'))
        self.sync_interval = int(os.getenv('SSD_SYNC_INTERVAL', '60'))
        self.last_sync_time = 0
        
        # Audio configuration
        self.chunk = 1024
        self.format = pyaudio.paInt16
        self.channels = 6  # ReSpeaker 6-mic array
        self.rate = 16000  # Sample rate in Hz
        self.record_seconds = 60  # Record for 1 minute per file
        
        self.recording = False
        self.audio = pyaudio.PyAudio()
        
    def get_recording_filename(self):
        """Generate filename with timestamp and device ID."""
        device_id = os.getenv('DEVICE_ID', 'default')
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return self.output_dir / f"{device_id}_{timestamp}.wav"
    
    def save_metadata(self, filename, gps_data=None):
        """Save metadata as JSON file."""
        metadata = {
            'device_id': os.getenv('DEVICE_ID', 'default'),
            'timestamp': datetime.now().isoformat(),
            'location': gps_data or {},
            'audio_format': {
                'channels': self.channels,
                'sample_width': self.audio.get_sample_size(self.format),
                'frame_rate': self.rate
            }
        }
        
        with open(f"{filename}.json", 'w') as f:
            json.dump(metadata, f, indent=2)
    
    def _force_sync(self):
        """Force sync to disk to prevent data loss."""
        try:
            if hasattr(os, 'sync'):
                os.sync()
            elif os.name == 'posix':
                os.system('sync')
        except Exception as e:
            logger.warning(f"Error syncing to disk: {e}")
    
    def _get_available_space_gb(self, path):
        """Get available space in GB for the filesystem containing path."""
        stat = os.statvfs(path)
        return (stat.f_bavail * stat.f_frsize) / (2**30)  # Convert to GB
    
    def record_audio(self):
        """Record audio from the microphone with SSD optimizations."""
        last_check_time = time.time()
        
        while self.recording:
            try:
                # Check available space before starting a new recording
                current_time = time.time()
                if current_time - last_check_time > 300:  # Check every 5 minutes
                    free_space = self._get_available_space_gb(self.ssd_mount_point)
                    if free_space < self.min_free_space_gb:
                        logger.warning(f"Low disk space: {free_space:.1f}GB free, minimum {self.min_free_space_gb}GB required")
                        self._check_storage()
                    last_check_time = current_time
                
                # Get filename and ensure directory exists (in case of mount changes)
                self.output_dir.mkdir(parents=True, exist_ok=True)
                filename = self.get_recording_filename()
                
                # Force sync to disk periodically
                if time.time() - self.last_sync_time > self.sync_interval:
                    self._force_sync()
                    self.last_sync_time = time.time()
                
                # Start recording
                stream = self.audio.open(
                    format=self.format,
                    channels=self.channels,
                    rate=self.rate,
                    input=True,
                    frames_per_buffer=self.chunk
                )
                
                logger.info(f"Recording to {filename}")
                frames = []
                
                # Record for the specified duration
                for _ in range(0, int(self.rate / self.chunk * self.record_seconds)):
                    if not self.recording:
                        break
                    data = stream.read(self.chunk, exception_on_overflow=False)
                    frames.append(data)
                
                # Stop and close the stream
                stream.stop_stream()
                stream.close()
                
                # Save the recorded data with error handling for SSD
                try:
                    temp_filename = f"{filename}.tmp"
                    with wave.open(temp_filename, 'wb') as wf:
                        wf.setnchannels(self.channels)
                        wf.setsampwidth(self.audio.get_sample_size(self.format))
                        wf.setframerate(self.rate)
                        wf.writeframes(b''.join(frames))
                    
                    # Atomic rename to prevent corruption
                    os.rename(temp_filename, filename)
                    
                    # Sync after writing important files
                    os.sync()
                    
                except IOError as e:
                    logger.error(f"I/O error saving {filename}: {e}")
                    # Check if the SSD is still mounted
                    if not os.path.ismount(self.ssd_mount_point):
                        logger.error(f"SSD not mounted at {self.ssd_mount_point}")
                        # Try to remount (adjust command as needed)
                        try:
                            os.system(f'sudo mount {self.ssd_mount_point}')
                            logger.info("Attempted to remount SSD")
                        except Exception as mount_error:
                            logger.error(f"Failed to remount SSD: {mount_error}")
                    raise
                
                # Save metadata
                self.save_metadata(str(filename))
                logger.info(f"Saved recording: {filename}")
                
            except Exception as e:
                logger.error(f"Error during recording: {e}")
                time.sleep(5)  # Wait before retrying
    
    def start(self):
        """Start the recording thread."""
        if not self.recording:
            self.recording = True
            self.recording_thread = threading.Thread(target=self.record_audio)
            self.recording_thread.daemon = True
            self.recording_thread.start()
            logger.info("Recording started")
    
    def _check_storage(self):
        """Check available storage and clean up old recordings if needed."""
        try:
            # Get disk usage statistics
            total, used, free = shutil.disk_usage(self.base_dir)
            free_gb = free / (2**30)  # Convert to GB
            total_used_gb = used / (2**30)
            
            # Check if we're over the storage limit or running low on space
            if total_used_gb > self.max_storage_gb or free_gb < self.min_free_space_gb:
                logger.warning(f"Storage limit reached ({total_used_gb:.1f}GB used, {free_gb:.1f}GB free). Cleaning up old recordings...")
                
                # Get list of recordings sorted by modification time (oldest first)
                recordings = sorted(self.output_dir.glob('*.wav'), key=os.path.getmtime)
                
                # Delete oldest recordings until we're under the limit
                while (total_used_gb > self.max_storage_gb * 0.9 or free_gb < self.min_free_space_gb) and recordings:
                    try:
                        oldest_recording = recordings.pop(0)
                        metadata_file = Path(f"{oldest_recording}.json")
                        
                        # Delete the recording and its metadata
                        oldest_recording.unlink()
                        if metadata_file.exists():
                            metadata_file.unlink()
                        
                        logger.info(f"Deleted old recording: {oldest_recording}")
                        
                        # Update disk usage
                        total, used, free = shutil.disk_usage(self.base_dir)
                        free_gb = free / (2**30)
                        total_used_gb = used / (2**30)
                        
                    except Exception as e:
                        logger.error(f"Error deleting old recording {oldest_recording}: {e}")
                        break
        
        except Exception as e:
            logger.error(f"Error checking storage: {e}")
    
    def stop(self):
        """Stop the recording."""
        self.recording = False
        if hasattr(self, 'recording_thread'):
            self.recording_thread.join()
        logger.info("Recording stopped")

if __name__ == "__main__":
    # Load environment variables
    load_dotenv()
    
    # Create and start the recorder
    recorder = AudioRecorder("recordings")
    
    try:
        recorder.start()
        # Keep the main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping recording...")
        recorder.stop()
        recorder.audio.terminate()
        print("Recorder stopped and resources released.")
