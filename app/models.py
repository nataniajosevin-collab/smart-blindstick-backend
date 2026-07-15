from pydantic import BaseModel, Field
from typing import Optional

class GPSData(BaseModel):
    latitude: float = 0.0
    longitude: float = 0.0
    satellites: int = 0
    speed: float = 0.0
    altitude: float = 0.0
    accuracy: float = 0.0
    gps_fix: bool = Field(default=False, alias="gpsFix")

    class Config:
        allow_population_by_field_name = True

class SensorData(BaseModel):
    device_id: str = Field(default="esp32_001", alias="deviceId")
    ultrasonic: float = 0.0
    tof_left: int = Field(default=0, alias="tofLeft")
    tof_right: int = Field(default=0, alias="tofRight")
    alert_distance: int = Field(default=50, alias="alertDistance")
    battery: float = 100.0
    gps: GPSData

    class Config:
        allow_population_by_field_name = True

class VibrationCommand(BaseModel):
    status: str
    intensity: Optional[int] = 255