import subprocess
import time
import ctypes, sys
import socket
import requests
import psutil
import datetime
import os

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
def write_local_log(action, target, result):
    """Ghi log nội bộ tại máy Agent"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] ACTION: {action} | TARGET: {target} | RESULT: {result}\n"
    
    try:
        # Ghi vào file local
        with open("remediation_history.txt", "a") as f:
            f.write(log_line)
        print(f"   -> [LOG] Written to local file: remediation_history.txt")
    except Exception as e:
        print(f"   -> [LOG] Error writing local file: {e}")

def fix_drift(service_name):
    print(f"   [ACTION] Stopping service {service_name}...")
    try:
        subprocess.run(f"net stop {service_name}", shell=True, capture_output=True, check=True)
        # Ghi log file
        write_local_log("STOP_SERVICE", service_name, "SUCCESS") 
        return True
    except:
        write_local_log("STOP_SERVICE", service_name, "FAILED")
        return False
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
def check_firewall():
    """Kiểm tra tường lửa đang Bật hay Tắt"""
    try:
        cmd = "netsh advfirewall show allprofiles state"
        result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
        if "ON" in result.stdout: return "ON"
        return "OFF"
    except: return "UNKNOWN"

def set_firewall(state):
    """Cấu hình tường lửa: state = 'ON' hoặc 'OFF'"""
    print(f"   [ACTION] Setting Firewall to {state}...")
    subprocess.run(f"netsh advfirewall set allprofiles state {state}", shell=True, capture_output=True)

# --- LOGIC CHẶN WEB (HOSTS FILE) ---
def block_website(domain):
    """Chặn web bằng cách trỏ về 127.0.0.1 trong file hosts"""
    hosts_path = r"C:\Windows\System32\drivers\etc\hosts"
    entry = f"\n127.0.0.1       {domain}"
    
    if not domain: return # Nếu rỗng thì bỏ qua

    try:
        # Đọc file xem đã chặn chưa
        with open(hosts_path, 'r') as f:
            content = f.read()
        
        if domain in content:
            return "BLOCKED" # Đã chặn rồi
        
        # Nếu chưa chặn thì ghi thêm vào
        print(f"   [ACTION] Blocking website: {domain}...")
        with open(hosts_path, 'a') as f:
            f.write(entry)
        return "BLOCKED"
    except Exception as e:
        print(f"   [ERROR] Cannot edit hosts file: {e}")
        return "ERROR"

# --- HÀM CHẠY CHÍNH ĐÃ ĐƯỢC NÂNG CẤP ---
def run_agent_job():
    print(f"\n[SYNC] Checking Policy...")
    policy = get_policy() # Hàm này giữ nguyên từ bài trước
    
    if not policy: return

    # 1. Xử lý Service (Logic cũ)
    svc_name = policy.get("service_name")
    svc_state = policy.get("desired_state")
    current_svc = check_service(svc_name) # Hàm check_service cũ
    
    if current_svc != svc_state:
        print(f"   -> DRIFT SERVICE: {svc_name} is {current_svc}. Fixing...")
        fix_drift(svc_name) # Cần sửa hàm fix_drift cũ để hỗ trợ cả Start/Stop nếu muốn
    
    # 2. Xử lý Firewall (Logic MỚI)
    fw_policy = policy.get("firewall") # "ON" hoặc "OFF"
    current_fw = check_firewall()
    
    if fw_policy and current_fw != fw_policy:
        print(f"   -> DRIFT FIREWALL: Expected {fw_policy} but got {current_fw}. Fixing...")
        set_firewall(fw_policy.lower()) # netsh dùng on/off thường
        send_report("DRIFT", f"Firewall fixed to {fw_policy}")
    
    # 3. Xử lý Chặn Web (Logic MỚI)
    site_to_block = policy.get("blocked_site")
    if site_to_block:
        block_status = block_website(site_to_block)
        if block_status == "ERROR":
            send_report("DRIFT", f"Failed to block {site_to_block}")

    # Gửi báo cáo định kỳ
    send_report("SAFE", f"Policy Enforced. FW: {current_fw} | Block: {site_to_block}")
if __name__ == "__main__":
    print(f"Windows Agent (Smart Mode) starting...")
    while True:
        run_agent_job()
        time.sleep(10)