from fastapi import APIRouter, HTTPException, Query
from datetime import datetime, timedelta
from app.models import SensorData, VibrationCommand
from app.database import get_database
from app.utils import (
    latest_data, history_data, alert_logs, vibration_status,
    check_alerts, save_alert, update_vibrator
)
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# ==================== ENDPOINT SENSOR ====================
@router.post("/sensors")
async def receive_sensor_data(data: SensorData):
    global latest_data, history_data, vibration_status
    
    logger.info(f"📥 Received sensor data from {data.device_id}")
    
    # Update data terbaru
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
    
    # 🔥 Simpan ke database (dengan error handling)
    try:
        db = get_database()
        if db:
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
            logger.info("💾 Data saved to MongoDB")
        else:
            logger.warning("⚠️ No database connection - data not saved")
    except Exception as e:
        logger.error(f"❌ Error saving to database: {e}")
    
    # Cek alert
    alerts = check_alerts(latest_data)
    for alert in alerts:
        save_alert(data.device_id, alert)
        try:
            db = get_database()
            if db:
                alert_doc = {
                    "device_id": data.device_id,
                    "timestamp": datetime.now(),
                    "type": alert["type"],
                    "distance": alert["distance"],
                    "message": alert["message"],
                    "acknowledged": False
                }
                await db.alert_logs.insert_one(alert_doc)
        except:
            pass
        
    update_vibrator(alerts)
    
    return {
        "status": "success",
        "alerts": alerts,
        "vibration": vibration_status["status"]
    }

# ==================== GET LATEST DATA ====================
@router.get("/sensors")
def get_sensors_dashboard():
    """Get latest sensor data (for dashboard)

    Important: keep response fast (do not touch MongoDB here), because some clients may
    timeout while waiting for the external request.
    """
    return latest_data


@router.get("/sensors/latest")
def get_latest_data():
    return latest_data

# ==================== VIBRATOR ====================
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

# ==================== ALERTS ====================
@router.get("/alerts")
def get_alerts(limit: int = 20):
    if alert_logs:
        return {"total": len(alert_logs), "data": alert_logs[-limit:]}
    return {"message": "No alerts"}

# ==================== STATS ====================
@router.get("/stats")
def get_stats():
    if not history_data:
        return {
            "total_alerts": 0,
            "avg_distance": 0,
            "battery": 100,
            "gps_fix": False,
            "total_readings": 0
        }
    recent = history_data[-10:]
    avg_dist = sum(d.get("ultrasonic", 0) for d in recent) / len(recent)
    return {
        "total_alerts": len(alert_logs),
        "avg_distance": round(avg_dist, 2),
        "battery": latest_data.get("battery", 0),
        "gps_fix": latest_data.get("gps", {}).get("gpsFix", False),
        "total_readings": len(history_data)
    }

# ==================== LOCATION (FOR PARENTS) ====================
@router.get("/location/current/{device_id}")
async def get_current_location(device_id: str):
    try:
        db = get_database()
        if not db:
            return {
                "device_id": device_id,
                "message": "Database not available"
            }
        
        data = await db.sensor_data.find_one(
            {"device_id": device_id},
            sort=[("timestamp", -1)]
        )
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
    except Exception as e:
        logger.error(f"❌ Error getting location: {e}")
        raise HTTPException(status_code=500, detail=str(e))