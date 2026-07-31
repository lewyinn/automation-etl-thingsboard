# Automation ETL - APC rPDU Log to ThingsBoard

Script Python untuk otomatisasi proses ETL (Extract, Transform, Load) dari file log APC Rack PDU (rPDU) ke platform IoT ThingsBoard.

## 📁 Struktur Folder

```
AUTOMATION ETL/
├── etl_thingsboard.py            # Script ETL DENGAN KONVERSI (Skala OID /100 dan /10)
├── etl_thingsboard_noconvert.py  # Script ETL TANPA KONVERSI (Nilai mentah asli .txt)
├── document/                     # Folder input file log .txt dari APC rPDU
│   ├── Data_TTCBUARAN_RPDU_A.txt
│   └── Data_TTCBUARAN_RPDU_B.txt
└── csv/                          # Folder output file .csv hasil konversi (otomatis terbuat)
```

---

## 🛠️ Pilihan Script ETL

| Nama File Script | Konversi Skala OID | Format Pengiriman | Cara Jalankan |
|---|---|---|---|
| **`etl_thingsboard.py`** | ✅ Diberlakukan (`/ 100`, `/ 10`) | ⚡ Single Request (Semua Sekaligus) | `python etl_thingsboard.py` |
| **`etl_thingsboard_noconvert.py`** | ❌ Tidak (Nilai Mentah Asli) | ⚡ Single Request (Semua Sekaligus) | `python etl_thingsboard_noconvert.py` |

---

## ⚙️ Cara Kerja ETL Pipeline

1. **Extract** - Membaca file `.txt` log APC rPDU dari folder `document/`, melewati baris metadata dan menyaring tabel data utama.
2. **Transform**:
   - **Timestamp:** Menggabungkan kolom `Date` (`MM/DD/YYYY`) dan `Time` (`HH:MM:SS`) lalu dikonversi ke format **UNIX Epoch Milliseconds** (`ts`).
   - **Metrics & Scaling:**
     - On **`etl_thingsboard.py`**: Nilai mentah dikonversi sesuai spesifikasi OID SNMP APC rPDU (dibagi `100` atau `10`).
     - On **`etl_thingsboard_noconvert.py`**: Nilai mentah diambil langsung dari file `.txt`.
   - **Handling Blank:** Nilai kosong (*blank*) otomatis diisi dengan `0.0`.
   - **CSV Export:** Menyimpan hasil transformasi ke file `.csv` di folder `csv/` menggunakan format delimiter titik-koma (`;`) dan encoding UTF-8 BOM yang kompatibel langsung dengan Microsoft Excel.
3. **Load** - Mengirimkan seluruh payload JSON telemetry sekaligus ke ThingsBoard via REST API Telemetry Controller (`/api/plugins/telemetry/DEVICE/{deviceId}/timeseries/ANY`) dengan autentikasi JWT Token.

---

## 📋 Mapping Kolom & Konversi OID SNMP

| Header CSV | Key Telemetry ThingsBoard | OID Numeric | Konversi (`etl_thingsboard.py`) |
|---|---|---|---|
| Pwr.kW | `rPDU2DeviceStatusPower` | `.1.3.6.1.4.1.318.1.1.26.4.3.1.5.1` | ÷ 100 = kW |
| Pwr Max.kW | `rPDU2DeviceStatusPeakPower` | `.1.3.6.1.4.1.318.1.1.26.4.3.1.6.1` | ÷ 100 = kW |
| Energy.kWh | `rPDU2DeviceStatusEnergy` | `.1.3.6.1.4.1.318.1.1.26.4.3.1.9.1` | ÷ 10 = kWh |
| Temp.C | `rPDU2SensorTempHumidityStatusTempC` | `.1.3.6.1.4.1.318.1.1.26.10.2.2.1.8.1` | ÷ 10 = °C |
| Hum.%RH | `rPDU2SensorTempHumidityStatusRelativeHumidity` | `.1.3.6.1.4.1.318.1.1.26.10.2.2.1.10.1` | Langsung %RH |
| Ph I.A | `rPDU2PhaseStatusCurrent` | `.1.3.6.1.4.1.318.1.1.26.6.3.1.5.1` | ÷ 10 = A |
| Ph I Max.A | `rPDU2PhaseStatusPeakCurrent` | `.1.3.6.1.4.1.318.1.1.26.6.3.1.10.1` | ÷ 10 = A |
| Bank1.A | `rPDU2BankStatusCurrent1` | `.1.3.6.1.4.1.318.1.1.26.8.3.1.5.1` | ÷ 10 = A |
| Bank2.A | `rPDU2BankStatusCurrent2` | `.1.3.6.1.4.1.318.1.1.26.8.3.1.5.2` | ÷ 10 = A |
| Bank1 Max.A | `rPDU2BankStatusPeakCurrent1` | `.1.3.6.1.4.1.318.1.1.26.8.3.1.6.1` | ÷ 10 = A |
| Bank2 Max.A | `rPDU2BankStatusPeakCurrent2` | `.1.3.6.1.4.1.318.1.1.26.8.3.1.6.2` | ÷ 10 = A |

---

## 🚀 Cara Menjalankan

### 1. Install Dependency
```bash
pip install requests
```

### 2. Jalankan Script

**Opsi A: Dengan Konversi Skala OID**
```bash
python etl_thingsboard.py
```

**Opsi B: Tanpa Konversi (Nilai Mentah)**
```bash
python etl_thingsboard_noconvert.py
```

### 3. Input Interactive Terminal
Saat script berjalan, masukkan:
1. Nomor pilihan file `.txt` (misal: `1`)
2. **Device ID** ThingsBoard (UUID)
3. Username & Password ThingsBoard (atau tekan *Enter* untuk default `tenant@thingsboard.org` / `tenant`)

---

## 🔗 Endpoint ThingsBoard REST API yang Digunakan

* **Auth Login:** `POST /api/auth/login` (Mendapatkan JWT Bearer Token)
* **Send Telemetry:** `POST /api/plugins/telemetry/DEVICE/{deviceId}/timeseries/ANY`
* **Fetch Keys:** `GET /api/plugins/telemetry/DEVICE/{deviceId}/keys/timeseries`
* **Fetch Values:** `GET /api/plugins/telemetry/DEVICE/{deviceId}/values/timeseries`
