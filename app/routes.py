from fastapi import APIRouter, HTTPException, Query
from datetime import datetime, timedelta
from app.models import SensorData, VibrationCommand
from app.database import get_database
from app.utils import (
    latest_data, history_data, alert_logs, vibration_status,
    check_alerts, save_alert, update_vibrator
)

router = APIRouter()

@router.get("/")
def root():
    return {
        "message": "Smart Blind Stick API Running Successfully",
        "status": "online",
        "version": "2.0.0"
    }

@router.get("/health")
def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# ==================== ENDPOINT UTAMA (ESP32 & HTML DASHBOARD) ====================
@router.post("/sensors")
async def receive_sensor_data(data: SensorData):
    global latest_data, history_data, vibration_status
    db = get_database()
    
    # Update data terbaru dengan format camelCase (Sesuai kebutuhan HTML)
    latest_data = {
        "deviceId": data.device_id,
        "ultrasonic": data.ultrasonic,
        "tofLeft": data.tof_left,
        "tofRight": data.tof_right,
        "alertDistance": data.alert_distance,
        "battery": data.battery,
        "gps": {
            "latitude": data.gps.latitude,
            "longitude": data.gps.longitude,
            "satellites": data.gps.satellites,
            "speed": data.gps.speed,
            "altitude": data.gps.altitude,
            "accuracy": data.gps.accuracy,
            "gpsFix": data.gps.gps_fix
        },
        "timestamp": datetime.now().isoformat()
    }
    
    history_data.append(latest_data.copy())
    if len(history_data) > 100:
        history_data.pop(0)
    
    # Simpan berkas log ke database cloud MongoDB
    sensor_doc = {
        "device_id": data.device_id,
        "ultrasonic": data.ultrasonic,
        "tof_left": data.tof_left,
        "tof_right": data.tof_right,
        "alert_distance": data.alert_distance,
        "battery": data.battery,
        "gps": {
            "latitude": data.gps.latitude,
            "longitude": data.gps.longitude,
            "satellites": data.gps.satellites,
            "speed": data.gps.speed,
            "altitude": data.gps.altitude,
            "accuracy": data.gps.accuracy,
            "gps_fix": data.gps.gps_fix
        },
        "timestamp": datetime.now()
    }
    await db.sensor_data.insert_one(sensor_doc)
    
    # Cek & simpan alert jika ada objek mendekat
    alerts = check_alerts(latest_data)
    for alert in alerts:
        save_alert(data.device_id, alert)
        alert_doc = {
            "device_id": data.device_id,
            "timestamp": datetime.now(),
            "type": alert["type"],
            "distance": alert["distance"],
            "message": alert["message"],
            "acknowledged": False
        }
        await db.alert_logs.insert_one(alert_doc)
        
    update_vibrator(alerts)
    
    return {
        "status": "success",
        "alerts": alerts,
        "vibration": vibration_status["status"]
    }

@router.get("/sensors")
def get_sensors_dashboard():
    """Melayani request GET /api/sensors dari index.html"""
    return latest_data

@router.get("/sensors/latest")
def get_latest_data():
    return latest_data

# ==================== ENDPOINT VIBRATOR & STATS ====================
@router.post("/vibration")
def control_vibration(command: VibrationCommand):
    global vibration_status
    if command.status not in ["on", "off"]:
        raise HTTPException(status_code=400, detail="Status must be 'on' or 'off'")
    
    vibration_status["status"] = command.status
    vibration_status["intensity"] = command.intensity if command.intensity else 255
    vibration_status["last_command"] = datetime.now().isoformat()
    return {"status": "success", "vibration": vibration_status["status"]}

@router.get("/vibration/status")
def get_vibration_status():
    return vibration_status

@router.get("/alerts")
def get_alerts(limit: int = 20):
    return {"total": len(alert_logs), "data": alert_logs[-limit:]} if alert_logs else {"message": "No alerts"}

@router.get("/stats")
def get_stats():
    if not history_data:
        return {"total_alerts": 0, "avg_distance": 0, "battery": 100, "gps_fix": False}
    recent = history_data[-10:]
    avg_dist = sum(d.get("ultrasonic", 0) for d in recent) / len(recent)
    return {
        "total_alerts": len(alert_logs),
        "avg_distance": round(avg_dist, 2),
        "battery": latest_data.get("battery", 0),
        "gps_fix": latest_data.get("gps", {}).get("gpsFix", False)
    }

# ==================== ENDPOINT PANELS ORANG TUA ====================
@router.get("/location/current/{device_id}")
async def get_current_location(device_id: str):
    db = get_database()
    data = await db.sensor_data.find_one({"device_id": device_id}, sort=[("timestamp", -1)])
    if not data:
        raise HTTPException(status_code=404, detail="Device not found")
    return {
        "device_id": device_id,
        "latitude": data.get("gps", {}).get("latitude", 0),
        "longitude": data.get("gps", {}).get("longitude", 0),
        "timestamp": data.get("timestamp"),
        "battery": data.get("battery", 0),
        "gps_fix": data.get("gps", {}).get("gps_fix", False)
    }