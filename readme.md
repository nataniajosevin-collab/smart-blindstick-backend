# Smart Blind Stick Backend v2.0

Backend API untuk monitoring tongkat pintar dengan tracking GPS real-time.

## 🚀 Fitur

- ✅ Menerima data sensor dari ESP32
- ✅ Menyimpan data ke MongoDB Atlas (Cloud)
- ✅ Tracking lokasi real-time untuk orang tua
- ✅ Riwayat perjalanan dan rute
- ✅ Notifikasi alert bahaya
- ✅ Kontrol vibrator jarak jauh

## 📡 API Endpoints untuk Orang Tua

| Method | Endpoint | Deskripsi |
|--------|----------|-----------|
| GET | `/api/location/current/{device_id}` | Lokasi terkini |
| GET | `/api/location/history/{device_id}` | Riwayat lokasi |
| GET | `/api/location/route/{device_id}` | Rute perjalanan |
| GET | `/api/alerts/active/{device_id}` | Alert aktif |

## 🚀 Deploy ke Railway

1. Buat akun https://railway.app
2. Hubungkan repository GitHub
3. Tambahkan environment variable `MONGO_URI`
4. Deploy

## 📱 Akses Dashboard

Dashboard orang tua: https://stick-blind-tuner.vercel.app