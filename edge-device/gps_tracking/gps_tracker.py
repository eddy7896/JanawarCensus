import os
import time
import json
import random
import logging
from datetime import datetime, timedelta
from pathlib import Path
import gpsd

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('gps_tracker.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class GPSTracker:
    def __init__(self, data_dir=None):
        """Initialize the GPS tracker with data directory."""
        # Load environment variables
        from dotenv import load_dotenv
        load_dotenv()
        
        # Set up directories
        self.base_dir = Path(os.getenv('BASE_DATA_DIR', '/var/lib/bird_recorder'))
        self.data_dir = Path(data_dir) if data_dir else Path(os.getenv('GPS_DATA_DIR', self.base_dir / 'gps_data'))
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.running = False
        self.max_gps_logs = 30  # Maximum number of daily GPS log files to keep
        
        # Connect to the local gpsd service
        try:
            gpsd.connect()
            self.gps_available = True
            logger.info("Successfully connected to GPSD")
        except Exception as e:
            self.gps_available = False
            logger.error(f"Failed to connect to GPSD: {e}")
    
    def get_current_location(self):
        """Get current GPS location data."""
        if not self.gps_available:
            return None
            
        try:
            packet = gpsd.get_current()
            if packet.mode >= 2:  # 2D or 3D fix
                return {
                    'timestamp': datetime.utcfromtimestamp(packet.get_time()).isoformat(),
                    'latitude': packet.lat,
                    'longitude': packet.lon,
                    'altitude': packet.alt if hasattr(packet, 'alt') else None,
                    'speed': packet.hspeed if hasattr(packet, 'hspeed') else None,
                    'track': packet.track if hasattr(packet, 'track') else None,
                    'mode': packet.mode,
                    'satellites_used': packet.sats,
                    'error': {
                        'lat': packet.error.get('y', 0),
                        'lon': packet.error.get('x', 0),
                        'alt': packet.error.get('v', 0)
                    } if hasattr(packet, 'error') else {}
                }
            else:
                logger.warning(f"No GPS fix (mode: {packet.mode})")
                return None
                
        except Exception as e:
            logger.error(f"Error getting GPS data: {e}")
            return None
    
    def _cleanup_old_logs(self):
        """Remove old GPS log files to prevent storage issues."""
        try:
            # Get all GPS log files sorted by modification time (oldest first)
            gps_logs = sorted(self.data_dir.glob('gps_*.jsonl'), key=os.path.getmtime)
            
            # Keep only the most recent logs
            while len(gps_logs) > self.max_gps_logs:
                try:
                    old_log = gps_logs.pop(0)
                    old_log.unlink()
                    logger.info(f"Removed old GPS log: {old_log}")
                except Exception as e:
                    logger.error(f"Error removing GPS log {old_log}: {e}")
                    break
        except Exception as e:
            logger.error(f"Error during GPS log cleanup: {e}")
    
    def log_location(self):
        """Log current location to a file with storage management."""
        location = self.get_current_location()
        if location:
            # Create daily log file
            filename = self.data_dir / f"gps_{datetime.utcnow().strftime('%Y%m%d')}.jsonl"
            
            try:
                # Write location data
                with open(filename, 'a') as f:
                    f.write(json.dumps(location) + '\n')
                logger.debug(f"Logged location: {location}")
                
                # Periodically clean up old logs
                if random.random() < 0.01:  # ~1% chance to run cleanup on each location log
                    self._cleanup_old_logs()
                    
            except Exception as e:
                logger.error(f"Error writing GPS data to file: {e}")
        return location
    
    def start_tracking(self, interval=60):
        """Start tracking GPS location at specified interval (in seconds)."""
        if not self.gps_available:
            logger.error("GPS not available. Cannot start tracking.")
            return
            
        self.running = True
        logger.info(f"Starting GPS tracking with {interval} second interval")
        
        try:
            while self.running:
                self.log_location()
                time.sleep(interval)
        except KeyboardInterrupt:
            logger.info("GPS tracking stopped by user")
        except Exception as e:
            logger.error(f"Error in GPS tracking: {e}")
        finally:
            self.running = False
    
    def stop_tracking(self):
        """Stop the GPS tracking."""
        self.running = False
        logger.info("GPS tracking stopped")

if __name__ == "__main__":
    # Create and start the GPS tracker
    gps_tracker = GPSTracker()
    
    if gps_tracker.gps_available:
        try:
            # Test getting a single location
            location = gps_tracker.get_current_location()
            if location:
                print("Current location:")
                print(f"  Latitude: {location['latitude']}")
                print(f"  Longitude: {location['longitude']}")
                print(f"  Altitude: {location['altitude']}m")
                print(f"  Speed: {location['speed']} m/s" if location['speed'] else "  Speed: N/A")
                print(f"  Mode: {location['mode']} ({'No fix' if location['mode'] == 1 else '2D fix' if location['mode'] == 2 else '3D fix'})")
            
            # Start continuous tracking
            print("\nStarting GPS tracking (press Ctrl+C to stop)...")
            gps_tracker.start_tracking(interval=60)
            
        except KeyboardInterrupt:
            print("\nStopping GPS tracking...")
            gps_tracker.stop_tracking()
    else:
        print("GPS not available. Please check your GPS device and gpsd service.")
