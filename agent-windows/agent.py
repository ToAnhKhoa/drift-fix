import subprocess
import time
import ctypes, sys
import socket
import requests
import psutil

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

# Yêu cầu quyền Admin (giữ logic cũ)
if not is_admin():
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
    sys.exit()

def get_policy():
    """Pull policy from Server"""
    try:
        response = requests.get(f"{SERVER_URL}/api/policy", timeout=2)
        if response.status_code == 200:
            data = response.json()
            return data.get("windows")
    except:
        return None
    return None

def send_report(status, message):
    try:
        # Lấy thông số phần cứng
        metrics = get_system_metrics()
        
        payload = {
            "hostname": socket.gethostname(),
            "os": "Windows",
            "status": status,
            "message": message,
            "cpu": metrics["cpu"],      # <--- NEW DATA
            "ram": metrics["ram"],      # <--- NEW DATA
            "disk": metrics["disk"]     # <--- NEW DATA
        }
        headers = {"X-Api-Key": API_SECRET_KEY}
        requests.post(f"{SERVER_URL}/api/report", json=payload, headers=headers, timeout=2)
        print(f"   -> [REPORT] Sent. CPU: {metrics['cpu']}% | RAM: {metrics['ram']}%")
    except Exception as e:
        print(f"   -> [REPORT] Failed to send: {e}")

def check_service(service_name):
    try:
        cmd = ["sc", "query", service_name]
        result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
        if "RUNNING" in result.stdout: return "RUNNING"
        elif "STOPPED" in result.stdout: return "STOPPED"
        else: return "UNKNOWN"
    except: return "ERROR"

def fix_drift(service_name):
    print(f"   [ACTION] Stopping service {service_name}...")
    subprocess.run(f"net stop {service_name}", shell=True, capture_output=True)

def run_agent_job():
    print(f"\n[SYNC] Pulling Policy from Server...")
    policy = get_policy()
    
    if not policy:
        print("   -> Connection failed. Using fallback policy.")
        target_service = "Spooler"
        desired_state = "STOPPED"
    else:
        target_service = policy["service_name"]
        desired_state = policy["desired_state"]
        print(f"   -> Policy: Service '{target_service}' must be '{desired_state}'")

    current = check_service(target_service)
    
    if current == desired_state:
        print(f"   -> OK: Compliant ({current}).")
        send_report("SAFE", f"Service {target_service} is {current}")
    else:
        print(f"   -> DRIFT: Violation Detected! (Current: {current})")
        send_report("DRIFT", f"Drift detected on {target_service}")
        
        # Tự sửa lỗi
        fix_drift(target_service)
def get_system_metrics():
    """Get CPU, RAM, Disk usage"""
    try:
        cpu = psutil.cpu_percent(interval=1)
        ram = psutil.virtual_memory().percent
        disk = psutil.disk_usage('C:\\').percent
        return {"cpu": cpu, "ram": ram, "disk": disk}
    except:
        return {"cpu": 0, "ram": 0, "disk": 0}
if __name__ == "__main__":
    print(f"Windows Agent (Smart Mode) starting...")
    while True:
        run_agent_job()
        time.sleep(10)