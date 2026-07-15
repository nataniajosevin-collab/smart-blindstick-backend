from pydantic import BaseModel
from typing import Optional
from datetime import datetime

# ==================== MODEL GPS ====================
class GPSData(BaseModel):
    """Model untuk data GPS"""
    latitude: float = 0.0
    longitude: float = 0.0
    satellites: int = 0
    speed: float = 0.0
    altitude: float = 0.0
    accuracy: float = 0.0
    gps_fix: bool = False

# ==================== MODEL SENSOR ====================
class SensorData(BaseModel):
    """Model untuk data sensor dari ESP32"""
    device_id: str
    ultrasonic: float = 0.0
    tof_left: float = 0.0
    tof_right: float = 0.0
    alert_distance: int = 50
    battery: float = 100.0
    gps: GPSData = GPSData()

# ==================== MODEL VIBRATOR ====================
class VibrationCommand(BaseModel):
    """Model untuk kontrol vibrator"""
    status: str  # "on" atau "off"
    intensity: Optional[int] = 255

# ==================== MODEL USER ====================
class User(BaseModel):
    """Model untuk orang tua / pengguna"""
    username: str
    password: str
    device_id: str
    name: str
    phone: Optional[str] = None
    email: Optional[str] = None

# ==================== MODEL LOCATION ====================
class LocationData(BaseModel):
    """Model untuk tracking lokasi"""
    device_id: str
    latitude: float
    longitude: float
    timestamp: datetime = datetime.now()
    battery: float = 100.0
    gps_fix: bool = False
    speed: float = 0.0
    altitude: float = 0.0