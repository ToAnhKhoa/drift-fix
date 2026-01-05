import subprocess
import time
import ctypes, sys
import socket
import requests 

# ==========================================
# CONFIGURATION
# ==========================================
SERVICE_NAME = "Spooler"
DESIRED_STATE = "STOPPED"
SERVER_API_URL = "http://10.0.0.10:5000/api/report"
API_SECRET_KEY = "prethesis"

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

# Tự động nâng quyền Admin nếu chưa có
if not is_admin():
    print("Dang yeu cau quyen Admin...")
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
    sys.exit()

def send_report_to_server(status, message):
    """Gửi báo cáo về Master Server"""
    try:
        payload = {
            "hostname": socket.gethostname(),
            "ip": socket.gethostbyname(socket.gethostname()),
            "os": "Windows",
            "status": status, # "SAFE" hoặc "DRIFT"
            "message": message
        }
        headers = {"X-Api-Key": API_SECRET_KEY}
        
        # Gửi request POST
        response = requests.post(SERVER_API_URL, json=payload, headers=headers, timeout=2)
        if response.status_code == 200:
            print("   -> [REPORT] Da gui bao cao ve Server thanh cong.")
        else:
            print(f"   -> [REPORT] Loi Server: {response.status_code}")
    except Exception as e:
        print(f"   -> [REPORT] Khong ket noi duoc Server: {e}")

def check_service_status(service_name):
    try:
        cmd = ["sc", "query", service_name]
        result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
        if "RUNNING" in result.stdout:
            return "RUNNING"
        elif "STOPPED" in result.stdout:
            return "STOPPED"
        else:
            return "UNKNOWN"
    except:
        return "ERROR"

def fix_drift(service_name):
    print(f"   [ACTION] Dang tat dich vu {service_name}...")
    try:
        cmd = f"net stop {service_name}"
        subprocess.run(cmd, shell=True, check=True, capture_output=True)
        print(f"   -> Thanh cong!")
        return True
    except:
        print(f"   -> That bai!")
        return False

def run_agent_job():
    print(f"\n[CHECK] Kiem tra dich vu: {SERVICE_NAME}...")
    current_state = check_service_status(SERVICE_NAME)
    
    if current_state == DESIRED_STATE:
        print(f"   -> OK: Trang thai dung ({current_state}).")
        # Gửi báo cáo Xanh
        send_report_to_server("SAFE", f"Service {SERVICE_NAME} is {current_state}")
    else:
        print(f"   -> DRIFT: Phat hien loi! (Dang: {current_state})")
        # Gửi báo cáo Đỏ
        send_report_to_server("DRIFT", f"Service {SERVICE_NAME} is {current_state}")
        
        # Sửa lỗi
        if fix_drift(SERVICE_NAME):
            # Kiểm tra lại
            time.sleep(2)
            if check_service_status(SERVICE_NAME) == DESIRED_STATE:
                send_report_to_server("SAFE", "Auto-remediation success")

if __name__ == "__main__":
    print(f"Khoi dong Agent ket noi toi {SERVER_API_URL}...")
    while True:
        run_agent_job()
        time.sleep(10) # 10 giây báo cáo 1 lần