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

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    # IMPORT ĐẦY ĐỦ CÁC MODULE
    from modules import utils, ssh_monitor, service_watchdog, file_guard, net_guard, sudo_audit
    from config import SERVER_URL, API_SECRET_KEY, CHECK_INTERVAL
except ImportError as e:
    print(f"{RED}[CRITICAL] Missing modules: {e}{RESET}")
    sys.exit(1)

def check_root():
    if os.geteuid() != 0:
        print(f"{RED}[ERROR] Agent must run as root.{RESET}")
        sys.exit(1)

def get_linux_distro():
    try:
        if os.path.exists("/etc/os-release"):
            with open("/etc/os-release", "r") as f:
                for line in f:
                    if line.startswith("PRETTY_NAME="):
                        return line.split("=", 1)[1].strip().strip('"')
    except Exception: pass
    return f"{platform.system()} {platform.release()}"

def get_system_payload(status, message):
    return {
        "hostname": platform.node(),
        "os": "Linux",
        "os_full": get_linux_distro(),
        "os_release": platform.release(),
        "cpu": utils.get_cpu_usage(),
        "ram": utils.get_ram_usage(),
        "disk": utils.get_disk_usage(),
        "status": status,
        "message": message
    }

def fetch_policy():
    try:
        resp = requests.get(f"{SERVER_URL}/api/policy", timeout=3)
        if resp.status_code == 200:
            return resp.json().get("linux", {})
        return {}
    except: return {}

def send_report(status, message):
    payload = get_system_payload(status, message)
    try:
        requests.post(f"{SERVER_URL}/api/report", json=payload, headers={"X-Api-Key": API_SECRET_KEY}, timeout=3)
        color = RED if status == "DRIFT" else GREEN
        print(f" -> [REPORT] Sent: {color}{status}{RESET}")
    except Exception as e:
        pass

def main():
    check_root()
    print(f"{CYAN}=== LINUX AGENT ENTERPRISE v2.1 ==={RESET}")
    print(f"Server: {SERVER_URL}")

    while True:
        timestamp = time.strftime("%H:%M:%S")
        print(f"\n{CYAN}[SCAN] {timestamp} Auditing System...{RESET}")
        
        policy = fetch_policy()
        drift_msgs = []
        is_drift = False

        # --- 1. SSH CONFIG ---
        if 'ssh_config' in policy:
            d, m = ssh_monitor.check_ssh_drift(policy['ssh_config'])
            if d:
                is_drift = True; drift_msgs.append(f"SSH: {m}")
                print(f"   {RED}[SSH] ❌ {m}{RESET}")

        # --- 2. SERVICES ---
        if 'critical_services' in policy:
            d, m = service_watchdog.check_and_enforce_services(policy['critical_services'])
            if d:
                is_drift = True; drift_msgs.append(m)
                print(f"   {RED}[SERVICE] ❌ {m}{RESET}")

        # --- 3. FILE PERMISSIONS (Đã thêm lệnh gọi) ---
        if 'file_permissions' in policy:
            d, m = file_guard.check_and_enforce_perms(policy['file_permissions'])
            if d:
                is_drift = True; drift_msgs.append(m)
                print(f"   {RED}[FILE] ❌ {m}{RESET}")

        # --- 4. ALLOWED ADMINS (Đã thêm lệnh gọi) ---
        if 'allowed_admins' in policy:
            d, m = sudo_audit.check_and_remediate_admins(policy['allowed_admins'])
            if d:
                is_drift = True; drift_msgs.append(m)
                print(f"   {RED}[USER] ❌ {m}{RESET}")

        # --- 5. FIREWALL PORTS (Đã thêm lệnh gọi) ---
        if 'allowed_ports' in policy:
            d, m = net_guard.check_and_enforce_ports(policy['allowed_ports'])
            if d:
                is_drift = True; drift_msgs.append(m)
                print(f"   {RED}[NET] ❌ {m}{RESET}")

        # --- KẾT LUẬN ---
        if is_drift:
            status = "DRIFT"
            msg = " | ".join(drift_msgs)
        else:
            status = "SAFE"
            msg = "System Compliant"
            print(f"   {GREEN}[OK] System is fully compliant.{RESET}")

        send_report(status, msg)
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()