import subprocess
import time
import ctypes, sys
import socket
import requests
import psutil
import datetime
import os
import platform

# ==========================================
# STUDENT INFO (PLEASE FILL THIS)
# ==========================================
# Name:  [YOUR NAME HERE]
# Class: [YOUR CLASS HERE]
# ==========================================

# ==========================================
# CONFIGURATION
# ==========================================
SERVER_URL = "http://10.0.0.10:5000"
API_SECRET_KEY = "prethesis"
REDIRECT_IP = "10.0.0.10" # IP of Master Server (Block Page)

# Timers
CHECK_INTERVAL = 10       # Scan every 10s
HEARTBEAT_INTERVAL = 1800 # Report every 30 mins if SAFE

last_sent_time = 0 
HOSTS_PATH = r"C:\Windows\System32\drivers\etc\hosts"

# ==========================================
# HELPER FUNCTIONS
# ==========================================

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

# Elevate permissions if not Admin
if not is_admin():
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
    sys.exit()

def get_policy():
    """Fetch policy from Server"""
    try:
        response = requests.get(f"{SERVER_URL}/api/policy", timeout=2)
        if response.status_code == 200:
            return response.json().get("windows")
    except:
        return None
    return None

def get_os_details():
    """Get detailed OS info"""
    try:
        return {
            "full_name": f"{platform.system()} {platform.release()} ({platform.version()})",
            "release": platform.machine()
        }
    except:
        return {"full_name": "Unknown", "release": "Unknown"}

def check_critical_ports():
    """Scan open ports (80, 443, 3389, 22)"""
    target_ports = [80, 443, 3389, 22]
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
    """Get Hardware Stats"""
    try:
        cpu = psutil.cpu_percent(interval=1)
        ram = psutil.virtual_memory().percent
        disk = psutil.disk_usage('C:\\').percent
        return {"cpu": cpu, "ram": ram, "disk": disk}
    except:
        return {"cpu": 0, "ram": 0, "disk": 0}

def write_local_log(action, target, result):
    """Write action to local log file"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] ACTION: {action} | TARGET: {target} | RESULT: {result}\n"
    try:
        with open("remediation_history.txt", "a") as f:
            f.write(log_line)
    except Exception as e:
        print(f"   -> [LOG ERROR] {e}")

def send_report(status, message):
    global last_sent_time
    try:
        metrics = get_system_metrics()
        os_info = get_os_details()
        open_ports = check_critical_ports()
        
        payload = {
            "hostname": socket.gethostname(),
            "os": "Windows",
            "os_full": os_info["full_name"],
            "os_release": os_info["release"],
            "open_ports": open_ports,
            "status": status,
            "message": message,
            "cpu": metrics["cpu"],
            "ram": metrics["ram"],
            "disk": metrics["disk"]
        }
        headers = {"X-Api-Key": API_SECRET_KEY}
        requests.post(f"{SERVER_URL}/api/report", json=payload, headers=headers, timeout=2)
        
        last_sent_time = time.time()
        print(f"   -> [REPORT SENT] Status: {status} | Msg: {message}")
    except Exception as e:
        print(f"   -> [REPORT FAILED] {e}")

# ==========================================
# REMEDIATION LOGIC
# ==========================================

def check_service(service_name):
    try:
        cmd = ["sc", "query", service_name]
        result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
        if "RUNNING" in result.stdout: return "RUNNING"
        elif "STOPPED" in result.stdout: return "STOPPED"
        else: return "UNKNOWN"
    except: return "ERROR"

def fix_service(service_name, desired_state):
    action = "start" if desired_state == "RUNNING" else "stop"
    print(f"   [ACTION] Attempting to {action} service {service_name}...")
    
    try:
        subprocess.run(f"net {action} {service_name}", shell=True, capture_output=True, check=True)
        write_local_log(f"{action.upper()}_SERVICE", service_name, "SUCCESS") 
        return True
    except:
        write_local_log(f"{action.upper()}_SERVICE", service_name, "FAILED")
        return False

def check_firewall():
    try:
        cmd = "netsh advfirewall show allprofiles state"
        result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
        if "ON" in result.stdout: return "ON"
        return "OFF"
    except: return "UNKNOWN"

def set_firewall(state):
    print(f"   [ACTION] Setting Firewall to {state}...")
    subprocess.run(f"netsh advfirewall set allprofiles state {state}", shell=True, capture_output=True)

def manage_blocked_sites(blocked_list):
    """Update hosts file based on policy list"""
    if blocked_list is None: blocked_list = []
    
    try:
        with open(HOSTS_PATH, 'r') as f:
            lines = f.readlines()

        new_lines = []
        # Filter existing managed lines
        for line in lines:
            if REDIRECT_IP in line:
                parts = line.split()
                if len(parts) >= 2 and parts[1] in blocked_list:
                    new_lines.append(line) # Keep valid blocks
                else:
                    print(f"   [ACTION] Unblocking: {parts[1]}") # Remove old blocks
            else:
                new_lines.append(line) # Keep system lines

        # Add new blocks
        current_content = "".join(new_lines)
        for site in blocked_list:
            if site not in current_content:
                print(f"   [ACTION] Blocking: {site}")
                new_lines.append(f"{REDIRECT_IP}       {site}\n")
        
        # Write back if changed
        if len(lines) != len(new_lines) or any(site not in "".join(lines) for site in blocked_list):
            with open(HOSTS_PATH, 'w') as f:
                f.writelines(new_lines)
            return "UPDATED"
            
        return "NO_CHANGE"

    except Exception as e:
        print(f"   [ERROR] Hosts file error: {e}")
        return "ERROR"

# ==========================================
# MAIN LOOP
# ==========================================
def run_agent_job():
    print(f"\n[CHECK] Scanning... ({datetime.datetime.now().strftime('%H:%M:%S')})")
    
    policy = get_policy()
    if not policy: return

    is_drift = False
    drift_details = []

    # 1. Check Service
    svc_name = policy.get("service_name")
    svc_state = policy.get("desired_state")
    current_svc = check_service(svc_name)
    
    if current_svc != svc_state:
        is_drift = True
        drift_details.append(f"Service {svc_name} drift")
        fix_service(svc_name, svc_state)

    # 2. Check Firewall
    fw_policy = policy.get("firewall")
    current_fw = check_firewall()
    if fw_policy and current_fw != fw_policy:
        is_drift = True
        drift_details.append("Firewall drift")
        set_firewall(fw_policy.lower())

    # 3. Check Blocked Sites (List)
    sites_list = policy.get("blocked_sites", [])
    hosts_status = manage_blocked_sites(sites_list)
    if hosts_status == "UPDATED":
        is_drift = True
        drift_details.append("Updated blocked sites")
    elif hosts_status == "ERROR":
        drift_details.append("Failed to write hosts file")

    # REPORT LOGIC (Event Driven + Heartbeat)
    current_time = time.time()
    time_since_last = current_time - last_sent_time

    if is_drift:
        # Priority: Report immediately
        msg = " | ".join(drift_details)
        send_report("DRIFT", f"Correction applied: {msg}")
    elif time_since_last >= HEARTBEAT_INTERVAL:
        # Heartbeat: Report every 30 mins
        send_report("SAFE", "System Stable (Heartbeat)")
    else:
        # Silent mode
        print(f"   -> System SAFE. Next report in {int(HEARTBEAT_INTERVAL - time_since_last)}s")

if __name__ == "__main__":
    print(f"Windows Agent v2.0 Starting... (Heartbeat: {HEARTBEAT_INTERVAL}s)")
    while True:
        run_agent_job()
        time.sleep(CHECK_INTERVAL)