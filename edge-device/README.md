# Bird Sound Recorder - Edge Device

This is the edge device component of the Bird Sound Recorder system, designed to run on a Raspberry Pi 4 with a ReSpeaker USB Microphone Array, GPS module, and 4G/WiFi connectivity.

## Hardware Requirements

- Raspberry Pi 4 (recommended 4GB+ RAM)
- ReSpeaker USB Microphone Array
- GPS module (e.g., U-blox NEO-6M)
- 4G HAT or WiFi dongle for internet connectivity
- Adequate power supply (5V/3A recommended)
- MicroSD card (32GB+ recommended for OS)
- **External SSD** (recommended 500GB+ for audio storage)
  - USB 3.0/3.1 Gen 1 SSD enclosure
  - 2.5" or M.2 SATA SSD (recommended: 1TB for extended field use)

## Software Requirements

- Raspberry Pi OS (64-bit) Lite or Desktop
- Python 3.8+
- Required system packages (install with `apt-get`):
  ```
  sudo apt-get update
  sudo apt-get install -y \
    python3-pip \
    python3-venv \
    libportaudio2 \
    portaudio19-dev \
    gpsd \
    gpsd-clients \
    python3-gps \
    libasound2-dev
  ```

## SSD Setup

Before setting up the software, prepare your external SSD:

1. **Format the SSD** (if needed):
   ```bash
   # Identify the SSD (be VERY careful to select the correct device)
   lsblk
   
   # Format as ext4 (replace /dev/sdX with your device)
   sudo mkfs.ext4 /dev/sdX1
   ```

2. **Create a mount point and mount the SSD**:
   ```bash
   # Create mount point
   sudo mkdir -p /mnt/ssd
   
   # Get the SSD's UUID
   sudo blkid
   
   # Add to /etc/fstab for automatic mounting at boot
   # Replace UUID with your SSD's UUID
   echo "UUID=YOUR_SSD_UUID /mnt/ssd ext4 defaults,nofail,noatime,nodiratime 0 2" | sudo tee -a /etc/fstab
   
   # Mount the SSD
   sudo mount -a
   
   # Set proper permissions
   sudo chown -R $USER:$USER /mnt/ssd
   chmod 755 /mnt/ssd
   ```

3. **Enable TRIM for SSD** (recommended for better longevity):
   ```bash
   sudo systemctl enable fstrim.timer
   sudo systemctl start fstrim.timer
   ```

## Setup Instructions

1. **Clone the repository** to your Raspberry Pi:
   ```bash
   git clone <repository-url> /opt/bird_recorder
   cd /opt/bird_recorder/edge-device
   ```

2. **Create and activate a Python virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure the device**:
   ```bash
   cp .env.template .env
   nano .env  # Edit the configuration
   ```
   Update the following settings in the `.env` file:
   - `DEVICE_ID`: A unique identifier for this device
   - `VPS_SERVER_*`: Your VPS server details
   - `SSH_KEY_PATH`: Path to your SSH private key for server authentication

5. **Set up GPSD** (if using a GPS module):
   ```bash
   sudo systemctl enable gpsd.socket
   sudo systemctl start gpsd.socket
   ```

6. **Test the audio recording**:
   ```bash
   python3 audio_capture/audio_recorder.py
   ```
   Press Ctrl+C to stop recording. Check the `recordings` directory for the recorded files.

7. **Test the GPS tracking**:
   ```bash
   python3 gps_tracking/gps_tracker.py
   ```
   Verify that GPS data is being logged to the `gps_data` directory.

8. **Test server synchronization**:
   ```bash
   python3 upload_scripts/sync_to_server.py
   ```
   Check that files are being uploaded to your VPS server.

## Running as a Service

To run the bird recorder as a systemd service:

1. Create a service file:
   ```bash
   sudo nano /etc/systemd/system/bird-recorder.service
   ```

2. Add the following content (adjust paths as needed):
   ```ini
   [Unit]
   Description=Bird Sound Recorder Service
   After=network.target gpsd.service
   
   [Service]
   Type=simple
   User=pi
   WorkingDirectory=/opt/bird_recorder/edge-device
   Environment="PATH=/opt/bird_recorder/edge-device/venv/bin"
   ExecStart=/opt/bird_recorder/edge-device/venv/bin/python bird_recorder_service.py
   Restart=always
   RestartSec=10
   
   [Install]
   WantedBy=multi-user.target
   ```

3. Enable and start the service:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable bird-recorder.service
   sudo systemctl start bird-recorder.service
   ```

4. Check the service status:
   ```bash
   sudo systemctl status bird-recorder.service
   ```

## Directory Structure

```
edge-device/
├── audio_capture/         # Audio recording functionality
│   └── audio_recorder.py
├── gps_tracking/         # GPS tracking functionality
│   └── gps_tracker.py
├── upload_scripts/       # Server synchronization
│   └── sync_to_server.py
├── .env.template        # Configuration template
├── requirements.txt     # Python dependencies
└── bird_recorder_service.py  # Main service
```

## Monitoring and Maintenance

- **SSD Health**:
  ```bash
  # Check SSD health (if supported)
  sudo smartctl -a /dev/sdX
  
  # Check disk space
  df -h /mnt/ssd
  
  # Check disk I/O usage
  iostat -x 1
  ```

- **Logs**: Check the service logs with:
  ```bash
  # Follow logs in real-time
  journalctl -u bird-recorder.service -f
  
  # Check for disk-related errors
  journalctl -u bird-recorder.service | grep -i 'error\|ssd\|disk\|space'
  ```

- **Scheduled Tasks**:
  - The service automatically syncs with the VPS server daily at midnight local time
  - SSD TRIM runs weekly (enabled during setup)
  - Log rotation is handled automatically

- **SSD Maintenance**:
  - Periodically check SSD health with `smartctl`
  - Monitor write amplification with `iostat -x`
  - Consider replacing the SSD if reallocated sectors increase significantly

## Troubleshooting

1. **SSD Not Mounting**:
   - Check if the SSD is detected: `lsblk`
   - Check dmesg for errors: `dmesg | grep -i usb`
   - Verify the mount point exists and has correct permissions
   - Check /etc/fstab for errors: `sudo mount -a`

2. **Audio Recording Issues**:
   - Check if the ReSpeaker is properly connected
   - Run `arecord -l` to list audio devices
   - Ensure the user has permissions to access the audio device
   - Check for USB bandwidth issues (try different USB ports)

3. **GPS Not Working**:
   - Verify the GPS module is properly connected
   - Run `cgps` to check GPS data
   - Ensure gpsd is running: `sudo systemctl status gpsd`
   - Check for GPS signal: `gpsmon`

4. **Sync Failures**:
   - Check internet connectivity
   - Verify SSH keys are properly set up
   - Check server permissions and disk space
   - Verify the SSD is mounted and has sufficient space

5. **Performance Issues**:
   - Check CPU usage: `top` or `htop`
   - Check I/O wait: `iostat -x 1`
   - Monitor temperature: `vcgencmd measure_temp`
   - Check for USB bandwidth saturation

