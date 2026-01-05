import os
import time
import socket
import requests

SERVER_URL = "http://10.0.0.10:5000"
API_SECRET_KEY = "prethesis"

def get_policy():
    try:
        response = requests.get(f"{SERVER_URL}/api/policy", timeout=2)
        if response.status_code == 200:
            data = response.json()
            return data.get("linux") # Lấy phần cấu hình cho Linux
    except:
        return None
    return None

def send_report(status, message):
    try:
        payload = {
            "hostname": socket.gethostname(),
            "os": "Linux",
            "status": status,
            "message": message
        }
        headers = {"X-Api-Key": API_SECRET_KEY}
        requests.post(f"{SERVER_URL}/api/report", json=payload, headers=headers, timeout=2)
        print("   -> [REPORT] Da gui bao cao.")
    except:
        pass

def run_agent_job():
    print(f"\n[SYNC] Dang tai Policy tu Server...")
    policy = get_policy()
    
    if not policy:
        print("   -> Loi ket noi. Dung mac dinh.")
        target_file = "/tmp/virus.txt"
    else:
        target_file = policy["prohibited_file"]
        print(f"   -> Policy: Cam file '{target_file}'")

    # Kiểm tra và Xử lý
    if os.path.exists(target_file):
        print("   -> CANH BAO: Phat hien file cam!")
        send_report("DRIFT", f"Found file {target_file}")
        
        print("   [ACTION] Dang xoa file...")
        try:
            os.remove(target_file)
            send_report("SAFE", "Auto-remediation success")
        except:
            pass
    else:
        print("   -> OK: He thong sach.")
        send_report("SAFE", "System Clean")

if __name__ == "__main__":
    print("Linux Agent (Smart Mode) khoi dong...")
    while True:
        run_agent_job()
        time.sleep(10)