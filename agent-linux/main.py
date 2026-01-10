import time
import os
import requests
import json
import platform
import sys

# --- COLORS ---
RED = "\033[91m"
GREEN = "\033[92m"
CYAN = "\033[96m"
RESET = "\033[0m"

# Thêm đường dẫn để tìm thấy folder modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    # Import các module (Đảm bảo file config.py và folder modules đã đủ file)
    from config import SERVER_URL, API_SECRET_KEY, CHECK_INTERVAL
    from modules import utils, ssh_monitor, service_watchdog, file_guard, net_guard, sudo_audit
except ImportError as e:
    print(f"{RED}[CRITICAL] Missing modules: {e}{RESET}")
    sys.exit(1)

def check_root():
    if os.geteuid() != 0:
        print(f"{RED}[ERROR] Must run as root{RESET}")
        sys.exit(1)

def get_system_payload(status, message):
    return {
        "hostname": platform.node(),
        "os": "Linux",
        "status": status,
        "message": message,
        # Đảm bảo module utils có các hàm này
        "cpu": utils.get_cpu_usage(),
        "ram": utils.get_ram_usage(),
        "disk": utils.get_disk_usage()
    }

def fetch_policy():
    try:
        resp = requests.get(f"{SERVER_URL}/api/policy", timeout=3)
        if resp.status_code == 200:
            return resp.json().get("linux", {})
        return {}
    except: 
        return {}

def send_report(status, message):
    try:
        payload = get_system_payload(status, message)
        requests.post(f"{SERVER_URL}/api/report", json=payload, headers={"X-Api-Key": API_SECRET_KEY}, timeout=3)
        
        color = RED if status == "DRIFT" else GREEN
        print(f" -> [REPORT] Sent: {color}{status}{RESET}")
    except Exception as e:
        print(f" -> [REPORT ERROR] {e}")

def main():
    check_root()
    print(f"{CYAN}=== LINUX AGENT RUNNING ==={RESET}")
    print(f"Server: {SERVER_URL}")

    while True:
        timestamp = time.strftime("%H:%M:%S")
        print(f"\n{CYAN}[SCAN] {timestamp} Auditing System...{RESET}")
        
        policy = fetch_policy()
        drift_msgs = []
        is_drift = False

        # 1. SSH Check
        if 'ssh_config' in policy:
            d, m = ssh_monitor.check_ssh_drift(policy['ssh_config'])
            if d: is_drift = True; drift_msgs.append(f"SSH: {m}")

        # 2. Service Check
        if 'critical_services' in policy:
            d, m = service_watchdog.check_and_enforce_services(policy['critical_services'])
            if d: 
                is_drift = True
                drift_msgs.append(m)
                print(f"   {RED}[SERVICE] ❌ {m}{RESET}")

        # 3. File Permissions (Placeholder)
        if 'file_permissions' in policy:
            d, m = file_guard.check_and_enforce_perms(policy['file_permissions'])
            if d: is_drift = True; drift_msgs.append(m)

        # 4. Sudo Audit (Placeholder)
        if 'allowed_admins' in policy:
            d, m = sudo_audit.check_and_remediate_admins(policy['allowed_admins'])
            if d: is_drift = True; drift_msgs.append(m)

        # 5. Network (Placeholder)
        if 'allowed_ports' in policy:
            d, m = net_guard.check_and_enforce_ports(policy['allowed_ports'])
            if d: is_drift = True; drift_msgs.append(m)

        # KẾT LUẬN
        if is_drift:
            status = "DRIFT"
            msg = " | ".join(drift_msgs)
        else:
            status = "SAFE"
            msg = "System Compliant"
            print(f"   {GREEN}[OK] System Compliant{RESET}")

        send_report(status, msg)
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()