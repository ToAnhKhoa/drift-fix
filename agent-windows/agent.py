import subprocess
import time
import ctypes, sys
import socket
import requests

# ==========================================
# CONFIGURATION
# ==========================================
SERVER_URL = "http://10.0.0.10:5000"
API_SECRET_KEY = "prethesis"

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

if not is_admin():
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
    sys.exit()

def get_policy():
    """Tải cấu hình từ Server"""
    try:
        response = requests.get(f"{SERVER_URL}/api/policy", timeout=2)
        if response.status_code == 200:
            data = response.json()
            return data.get("windows") # Lấy phần cấu hình cho Windows
    except:
        return None
    return None

def send_report(status, message):
    try:
        payload = {
            "hostname": socket.gethostname(),
            "os": "Windows",
            "status": status,
            "message": message
        }
        headers = {"X-Api-Key": API_SECRET_KEY}
        requests.post(f"{SERVER_URL}/api/report", json=payload, headers=headers, timeout=2)
        print("   -> [REPORT] Da gui bao cao.")
    except:
        pass

def check_service(service_name):
    try:
        cmd = ["sc", "query", service_name]
        result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
        if "RUNNING" in result.stdout: return "RUNNING"
        elif "STOPPED" in result.stdout: return "STOPPED"
        else: return "UNKNOWN"
    except: return "ERROR"

def fix_drift(service_name):
    print(f"   [ACTION] Dang tat dich vu {service_name}...")
    subprocess.run(f"net stop {service_name}", shell=True, capture_output=True)

def run_agent_job():
    # 1. Tải Policy mới nhất
    print(f"\n[SYNC] Dang tai Policy tu Server...")
    policy = get_policy()
    
    if not policy:
        print("   -> Khong ket noi duoc Server. Dung policy cu...")
        # Fallback nếu mất mạng (Dùng tạm Spooler)
        target_service = "Spooler"
        desired_state = "STOPPED"
    else:
        target_service = policy["service_name"]
        desired_state = policy["desired_state"]
        print(f"   -> Policy: Service '{target_service}' phai '{desired_state}'")

    # 2. Thực thi kiểm tra
    current = check_service(target_service)
    
    if current == desired_state:
        print(f"   -> OK: Tuan thu dung ({current}).")
        send_report("SAFE", f"Service {target_service} is {current}")
    else:
        print(f"   -> DRIFT: Phat hien sai lech! (Dang: {current})")
        send_report("DRIFT", f"Drift detected on {target_service}")
        
        # Tự sửa lỗi
        fix_drift(target_service)

if __name__ == "__main__":
    print(f"Windows Agent (Smart Mode) khoi dong...")
    while True:
        run_agent_job()
        time.sleep(10)