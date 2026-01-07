import os
import time
import socket
import requests
import psutil
import datetime

SERVER_URL = "http://10.0.0.10:5000"
API_SECRET_KEY = "prethesis"

def get_policy():
    try:
        response = requests.get(f"{SERVER_URL}/api/policy", timeout=2)
        if response.status_code == 200:
            data = response.json()
            return data.get("linux")
    except:
        return None
    return None

def send_report(status, message):
    try:
        metrics = get_system_metrics()
        
        payload = {
            "hostname": socket.gethostname(),
            "os": "Linux",
            "status": status,
            "message": message,
            "cpu": metrics["cpu"],      
            "ram": metrics["ram"],      
            "disk": metrics["disk"]     
        }
        headers = {"X-Api-Key": API_SECRET_KEY}
        requests.post(f"{SERVER_URL}/api/report", json=payload, headers=headers, timeout=2)
        print(f"   -> [REPORT] Sent. CPU: {metrics['cpu']}% | RAM: {metrics['ram']}%")
    except Exception as e:
        print(f"   -> [REPORT] Failed to send: {e}")
def get_system_metrics():
    try:
        cpu = psutil.cpu_percent(interval=1)
        ram = psutil.virtual_memory().percent
        disk = psutil.disk_usage('/').percent
        return {"cpu": cpu, "ram": ram, "disk": disk}
    except:
        return {"cpu": 0, "ram": 0, "disk": 0}
def run_agent_job():
    print(f"\n[SYNC] Pulling Policy from Server...")
    policy = get_policy()
    
    if not policy:
        print("   -> Connection failed. Using fallback.")
        target_file = "/tmp/virus.txt"
    else:
        target_file = policy["prohibited_file"]
        print(f"   -> Policy: Prohibited file '{target_file}'")

    if os.path.exists(target_file):
        print("   -> WARNING: Violation Detected!")
        send_report("DRIFT", f"Found prohibited file: {target_file}")
        
        print("   [ACTION] Deleting file...")
        try:
            os.remove(target_file)
            print("   -> File deleted.")
            send_report("SAFE", "Auto-remediation success")
        except:
            print("   -> Failed to delete.")
    else:
        print("   -> OK: System Clean.")
        send_report("SAFE", "System Clean")
def write_local_log(action, target, result):
    """Ghi log nội bộ tại máy Agent"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] ACTION: {action} | TARGET: {target} | RESULT: {result}\n"
    
    try:
        with open("/var/log/drift_agent.log", "a") as f: # Lưu hẳn vào thư mục log
            f.write(log_line)
        print(f"   -> [LOG] Written to /var/log/drift_agent.log")
    except:
        # Nếu không có quyền root ghi vào /var/log thì ghi tại chỗ
        with open("drift_agent.log", "a") as f:
            f.write(log_line)
def fix_drift():
    target_file = "/tmp/virus.txt"
    
    print(f"   [ACTION] Deleting file...")
    try:
        os.remove(target_file)
        write_local_log("DELETE_FILE", target_file, "SUCCESS")
        return True
    except:
        write_local_log("DELETE_FILE", target_file, "FAILED")
        return False
if __name__ == "__main__":
    print("Linux Agent (Smart Mode) starting...")
    while True:
        run_agent_job()
        time.sleep(10)