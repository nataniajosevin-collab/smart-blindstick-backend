from fastapi import APIRouter, HTTPException, Query
from datetime import datetime, timedelta
from app.models import SensorData, VibrationCommand
from app.database import get_database
from app.utils import (
    latest_data, history_data, alert_logs, vibration_status,
    check_alerts, save_alert, update_vibrator
)

router = APIRouter()

# ==================== ENDPOINT ROOT ====================
@router.get("/")
def root():
    return {
        "message": "Smart Blind Stick API",
        "status": "running",
        "version": "2.0.0",
        "endpoints": {
            "POST /api/sensors": "Kirim data sensor dari ESP32",
            "GET /api/sensors/latest": "Ambil data sensor terbaru",
            "GET /api/sensors/history": "Ambil history data sensor",
            "POST /api/vibration": "Kontrol motor vibrator",
            "GET /api/vibration/status": "Cek status vibrator",
            "GET /api/alerts": "Ambil log alert",
            "DELETE /api/alerts": "Hapus semua alert",
            "GET /api/stats": "Ambil statistik dashboard",
            "POST /api/test/alert": "Test alert",
            "GET /api/location/current/{device_id}": "Lokasi terkini untuk orang tua",
            "GET /api/location/history/{device_id}": "History lokasi",
            "GET /api/location/route/{device_id}": "Rute perjalanan",
            "GET /api/alerts/active/{device_id}": "Alert aktif yang belum dibaca"
        }
    }

@router.get("/health")
def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }

# ==================== ENDPOINT SENSOR (UNTUK ESP32) ====================
@router.post("/sensors")
async def receive_sensor_data(data: SensorData):
    """
    Terima data sensor dari ESP32 dan simpan ke database
    """
    global latest_data, history_data, vibration_status
    
    db = get_database()
    
    # Update data terbaru
    latest_data = {
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
        "last_update": datetime.now().isoformat()
    }
    
    # Simpan ke history (max 100 data)
    history_data.append(latest_data.copy())
    if len(history_data) > 100:
        history_data.pop(0)
    
    # 🔥 Simpan ke database
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
    
    # Cek alert
    alerts = check_alerts(latest_data)
    
    # Simpan alert ke log dan database
    for alert in alerts:
        save_alert(data.device_id, alert)
        
        # Simpan ke database
        alert_doc = {
            "device_id": data.device_id,
            "timestamp": datetime.now(),
            "type": alert["type"],
            "distance": alert["distance"],
            "message": alert["message"],
            "acknowledged": False
        }
        await db.alert_logs.insert_one(alert_doc)
    
    # Update vibrator
    update_vibrator(alerts)
    
    return {
        "status": "success",
        "message": "Data received and saved",
        "alerts": alerts,
        "vibration": vibration_status["status"],
        "timestamp": datetime.now().isoformat()
    }

# ==================== ENDPOINT GET LATEST DATA ====================
@router.get("/sensors/latest")
def get_latest_data():
    """Ambil data sensor terbaru"""
    if latest_data:
        return latest_data
    return {"message": "No data available", "status": "empty"}

# ==================== ENDPOINT GET HISTORY ====================
@router.get("/sensors/history")
def get_history(limit: int = 20):
    """Ambil history data sensor"""
    if history_data:
        return {
            "total": len(history_data),
            "data": history_data[-limit:]
        }
    return {"message": "No history available", "status": "empty"}

# ==================== ENDPOINT VIBRATOR ====================
@router.post("/vibration")
def control_vibration(command: VibrationCommand):
    """Kontrol motor vibrator"""
    global vibration_status
    
    if command.status not in ["on", "off"]:
        raise HTTPException(
            status_code=400, 
            detail="Status harus 'on' atau 'off'"
        )
    
    vibration_status["status"] = command.status
    vibration_status["intensity"] = command.intensity if command.intensity else 255
    vibration_status["last_command"] = datetime.now().isoformat()
    
    return {
        "status": "success",
        "vibration": vibration_status["status"],
        "intensity": vibration_status["intensity"],
        "message": f"Vibrator turned {command.status}",
        "timestamp": datetime.now().isoformat()
    }

@router.get("/vibration/status")
def get_vibration_status():
    """Cek status vibrator saat ini"""
    return vibration_status

# ==================== ENDPOINT ALERT ====================
@router.get("/alerts")
def get_alerts(limit: int = 20):
    """Ambil log alert"""
    if alert_logs:
        return {
            "total": len(alert_logs),
            "data": alert_logs[-limit:]
        }
    return {"message": "No alerts", "status": "empty"}

@router.delete("/alerts")
def clear_alerts():
    """Hapus semua alert"""
    global alert_logs
    alert_logs = []
    return {"status": "success", "message": "All alerts cleared"}

# ==================== ENDPOINT STATISTIK ====================
@router.get("/stats")
def get_stats():
    """Ambil statistik untuk dashboard"""
    if not history_data:
        return {
            "total_alerts": 0,
            "avg_distance": 0,
            "battery": 0,
            "gps_fix": False,
            "vibration_status": "off",
            "total_readings": 0,
            "last_update": None
        }
    
    recent = history_data[-10:]
    avg_distance = sum(d.get("ultrasonic", 0) for d in recent) / len(recent) if recent else 0
    
    return {
        "total_alerts": len(alert_logs),
        "avg_distance": round(avg_distance, 2),
        "battery": latest_data.get("battery", 0),
        "gps_fix": latest_data.get("gps", {}).get("gps_fix", False),
        "vibration_status": vibration_status["status"],
        "total_readings": len(history_data),
        "last_update": latest_data.get("last_update")
    }

