# utils.py
import requests
import socket
import psutil
import platform
import ctypes
import sys
import datetime
import os
from config import SERVER_URL, API_SECRET_KEY,LOG_FILE

def is_admin():
    try: return ctypes.windll.shell32.IsUserAnAdmin()
    except: return False

def force_admin():
    """Tự động xin quyền Admin nếu chưa có"""
    if not is_admin():
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        sys.exit()

def get_policy():
    """Lấy cấu hình Windows từ Server"""
    try:
        # Gọi API chung, server tự gộp hoặc tách xử lý
        resp = requests.get(f"{SERVER_URL}/api/policy", timeout=2)
        if resp.status_code == 200:
            return resp.json().get("windows")
    except:
        return None
    return None

def get_system_metrics():
    try:
        return {
            "cpu": psutil.cpu_percent(interval=None),
            "ram": psutil.virtual_memory().percent,
            "disk": psutil.disk_usage('C:\\').percent
        }
    except:
        return {"cpu": 0, "ram": 0, "disk": 0}

def get_os_info():
    return {
        "full": f"{platform.system()} {platform.release()}", 
        "rel": platform.machine()
    }
def write_local_log(drift_type, details, action_taken):
    """
    Ghi nhật ký sửa lỗi ra file log.txt
    Format: [Time] | TYPE | Details | Action
    """
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Tạo nội dung log
    log_line = f"[{timestamp}] TYPE: {drift_type} | ISSUE: {details} | FIX: {action_taken}\n"
    
    try:
        # Mở file mode 
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(log_line)
        print(f"   [LOG SAVED] {drift_type} logged to {LOG_FILE}")
    except Exception as e:
        print(f"   [LOG ERROR] Cannot write to file: {e}")
def send_report(status, msg):
    try:
        payload = {
            "hostname": socket.gethostname(),
            "os": "Windows",
            "os_full": get_os_info()["full"],
            "os_release": get_os_info()["rel"],
            "status": status,
            "message": msg,
            "cpu": get_system_metrics()["cpu"],
            "ram": get_system_metrics()["ram"],
            "disk": get_system_metrics()["disk"]
        }
        headers = {"X-Api-Key": API_SECRET_KEY}
        requests.post(f"{SERVER_URL}/api/report", json=payload, headers=headers, timeout=2)
        print(f"   -> [REPORT] Sent: {status}")
    except Exception as e:
        print(f"   -> [REPORT ERROR] {e}")