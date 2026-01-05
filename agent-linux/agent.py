import os
import time
import socket
import requests

# ==========================================
# CONFIGURATION
# ==========================================
PROHIBITED_FILE = "/tmp/virus.txt"
SERVER_API_URL = "http://10.0.0.10:5000/api/report"
API_SECRET_KEY = "prethesis"

def send_report_to_server(status, message):
    try:
        payload = {
            "hostname": socket.gethostname(),
            "os": "Linux",
            "status": status,
            "message": message
        }
        headers = {"X-Api-Key": API_SECRET_KEY}
        requests.post(SERVER_API_URL, json=payload, headers=headers, timeout=2)
        print("   -> [REPORT] Da gui bao cao ve Server.")
    except Exception as e:
        print(f"   -> [REPORT] Loi ket noi Server: {e}")

def check_file_drift():
    if os.path.exists(PROHIBITED_FILE):
        return "DRIFT"
    else:
        return "SAFE"

def fix_drift():
    print(f"   [ACTION] Xoa file cam: {PROHIBITED_FILE}...")
    try:
        os.remove(PROHIBITED_FILE)
        return True
    except:
        return False

def run_agent_job():
    print(f"\n[CHECK] Kiem tra file: {PROHIBITED_FILE}...")
    status = check_file_drift()
    
    if status == "SAFE":
        print("   -> OK: He thong sach.")
        send_report_to_server("SAFE", "System Clean")
    else:
        print("   -> CANH BAO: Phat hien file cam!")
        send_report_to_server("DRIFT", f"Found prohibited file: {PROHIBITED_FILE}")
        
        if fix_drift():
            send_report_to_server("SAFE", "Auto-remediation: File deleted")

if __name__ == "__main__":
    print(f"Linux Agent start... Target: {SERVER_API_URL}")
    while True:
        run_agent_job()
        time.sleep(10)