@router.post("/test/alert")
def test_alert():
    """Endpoint untuk test alert"""
    global alert_logs, vibration_status
    
    alert_logs.append({
        "timestamp": datetime.now().isoformat(),
        "device_id": "esp32_001",
        "type": "test",
        "distance": 30,
        "message": "🧪 Test alert berhasil!",
        "acknowledged": False
    })
    
    vibration_status["status"] = "on"
    vibration_status["intensity"] = 255
    
    return {
        "status": "success",
        "message": "Test alert triggered",
        "timestamp": datetime.now().isoformat()
    }

# ==================== 🔥 ENDPOINT UNTUK ORANG TUA ====================

@router.get("/location/current/{device_id}")
async def get_current_location(device_id: str):
    """
    Dapatkan lokasi terkini dari tongkat anak
    Ini yang dilihat orang tua di HP
    """
    db = get_database()
    
    # Ambil data terbaru dari database
    data = await db.sensor_data.find_one(
        {"device_id": device_id},
        sort=[("timestamp", -1)]
    )
    
    if not data:
        raise HTTPException(status_code=404, detail="Device not found")
    
    # Konversi ObjectId ke string
    data["_id"] = str(data["_id"])
    
    return {
        "device_id": device_id,
        "latitude": data.get("gps", {}).get("latitude", 0),
        "longitude": data.get("gps", {}).get("longitude", 0),
        "timestamp": data.get("timestamp"),
        "battery": data.get("battery", 0),
        "gps_fix": data.get("gps", {}).get("gps_fix", False),
        "last_alert": data.get("alert_distance", 0),
        "ultrasonic": data.get("ultrasonic", 0)
    }

@router.get("/location/history/{device_id}")
async def get_location_history(
    device_id: str,
    hours: int = Query(24, description="Jumlah jam terakhir"),
    limit: int = Query(100, description="Maksimal data")
):
    """
    Dapatkan riwayat lokasi (untuk melihat track perjalanan)
    """
    db = get_database()
    
    cutoff_time = datetime.now() - timedelta(hours=hours)
    
    cursor = db.sensor_data.find(
        {
            "device_id": device_id,
            "timestamp": {"$gte": cutoff_time},
            "gps.gps_fix": True
        }
    ).sort("timestamp", -1).limit(limit)
    
    history = []
    async for doc in cursor:
        history.append({
            "latitude": doc.get("gps", {}).get("latitude", 0),
            "longitude": doc.get("gps", {}).get("longitude", 0),
            "timestamp": doc.get("timestamp"),
            "battery": doc.get("battery", 0)
        })
    
    return {
        "device_id": device_id,
        "total": len(history),
        "history": history
    }

@router.get("/location/route/{device_id}")
async def get_route(
    device_id: str,
    hours: int = Query(1, description="Jam terakhir")
):
    """
    Dapatkan rute perjalanan (untuk ditampilkan di map)
    Format: [[lat1, lng1], [lat2, lng2], ...]
    """
    db = get_database()
    
    cutoff = datetime.now() - timedelta(hours=hours)
    cursor = db.sensor_data.find(
        {
            "device_id": device_id,
            "timestamp": {"$gte": cutoff},
            "gps.gps_fix": True
        }
    ).sort("timestamp", 1).limit(200)
    
    route = []
    async for doc in cursor:
        lat = doc.get("gps", {}).get("latitude", 0)
        lng = doc.get("gps", {}).get("longitude", 0)
        if lat != 0 and lng != 0:
            route.append([lat, lng])
    
    return {
        "device_id": device_id,
        "total_points": len(route),
        "route": route
    }

@router.get("/alerts/active/{device_id}")
async def get_active_alerts(device_id: str):
    """
    Dapatkan alert yang belum dibaca/aktif
    """
    db = get_database()
    
    cursor = db.alert_logs.find(
        {
            "device_id": device_id,
            "acknowledged": False
        }
    ).sort("timestamp", -1).limit(10)
    
    alerts = []
    async for doc in cursor:
        alerts.append({
            "id": str(doc["_id"]),
            "timestamp": doc.get("timestamp"),
            "message": doc.get("message"),
            "distance": doc.get("distance"),
            "type": doc.get("type")
        })
    
    return {
        "device_id": device_id,
        "active_alerts": len(alerts),
        "alerts": alerts
    }

@router.post("/alert/acknowledge/{alert_id}")
async def acknowledge_alert(alert_id: str):
    """
    Orang tua sudah melihat alert (mark as read)
    """
    from bson import ObjectId
    
    db = get_database()
    
    try:
        result = await db.alert_logs.update_one(
            {"_id": ObjectId(alert_id)},
            {"$set": {"acknowledged": True}}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Alert not found")
        
        return {"status": "success", "message": "Alert acknowledged"}
    except:
        raise HTTPException(status_code=400, detail="Invalid alert ID")