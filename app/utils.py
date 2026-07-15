from datetime import datetime

# ==================== DATA STORAGE (IN-MEMORY) ====================
latest_data = {
    "deviceId": "esp32_001",
    "ultrasonic": 0.0,
    "tofLeft": 0,
    "tofRight": 0,
    "alertDistance": 50,
    "battery": 100.0,
    "gps": {
        "latitude": -0.9431,
        "longitude": 100.3722,
        "satellites": 0,
        "speed": 0.0,
        "altitude": 0.0,
        "accuracy": 0.0,
        "gpsFix": False
    },
    "lastUpdate": None
}

history_data = []
alert_logs = []

vibration_status = {
    "status": "off", 
    "intensity": 0,
    "last_command": None
}

# ==================== FUNGSI CEK ALERT ====================
def check_alerts(data):
    alerts = []
    alert_distance = data.get("alertDistance", 50)
    
    # Cek sensor Ultrasonic
    ultrasonic = data.get("ultrasonic", 999)
    if 0 < ultrasonic < alert_distance:
        alerts.append({
            "type": "ultrasonic",
            "distance": ultrasonic,
            "message": f"⚠️ Objek terdeteksi pada jarak {ultrasonic:.1f} cm (Ultrasonik)"
        })
    
    # Cek TOF Left (konversi mm ke cm)
    tof_left = data.get("tofLeft", 999) / 10
    if 0 < tof_left < alert_distance:
        alerts.append({
            "type": "tofLeft",
            "distance": tof_left,
            "message": f"⚠️ Objek terdeteksi pada jarak {tof_left:.1f} cm (TOF Kiri)"
        })
    
    # Cek TOF Right (konversi mm ke cm)
    tof_right = data.get("tofRight", 999) / 10
    if 0 < tof_right < alert_distance:
        alerts.append({
            "type": "tofRight",
            "distance": tof_right,
            "message": f"⚠️ Objek terdeteksi pada jarak {tof_right:.1f} cm (TOF Kanan)"
        })
    
    return alerts

# ==================== FUNGSI SAVE ALERT ====================
def save_alert(device_id: str, alert: dict):
    global alert_logs
    alert_logs.append({
        "timestamp": datetime.now().isoformat(),
        "deviceId": device_id,
        **alert,
        "acknowledged": False
    })
    if len(alert_logs) > 50:
        alert_logs.pop(0)

# ==================== FUNGSI UPDATE VIBRATOR ====================
def update_vibrator(alerts):
    global vibration_status
    if alerts:
        vibration_status["status"] = "on"
        vibration_status["intensity"] = 255
    else:
        vibration_status["status"] = "off"
        vibration_status["intensity"] = 0