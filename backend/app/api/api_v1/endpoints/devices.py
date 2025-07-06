from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from .... import crud, schemas, models
from ....core.config import settings
from ....db.session import get_db
from ....core.security import get_current_active_user
from ....schemas.device import Device, DeviceCreate, DeviceUpdate, DeviceStatus, DeviceRegister

router = APIRouter()

@router.post("/register/", response_model=schemas.device.Device)
async def register_device(
    device_in: DeviceRegister,
    db: Session = Depends(get_db)
):
    """
    Register a new device or update an existing one.
    
    This endpoint is called by edge devices to register themselves with the system.
    If the device already exists, its last_seen timestamp will be updated.
    """
    try:
        # Register or update the device
        device = crud.device.register_device(
            db=db,
            device_id=device_in.device_id,
            name=device_in.name,
            hardware_version=device_in.hardware_version,
            firmware_version=device_in.firmware_version,
            location_name=device_in.location_name,
            latitude=device_in.latitude,
            longitude=device_in.longitude
        )
        
        return device
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/{device_id}", response_model=schemas.device.DeviceWithStatus)
def get_device(
    device_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Get device details and status by device ID.
    """
    device = crud.device.get_by_device_id(db, device_id=device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    # Get device status
    status_info = crud.device.get_status(db, device_id=device_id)
    
    # Get activity timeline (last 7 days)
    activity_timeline = crud.device.get_activity_timeline(db, device_id=device_id, days=7)
    
    return {
        **device.__dict__,
        "status_info": status_info,
        "activity_timeline": activity_timeline
    }

@router.get("/", response_model=List[schemas.device.DeviceWithStatus])
def list_devices(
    skip: int = 0,
    limit: int = 100,
    active_only: bool = True,
    status: Optional[DeviceStatus] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    List all devices with optional filtering.
    """
    # Get device statistics
    stats = crud.device.get_device_stats(
        db,
        skip=skip,
        limit=limit,
        active_only=active_only
    )
    
    # Apply status filter if provided
    if status:
        fifteen_minutes_ago = datetime.utcnow() - timedelta(minutes=15)
        
        def is_device_matching_status(device_info):
            if status == DeviceStatus.ONLINE:
                return device_info["status"] == DeviceStatus.ONLINE
            else:  # OFFLINE
                return device_info["status"] == DeviceStatus.OFFLINE
        
        stats["devices"] = [d for d in stats["devices"] if is_device_matching_status(d)]
    
    return stats["devices"]

@router.put("/{device_id}", response_model=schemas.device.Device)
def update_device(
    device_id: str,
    device_in: DeviceUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Update device information.
    """
    device = crud.device.get_by_device_id(db, device_id=device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    # Only admin can deactivate/reactivate devices
    if not current_user.is_superuser and "is_active" in device_in.dict(exclude_unset=True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to update device status"
        )
    
    device = crud.device.update(db, db_obj=device, obj_in=device_in)
    return device

@router.delete("/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_device(
    device_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Delete a device.
    
    Only admin users can delete devices.
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to delete devices"
        )
    
    device = crud.device.get_by_device_id(db, device_id=device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    crud.device.remove(db, id=device.id)
    return None

@router.get("/{device_id}/recordings/", response_model=List[schemas.recording.Recording])
def get_device_recordings(
    device_id: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Get recordings from a specific device.
    """
    # Check if device exists
    device = crud.device.get_by_device_id(db, device_id=device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    # Get recordings for this device
    recordings, total = crud.recording.get_multi(
        db,
        skip=skip,
        limit=limit,
        filters={"device_id": device_id}
    )
    
    return recordings

@router.get("/{device_id}/status/", response_model=Dict[str, Any])
def get_device_status(
    device_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Get detailed status information for a device.
    """
    device = crud.device.get_by_device_id(db, device_id=device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    return crud.device.get_status(db, device_id=device_id)

@router.get("/{device_id}/activity/", response_model=List[Dict[str, Any]])
def get_device_activity(
    device_id: str,
    days: int = Query(7, ge=1, le=365, description="Number of days of activity to return"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Get activity timeline for a device.
    """
    # Check if device exists
    device = crud.device.get_by_device_id(db, device_id=device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    return crud.device.get_activity_timeline(db, device_id=device_id, days=days)
