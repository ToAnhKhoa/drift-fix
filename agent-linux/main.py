import time
import os
import requests
import sys
import platform


sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# --- COLORS ---
RED = "\033[91m"
GREEN = "\033[92m"
CYAN = "\033[96m"
RESET = "\033[0m"


try:
    from config import SERVER_URL, API_SECRET_KEY, CHECK_INTERVAL
    from modules import utils, ssh_monitor, service_watchdog, file_guard
except ImportError as e:
    print(f"CRITICAL ERROR: Missing core modules: {e}")
    sys.exit(1)

def send_report(status, message):
    try:
        payload = {
            "hostname": platform.node(),
            "os": "Linux",
            "status": status,
            "message": message,
            "cpu": utils.get_cpu_usage(),
            "ram": utils.get_ram_usage(),
            "disk": utils.get_disk_usage()
        }
        requests.post(f"{SERVER_URL}/api/report", json=payload, headers={"X-Api-Key": API_SECRET_KEY}, timeout=3)
        
        color = RED if status == "DRIFT" else GREEN
        print(f" -> [REPORT] Sent: {color}{status}{RESET}")
    except Exception as e:
        print(f" -> [REPORT ERROR] {e}")

def main():
    if os.geteuid() != 0:
        print("Must run as root")
        sys.exit(1)

    print(f"{CYAN}=== LINUX AGENT (File Guard Enabled) ==={RESET}")
    print(f"Server: {SERVER_URL}")

    while True:
        print(f"\n{CYAN}[SCAN] Auditing System...{RESET}")
        
      
        try:
            resp = requests.get(f"{SERVER_URL}/api/policy", timeout=3)
            policy = resp.json().get("linux", {}) if resp.status_code == 200 else {}
        except:
            policy = {}

        drift_msgs = []
        is_drift = False

        if 'ssh_config' in policy:
            d, m = ssh_monitor.check_ssh_drift(policy['ssh_config'])
            if d: is_drift = True; drift_msgs.append(f"SSH: {m}"); print(f"   {RED}[SSH] ❌ {m}{RESET}")

      
        if 'critical_services' in policy:
            d, m = service_watchdog.check_and_enforce_services(policy['critical_services'])
            if d: is_drift = True; drift_msgs.append(m); print(f"   {RED}[SVC] ❌ {m}{RESET}")

       
        if 'file_permissions' in policy:
           
            d, m = file_guard.check_and_enforce_perms(policy['file_permissions'])
            if d:
                is_drift = True
                drift_msgs.append(m)
                print(f"   {RED}[FILE] ❌ {m}{RESET}")

    
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