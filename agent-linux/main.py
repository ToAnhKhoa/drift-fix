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
        sys.exit(1)

def fetch_policy():
    try:
        resp = requests.get(f"{SERVER_URL}/api/policy", timeout=3)
        if resp.status_code == 200:
            return resp.json().get("linux", {})
        return {}
    except: return {}

def send_report(status, message):
    # (Giữ nguyên code send_report cũ của bạn để tiết kiệm dòng)
    pass 
    # Bạn copy lại hàm send_report và get_system_payload từ file cũ nhé
    # Hoặc nếu cần tôi sẽ viết lại full, nhưng logic không đổi.
    payload = {
        "hostname": platform.node(),
        "os": "Linux",
        "status": status,
        "message": message
    }
    try:
        requests.post(f"{SERVER_URL}/api/report", json=payload, headers={"X-Api-Key": API_SECRET_KEY})
        color = RED if status == "DRIFT" else GREEN
        print(f" -> [REPORT] Sent: {color}{status}{RESET}")
    except: pass

def main():
    check_root()
    print(f"{CYAN}=== LINUX AGENT ENTERPRISE v2.0 ==={RESET}")
    print(f"Interval: {CHECK_INTERVAL}s")

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

        # --- 2. SERVICES (Active & Inactive) ---
        if 'critical_services' in policy:
            d, m = service_watchdog.check_and_enforce_services(policy['critical_services'])
            if d:
                is_drift = True; drift_msgs.append(m)
                print(f"   {RED}[SERVICE] ❌ {m}{RESET}")

        # --- 3. FILE PERMISSIONS ---
        if 'file_permissions' in policy:
            d, m = file_guard.check_and_enforce_perms(policy['file_permissions'])
            if d:
                is_drift = True; drift_msgs.append(m)
                print(f"   {RED}[FILE] ❌ {m}{RESET}")

        # --- 4. ALLOWED ADMINS ---
        if 'allowed_admins' in policy:
            d, m = sudo_audit.check_and_remediate_admins(policy['allowed_admins'])
            if d:
                is_drift = True; drift_msgs.append(m)
                print(f"   {RED}[USER] ❌ {m}{RESET}")

        # --- 5. FIREWALL PORTS ---
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