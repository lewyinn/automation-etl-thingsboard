# Automation ETL - APC rPDU Log to ThingsBoard

Script Python untuk otomatisasi proses ETL (Extract, Transform, Load) dari file log APC Rack PDU (rPDU) ke platform IoT ThingsBoard.

## Struktur Folder

```
AUTOMATION ETL/
├── etl_thingsboard.py          # Script ETL utama dengan pengiriman per batch (100 record/request)
├── etl_thingsboard_nobatch.py  # Script ETL tanpa batching (kirim semua sekaligus)
├── dokument/                   # Folder input file log .txt dari APC rPDU
│   ├── Data_TTCBUARAN_RPDU_A.txt
│   └── Data_TTCBUARAN_RPDU_B.txt
└── csv/                        # Folder output file .csv hasil konversi (otomatis terbuat)
```

## Cara Kerja

1. **Extract** - Membaca file `.txt` log APC rPDU dari folder `dokument/`, melewati baris header dan mengambil data tabel utama.
2. **Transform** - Menggabungkan kolom `Date` dan `Time` lalu dikonversi ke format **UNIX Epoch Milliseconds** untuk `ts`. Semua nama kolom diubah ke nama key telemetry ThingsBoard. Nilai kosong otomatis diisi `0.0`.
3. **Load** - Mengirim data dalam format JSON telemetry ke ThingsBoard via REST API menggunakan Device ID dan autentikasi JWT.

## Mapping Kolom

| Kolom di File .txt | Key Telemetry ThingsBoard |
|---|---|
| Pwr.kW | rPDU2DeviceStatusPower |
| Pwr Max.kW | rPDU2DeviceStatusPeakPower |
| Energy.kWh | rPDU2DeviceStatusEnergy |
| Temp.C | rPDU2SensorTempHumidityStatusTempC |
| Hum.%RH | rPDU2SensorTempHumidityStatusRelativeHumidity |
| Ph I.A | rPDU2PhaseStatusCurrent |
| Ph I Max.A | rPDU2PhaseStatusPeakCurrent |
| Bank I.A 1 | rPDU2BankStatusCurrent1 |
| Bank I.A 2 | rPDU2BankStatusCurrent2 |
| Bank I Max.A 1 | rPDU2BankStatusPeakCurrent1 |
| Bank I Max.A 2 | rPDU2BankStatusPeakCurrent2 |

## Format Output JSON

```json
[
    {
        "ts": 1739154681000,
        "values": {
            "rPDU2DeviceStatusPower": 1.12,
            "rPDU2DeviceStatusPeakPower": 1.15,
            "rPDU2DeviceStatusEnergy": 26927.7
        }
    }
]
```

## Cara Menjalankan

### Install Dependency
```bash
pip install requests
```

### Jalankan Script
```bash
# Dengan batching (direkomendasikan untuk data besar)
python etl_thingsboard.py

# Tanpa batching (kirim sekaligus dalam 1 request)
python etl_thingsboard_nobatch.py
```

Script akan meminta input:
1. Pilih nomor file `.txt` yang ingin diproses
2. Masukkan **Device ID** ThingsBoard (UUID)
3. Masukkan Username dan Password ThingsBoard

## Konfigurasi

Edit variabel berikut di bagian atas script sesuai kebutuhan:

```python
TB_URL = "http://localhost:8081"   # URL ThingsBoard
BATCH_SIZE = 100                   # Jumlah record per request (khusus etl_thingsboard.py)
```

## Endpoint ThingsBoard yang Digunakan

| Tujuan | Method | Endpoint |
|---|---|---|
| Login / Ambil JWT Token | POST | `/api/auth/login` |
| Kirim Telemetry | POST | `/api/plugins/telemetry/DEVICE/{deviceId}/timeseries/ANY` |
| Cek Keys Telemetry | GET | `/api/plugins/telemetry/DEVICE/{deviceId}/keys/timeseries` |
| Ambil Data Historis | GET | `/api/plugins/telemetry/DEVICE/{deviceId}/values/timeseries` |
