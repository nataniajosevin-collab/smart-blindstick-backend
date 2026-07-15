from datetime import datetime

# ==================== DATA STORAGE (IN-MEMORY) ====================
# Data terbaru dari ESP32
latest_data = {
    "device_id": "esp32_001",
    "ultrasonic": 0,
    "tof_left": 0,
    "tof_right": 0,
    "alert_distance": 50,
    "battery": 100,
    "gps": {
        "latitude": -6.2088,
        "longitude": 106.8456,
        "satellites": 0,
        "speed": 0,
        "altitude": 0,
        "accuracy": 0,
        "gps_fix": False
    },
    "last_update": None
}

# History data (max 100 data)
history_data = []

# Alert logs (max 50 logs)
alert_logs = []

# Status vibrator
vibration_status = {
    "status": "off", 
    "intensity": 0,
    "last_command": None
}

# ==================== FUNGSI CEK ALERT ====================
def check_alerts(data):
    """
    Cek apakah ada alert berdasarkan data sensor
    
    Args:
        data (dict): Data sensor terbaru
    
    Returns:
        list: Daftar alert yang terdeteksi
    """
    alerts = []
    alert_distance = data.get("alert_distance", 50)
    
    # Cek sensor Ultrasonic
    ultrasonic = data.get("ultrasonic", 999)
    if ultrasonic < alert_distance:
        alerts.append({
            "type": "ultrasonic",
            "distance": ultrasonic,
            "message": f"⚠️ Objek terdeteksi pada jarak {ultrasonic:.1f} cm (Ultrasonik)"
        })
    
    # Cek TOF Left (konversi mm ke cm)
    tof_left = data.get("tof_left", 999) / 10
    if tof_left < alert_distance:
        alerts.append({
            "type": "tof_left",
            "distance": tof_left,
            "message": f"⚠️ Objek terdeteksi pada jarak {tof_left:.1f} cm (TOF Kiri)"
        })
    
    # Cek TOF Right (konversi mm ke cm)
    tof_right = data.get("tof_right", 999) / 10
    if tof_right < alert_distance:
        alerts.append({
            "type": "tof_right",
            "distance": tof_right,
            "message": f"⚠️ Objek terdeteksi pada jarak {tof_right:.1f} cm (TOF Kanan)"
        })
    
    return alerts

# ==================== FUNGSI SAVE ALERT ====================
def save_alert(device_id: str, alert: dict):
    """
    Simpan alert ke log
    
    Args:
        device_id (str): ID perangkat
        alert (dict): Data alert
    """
    global alert_logs
    
    alert_logs.append({
        "timestamp": datetime.now().isoformat(),
        "device_id": device_id,
        **alert,
        "acknowledged": False
    })
    
    # Batasi jumlah log (max 50)
    if len(alert_logs) > 50:
        alert_logs.pop(0)

# ==================== FUNGSI UPDATE VIBRATOR ====================
def update_vibrator(alerts):
    """
    Update status vibrator berdasarkan alert
    
    Args:
        alerts (list): Daftar alert yang terdeteksi
    """
    global vibration_status
    
    if alerts:
        vibration_status["status"] = "on"
        vibration_status["intensity"] = 255
    else:
        vibration_status["status"] = "off"
        vibration_status["intensity"] = 0