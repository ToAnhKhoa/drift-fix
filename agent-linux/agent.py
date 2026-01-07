import os
import time
import socket
import requests
import psutil
import platform
import datetime

# ==========================================
# CONFIGURATION
# ==========================================
SERVER_URL = "http://10.0.0.10:5000"
API_SECRET_KEY = "prethesis"

# Cấu hình chu kỳ
CHECK_INTERVAL = 10       # Kiểm tra lỗi mỗi 10 giây
HEARTBEAT_INTERVAL = 1800 # 30 phút (1800s) mới báo cáo SAFE một lần

# Biến lưu thời gian gửi cuối cùng
last_sent_time = 0

# ==========================================
# SYSTEM INFO FUNCTIONS
# ==========================================
def get_os_details():
    """Lấy thông tin chi tiết về bản phân phối Linux"""
    try:
        # Cách lấy thông tin trên các distro hiện đại
        if os.path.exists("/etc/os-release"):
            with open("/etc/os-release") as f:
                info = {}
                for line in f:
                    if "=" in line:
                        k, v = line.strip().split("=", 1)
                        info[k] = v.strip('"')
                return {
                    "full_name": info.get("PRETTY_NAME", "Linux Unknown"),
                    "release": platform.release()
                }
        else:
            return {"full_name": "Linux Generic", "release": platform.release()}
    except:
        return {"full_name": "Linux Unknown", "release": "Unknown"}

def check_critical_ports():
    """Kiểm tra các cổng quan trọng (SSH, Web, SQL)"""
    target_ports = [22, 80, 443, 3306, 8080]
    open_ports = []
    
    for port in target_ports:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(0.5)
        result = sock.connect_ex(('127.0.0.1', port))
        if result == 0:
            open_ports.append(port)
        sock.close()
    return open_ports

def get_system_metrics():
    try:
        cpu = psutil.cpu_percent(interval=1)
        ram = psutil.virtual_memory().percent
        disk = psutil.disk_usage('/').percent
        return {"cpu": cpu, "ram": ram, "disk": disk}
    except:
        return {"cpu": 0, "ram": 0, "disk": 0}

def get_policy():
    try:
        response = requests.get(f"{SERVER_URL}/api/policy", timeout=2)
        if response.status_code == 200:
            data = response.json()
            return data.get("linux")
    except:
        return None
    return None

# ==========================================
# LOGGING & REPORTING
# ==========================================
def write_local_log(action, target, result):
    """Ghi log nội bộ"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] ACTION: {action} | TARGET: {target} | RESULT: {result}\n"
    try:
        with open("/var/log/drift_agent.log", "a") as f:
            f.write(log_line)
    except:
        with open("drift_agent.log", "a") as f:
            f.write(log_line)

def send_report(status, message):
    global last_sent_time
    try:
        metrics = get_system_metrics()
        os_info = get_os_details()
        open_ports = check_critical_ports()
        
        payload = {
            "hostname": socket.gethostname(),
            "os": "Linux",
            "os_full": os_info["full_name"],     # <--- Mới
            "os_release": os_info["release"],    # <--- Mới
            "open_ports": open_ports,            # <--- Mới
            "status": status,
            "message": message,
            "cpu": metrics["cpu"],      
            "ram": metrics["ram"],      
            "disk": metrics["disk"]     
        }
        headers = {"X-Api-Key": API_SECRET_KEY}
        requests.post(f"{SERVER_URL}/api/report", json=payload, headers=headers, timeout=2)
        
        last_sent_time = time.time() # Cập nhật thời gian gửi
        print(f"   -> [REPORT SENT] Status: {status} | CPU: {metrics['cpu']}%")
    except Exception as e:
        print(f"   -> [REPORT ERROR] Failed to send: {e}")

# ==========================================
# MAIN LOGIC
# ==========================================
def run_agent_job():
    global last_sent_time
    print(f"\n[CHECK] Scanning... ({datetime.datetime.now().strftime('%H:%M:%S')})")
    
    policy = get_policy()
    
    if not policy:
        print("   -> Connection failed. Using fallback.")
        target_file = "/tmp/virus.txt"
    else:
        target_file = policy.get("prohibited_file", "/tmp/virus.txt")

    # 1. KIỂM TRA DRIFT
    is_drift = False
    
    if os.path.exists(target_file):
        is_drift = True
        print(f"   -> DRIFT: Found prohibited file '{target_file}'")
        
        # Tự động sửa lỗi (Auto-remediation)
        print("   [ACTION] Deleting file...")
        try:
            os.remove(target_file)
            write_local_log("DELETE_FILE", target_file, "SUCCESS")
            send_report("DRIFT", f"Auto-remediated: Deleted {target_file}")
            return # Gửi báo cáo xong thì return luôn
        except Exception as e:
            write_local_log("DELETE_FILE", target_file, "FAILED")
            send_report("DRIFT", f"Failed to delete {target_file}: {e}")
            return

    # 2. XỬ LÝ HEARTBEAT (Nếu hệ thống SAFE)
    current_time = time.time()
    time_since_last = current_time - last_sent_time

    if is_drift:
        pass # Đã xử lý ở trên
    elif time_since_last >= HEARTBEAT_INTERVAL:
        # Hết thời gian chờ -> Gửi báo cáo định kỳ
        print("   -> Sending Heartbeat...")
        send_report("SAFE", "System Stable (Heartbeat)")
    else:
        # Chưa đến giờ gửi -> Im lặng
        print(f"   -> System SAFE. Next report in {int(HEARTBEAT_INTERVAL - time_since_last)}s")

if __name__ == "__main__":
    print(f"Linux Agent v2.0 Starting... (Heartbeat: {HEARTBEAT_INTERVAL}s)")
    
    # Kiểm tra thư viện psutil ngay khi khởi động
    try:
        import psutil
    except ImportError:
        print("!!! ERROR: Missing 'psutil' library. Please run: sudo pip3 install psutil")
        exit(1)

    while True:
        run_agent_job()
        time.sleep(CHECK_INTERVAL)