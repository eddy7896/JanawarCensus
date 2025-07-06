from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from ..models.recording import Device, Recording
from .base import CRUDBase
from ..schemas.device import DeviceCreate, DeviceUpdate, DeviceStatus

class CRUDDevice(CRUDBase[Device, DeviceCreate, DeviceUpdate]):
    """CRUD operations for Device model with additional methods specific to devices."""
    
    def get_by_device_id(
        self, 
        db: Session, 
        device_id: str
    ) -> Optional[Device]:
        """Get a device by its device_id (case-insensitive)."""
        return (
            db.query(Device)
            .filter(func.lower(Device.device_id) == func.lower(device_id))
            .first()
        )
    
    def get_status(
        self,
        db: Session,
        device_id: str
    ) -> Dict[str, Any]:
        """
        Get the status of a device including its recent activity.
        
        Args:
            db: Database session
            device_id: ID of the device
            
        Returns:
            Dictionary containing device status information
        """
        device = self.get_by_device_id(db, device_id)
        if not device:
            return {
                "status": DeviceStatus.OFFLINE,
                "last_seen": None,
                "message": "Device not found"
            }
        
        # Check if device is online (seen in the last 15 minutes)
        fifteen_minutes_ago = datetime.utcnow() - timedelta(minutes=15)
        is_online = device.last_seen and device.last_seen >= fifteen_minutes_ago
        
        # Get recording statistics
        recording_stats = db.query(
            func.count(Recording.id).label("total_recordings"),
            func.min(Recording.created_at).label("first_recording"),
            func.max(Recording.created_at).label("last_recording")
        ).filter(
            Recording.device_id == device_id
        ).first()
        
        # Get disk space information if available
        disk_space = None
        if device.disk_space_total and device.disk_space_used is not None:
            disk_space = {
                "total_gb": round(device.disk_space_total / (1024 ** 3), 2),
                "used_gb": round(device.disk_space_used / (1024 ** 3), 2),
                "available_gb": round((device.disk_space_total - device.disk_space_used) / (1024 ** 3), 2),
                "used_percent": round((device.disk_space_used / device.disk_space_total) * 100, 1)
            }
        
        return {
            "device_id": device.device_id,
            "name": device.name,
            "status": DeviceStatus.ONLINE if is_online else DeviceStatus.OFFLINE,
            "last_seen": device.last_seen,
            "location": {
                "name": device.location_name,
                "latitude": device.latitude,
                "longitude": device.longitude
            } if device.latitude and device.longitude else None,
            "recordings": {
                "total": recording_stats.total_recordings or 0,
                "first_recording": recording_stats.first_recording,
                "last_recording": recording_stats.last_recording
            },
            "hardware": {
                "version": device.hardware_version,
                "firmware_version": device.firmware_version
            },
            "disk_space": disk_space,
            "is_active": device.is_active
        }
    
    def update_last_seen(
        self,
        db: Session,
        *,
        db_obj: Device,
        update_data: Optional[Dict[str, Any]] = None
    ) -> Device:
        """Update the last_seen timestamp and optionally other fields."""
        if update_data is None:
            update_data = {}
        
        # Always update last_seen
        update_data["last_seen"] = datetime.utcnow()
        
        return self.update(db, db_obj=db_obj, obj_in=update_data)
    
    def get_device_stats(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = True,
        **filters
    ) -> Dict[str, Any]:
        """
        Get statistics for all devices.
        
        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            active_only: Only include active devices
            **filters: Additional filters to apply
            
        Returns:
            Dictionary containing device statistics
        """
        from ..models.recording import Recording
        
        # Base query
        query = db.query(Device)
        
        # Apply filters
        if active_only:
            query = query.filter(Device.is_active == True)
            
        for key, value in filters.items():
            if value is not None and hasattr(Device, key):
                query = query.filter(getattr(Device, key) == value)
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        devices = query.offset(skip).limit(limit).all()
        
        # Get recording counts for each device
        device_ids = [device.id for device in devices]
        recording_counts = {}
        
        if device_ids:
            counts = db.query(
                Recording.device_id,
                func.count(Recording.id).label("recording_count")
            ).filter(
                Recording.device_id.in_(device_ids)
            ).group_by(
                Recording.device_id
            ).all()
            
            recording_counts = {device_id: count for device_id, count in counts}
        
        # Get online status for each device
        fifteen_minutes_ago = datetime.utcnow() - timedelta(minutes=15)
        
        # Format results
        device_stats = []
        for device in devices:
            is_online = device.last_seen and device.last_seen >= fifteen_minutes_ago
            
            device_stats.append({
                "device_id": device.device_id,
                "name": device.name,
                "status": DeviceStatus.ONLINE if is_online else DeviceStatus.OFFLINE,
                "last_seen": device.last_seen,
                "location": {
                    "name": device.location_name,
                    "latitude": device.latitude,
                    "longitude": device.longitude
                } if device.latitude and device.longitude else None,
                "recording_count": recording_counts.get(device.id, 0),
                "is_active": device.is_active,
                "hardware": {
                    "version": device.hardware_version,
                    "firmware_version": device.firmware_version
                }
            })
        
        return {
            "total": total,
            "devices": device_stats,
            "online_count": sum(1 for d in device_stats if d["status"] == DeviceStatus.ONLINE),
            "offline_count": sum(1 for d in device_stats if d["status"] == DeviceStatus.OFFLINE)
        }
    
    def get_activity_timeline(
        self,
        db: Session,
        device_id: str,
        days: int = 7
    ) -> List[Dict[str, Any]]:
        """
        Get a timeline of device activity.
        
        Args:
            db: Database session
            device_id: ID of the device
            days: Number of days of history to return
            
        Returns:
            List of dictionaries with activity data
        """
        from ..models.recording import Recording
        
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get recording counts by day
        recording_counts = db.query(
            func.date(Recording.created_at).label("date"),
            func.count(Recording.id).label("count")
        ).filter(
            Recording.device_id == device_id,
            Recording.created_at >= start_date,
            Recording.created_at <= end_date
        ).group_by(
            func.date(Recording.created_at)
        ).order_by(
            func.date(Recording.created_at)
        ).all()
        
        # Convert to dictionary for easier lookup
        counts_by_date = {r.date: r.count for r in recording_counts}
        
        # Generate timeline for all days in range
        timeline = []
        current_date = start_date.date()
        
        while current_date <= end_date.date():
            timeline.append({
                "date": current_date.isoformat(),
                "recording_count": counts_by_date.get(current_date, 0)
            })
            current_date += timedelta(days=1)
        
        return timeline
    
    def register_device(
        self,
        db: Session,
        *,
        device_id: str,
        name: Optional[str] = None,
        hardware_version: Optional[str] = None,
        firmware_version: Optional[str] = None,
        location_name: Optional[str] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None
    ) -> Device:
        """
        Register a new device or update an existing one.
        
        Args:
            db: Database session
            device_id: Unique identifier for the device
            name: Human-readable name for the device
            hardware_version: Hardware version string
            firmware_version: Firmware version string
            location_name: Human-readable location name
            latitude: Latitude of the device location
            longitude: Longitude of the device location
            
        Returns:
            The created or updated device
        """
        # Check if device already exists
        device = self.get_by_device_id(db, device_id)
        
        if device:
            # Update existing device
            update_data = {
                "last_seen": datetime.utcnow(),
                "is_active": True
            }
            
            # Only update these fields if they're provided
            if name is not None:
                update_data["name"] = name
            if hardware_version is not None:
                update_data["hardware_version"] = hardware_version
            if firmware_version is not None:
                update_data["firmware_version"] = firmware_version
            if location_name is not None:
                update_data["location_name"] = location_name
            if latitude is not None:
                update_data["latitude"] = latitude
            if longitude is not None:
                update_data["longitude"] = longitude
                
            return self.update(db, db_obj=device, obj_in=update_data)
        else:
            # Create new device
            device_in = {
                "device_id": device_id,
                "name": name or f"Device {device_id[:6]}",
                "hardware_version": hardware_version,
                "firmware_version": firmware_version,
                "location_name": location_name,
                "latitude": latitude,
                "longitude": longitude,
                "is_active": True,
                "last_seen": datetime.utcnow()
            }
            return self.create(db, obj_in=device_in)

# Create an instance of CRUDDevice
device = CRUDDevice(Device)
