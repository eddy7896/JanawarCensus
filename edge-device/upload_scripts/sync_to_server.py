import os
import paramiko
import logging
from datetime import datetime, timedelta
from pathlib import Path
import json
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('sync_to_server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ServerSynchronizer:
    def __init__(self):
        """Initialize the server synchronizer with configuration from environment variables."""
        load_dotenv()
        
        # Server configuration
        self.server_address = os.getenv('VPS_SERVER_ADDRESS')
        self.server_username = os.getenv('VPS_USERNAME')
        self.server_password = os.getenv('VPS_PASSWORD', '')
        self.ssh_key_path = os.getenv('SSH_KEY_PATH')
        self.server_port = int(os.getenv('VPS_PORT', '22'))
        
        # Local directories
        self.local_recordings_dir = Path(os.getenv('RECORDINGS_DIR', 'recordings'))
        self.local_gps_dir = Path(os.getenv('GPS_DATA_DIR', 'gps_data'))
        
        # Remote directories on the server
        self.remote_base_dir = Path(os.getenv('REMOTE_BASE_DIR', '/home/username/audio_recordings'))
        self.remote_recordings_dir = self.remote_base_dir / 'recordings'
        self.remote_gps_dir = self.remote_base_dir / 'gps_data'
        
        # Create local directories if they don't exist
        self.local_recordings_dir.mkdir(parents=True, exist_ok=True)
        self.local_gps_dir.mkdir(parents=True, exist_ok=True)
        
        # Track successfully synced files
        self.sync_log_file = 'sync_status.json'
        self.synced_files = self._load_sync_status()
    
    def _load_sync_status(self):
        """Load the synchronization status from the log file."""
        if os.path.exists(self.sync_log_file):
            try:
                with open(self.sync_log_file, 'r') as f:
                    return set(json.load(f).get('synced_files', []))
            except Exception as e:
                logger.warning(f"Error loading sync status: {e}")
        return set()
    
    def _save_sync_status(self):
        """Save the current synchronization status to the log file."""
        try:
            with open(self.sync_log_file, 'w') as f:
                json.dump({'synced_files': list(self.synced_files)}, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving sync status: {e}")
    
    def _get_ssh_client(self):
        """Create and return an SSH client connected to the server."""
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        try:
            if self.ssh_key_path and os.path.exists(self.ssh_key_path):
                # Use SSH key authentication if available
                client.connect(
                    self.server_address,
                    port=self.server_port,
                    username=self.server_username,
                    key_filename=self.ssh_key_path
                )
            else:
                # Fall back to password authentication
                client.connect(
                    self.server_address,
                    port=self.server_port,
                    username=self.server_username,
                    password=self.server_password
                )
            return client
        except Exception as e:
            logger.error(f"Failed to connect to server: {e}")
            return None
    
    def _ensure_remote_directories(self, sftp):
        """Ensure that the required remote directories exist."""
        try:
            for directory in [self.remote_recordings_dir, self.remote_gps_dir]:
                try:
                    sftp.stat(str(directory))
                except FileNotFoundError:
                    sftp.mkdir(str(directory), mode=0o755)
        except Exception as e:
            logger.error(f"Error ensuring remote directories: {e}")
            raise
    
    def _upload_file(self, sftp, local_path, remote_path):
        """Upload a single file to the server."""
        try:
            remote_file = str(remote_path)
            sftp.put(str(local_path), remote_file)
            
            # Set appropriate permissions
            sftp.chmod(remote_file, 0o644)
            
            # Add to synced files
            self.synced_files.add(str(local_path.absolute()))
            self._save_sync_status()
            
            logger.info(f"Uploaded {local_path} to {remote_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error uploading {local_path}: {e}")
            return False
    
    def sync_files(self):
        """Synchronize local files with the server."""
        if not all([self.server_address, self.server_username]):
            logger.error("Server configuration is incomplete. Please check your environment variables.")
            return False
        
        client = self._get_ssh_client()
        if not client:
            return False
        
        try:
            # Open SFTP session
            sftp = client.open_sftp()
            
            # Ensure remote directories exist
            self._ensure_remote_directories(sftp)
            
            # Upload new recordings
            for file_type, local_dir, remote_dir in [
                ('recording', self.local_recordings_dir, self.remote_recordings_dir),
                ('gps', self.local_gps_dir, self.remote_gps_dir)
            ]:
                logger.info(f"Checking for new {file_type} files...")
                
                for file_path in local_dir.glob('**/*'):
                    if file_path.is_file() and str(file_path.absolute()) not in self.synced_files:
                        remote_path = remote_dir / file_path.relative_to(local_dir)
                        remote_parent = remote_path.parent
                        
                        # Ensure remote directory exists
                        try:
                            sftp.stat(str(remote_parent))
                        except FileNotFoundError:
                            # Create parent directories if they don't exist
                            parts = remote_parent.parts
                            current_path = Path(parts[0])
                            for part in parts[1:]:
                                current_path = current_path / part
                                try:
                                    sftp.mkdir(str(current_path), mode=0o755)
                                except OSError:
                                    pass  # Directory already exists
                        
                        # Upload the file
                        if self._upload_file(sftp, file_path, remote_path):
                            # Optionally, remove the local file after successful upload
                            # file_path.unlink()
                            pass
            
            return True
            
        except Exception as e:
            logger.error(f"Error during synchronization: {e}")
            return False
            
        finally:
            sftp.close()
            client.close()

def main():
    """Main function to run the synchronization."""
    logger.info("Starting synchronization with server...")
    
    synchronizer = ServerSynchronizer()
    success = synchronizer.sync_files()
    
    if success:
        logger.info("Synchronization completed successfully")
    else:
        logger.error("Synchronization failed")
    
    return 0 if success else 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
