import os
import json
import csv
import requests
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOCS_DIR = os.path.join(BASE_DIR, "document")
CSV_DIR = os.path.join(BASE_DIR, "csv")
TB_URL = "http://localhost:8081"

BATCH_SIZE = 500

METRIC_KEYS = {
    2: "rPDU2DeviceStatusPower",
    3: "rPDU2DeviceStatusPeakPower",
    4: "rPDU2DeviceStatusEnergy",
    5: "rPDU2SensorTempHumidityStatusTempC",
    6: "rPDU2SensorTempHumidityStatusRelativeHumidity",
    7: "rPDU2PhaseStatusCurrent",
    8: "rPDU2PhaseStatusPeakCurrent",
    9: "rPDU2BankStatusCurrent1",
    10: "rPDU2BankStatusCurrent2",
    11: "rPDU2BankStatusPeakCurrent1",
    12: "rPDU2BankStatusPeakCurrent2"
}


def parse_float(val):
    if not val:
        return 0.0
    try:
        return float(val.strip())
    except ValueError:
        return 0.0


def to_epoch_ms(date_str, time_str):
    dt = datetime.strptime(f"{date_str.strip()} {time_str.strip()}", "%m/%d/%Y %H:%M:%S")
    return int(dt.timestamp() * 1000)


def get_jwt_token(username, password):
    login_url = f"{TB_URL}/api/auth/login"
    try:
        res = requests.post(login_url, json={"username": username, "password": password})
        if res.status_code == 200:
            return res.json().get("token")
        print(f"[-] Login gagal ({res.status_code}): {res.text}")
        return None
    except Exception as e:
        print(f"[-] Error koneksi login: {e}")
        return None


def process_txt_file(filepath):
    if not os.path.exists(CSV_DIR):
        os.makedirs(CSV_DIR)

    filename = os.path.basename(filepath)
    csv_filename = filename.rsplit(".", 1)[0] + "_converted.csv"
    csv_path = os.path.join(CSV_DIR, csv_filename)
    
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()

    csv_rows = [["Date", "Time"] + list(METRIC_KEYS.values())]
    payload = []

    start_parsing = False
    for line in lines:
        row = line.strip()
        if not row:
            continue

        if row.startswith("Date") and "Pwr.kW" in row:
            start_parsing = True
            continue

        if start_parsing:
            cols = row.split("\t")
            if len(cols) < 2:
                continue

            date_str, time_str = cols[0].strip(), cols[1].strip()
            try:
                ts = to_epoch_ms(date_str, time_str)
            except ValueError:
                continue

            values = {}
            csv_line = [date_str, time_str]

            for idx, key in METRIC_KEYS.items():
                val = cols[idx] if idx < len(cols) else ""
                num = parse_float(val)
                values[key] = num
                csv_line.append(num)

            payload.append({"ts": ts, "values": values})
            csv_rows.append(csv_line)

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(csv_rows)

    return payload, csv_path


def send_telemetry(device_id, token, payload):
    url = f"{TB_URL}/api/plugins/telemetry/DEVICE/{device_id}/timeseries/ANY"
    headers = {
        "Content-Type": "application/json",
        "X-Authorization": f"Bearer {token}"
    }
    
    total = len(payload)
    print(f"\nMengirim {total} data telemetry ke ThingsBoard (Batch per {BATCH_SIZE} record)...")
    
    success_count = 0
    total_batches = (total + BATCH_SIZE - 1) // BATCH_SIZE

    for i in range(0, total, BATCH_SIZE):
        batch = payload[i : i + BATCH_SIZE]
        batch_no = (i // BATCH_SIZE) + 1
        
        try:
            res = requests.post(url, data=json.dumps(batch), headers=headers)
            if res.status_code == 200:
                success_count += len(batch)
                print(f"[+] Batch {batch_no}/{total_batches} ({len(batch)} record): Terkirim [200 OK]")
            else:
                print(f"[-] Batch {batch_no}/{total_batches} gagal ({res.status_code}): {res.text}")
        except Exception as e:
            print(f"[-] Batch {batch_no}/{total_batches} error koneksi: {e}")

    print(f"\n[+] Selesai! Total {success_count}/{total} record telemetry berhasil masuk ke ThingsBoard.")


def main():
    if not os.path.exists(DOCS_DIR):
        print(f"[-] Folder 'dokument' tidak ditemukan: {DOCS_DIR}")
        return

    txt_files = [f for f in os.listdir(DOCS_DIR) if f.endswith(".txt")]
    if not txt_files:
        print("[-] Tidak ada file .txt di folder 'dokument'")
        return

    print("Daftar file .txt:")
    for i, file in enumerate(txt_files, 1):
        print(f"  {i}. {file}")

    try:
        idx = int(input("\nPilih nomor file: ")) - 1
        if idx < 0 or idx >= len(txt_files):
            print("[-] Pilihan tidak valid.")
            return
    except ValueError:
        print("[-] Input harus berupa angka.")
        return

    selected_file = os.path.join(DOCS_DIR, txt_files[idx])
    print(f"\n[+] Memproses: {txt_files[idx]}")

    payload, csv_path = process_txt_file(selected_file)
    print(f"[+] File CSV tersimpan di: {csv_path}")
    print(f"[+] Total record: {len(payload)}")

    print("\nFormat JSON Telemetry (Preview 2 data pertama):")
    print(json.dumps(payload[:2], indent=4))

    device_id = input("\nMasukkan Device ID: ").strip()
    if not device_id:
        print("[-] Device ID tidak boleh kosong.")
        return

    username = input("Username [default: tenant@thingsboard.org]: ").strip() or "tenant@thingsboard.org"
    password = input("Password [default: tenant]: ").strip() or "tenant"

    token = get_jwt_token(username, password)
    if token:
        send_telemetry(device_id, token, payload)


if __name__ == "__main__":
    main()