import time
import os
import requests
import sys
import platform

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
RED = "\033[91m"; GREEN = "\033[92m"; CYAN = "\033[96m"; RESET = "\033[0m"

try:
    from config import SERVER_URL, API_SECRET_KEY, CHECK_INTERVAL
    # Import thêm net_guard
    from modules import utils, ssh_monitor, service_watchdog, file_guard, net_guard
except ImportError as e:
    print(f"Missing modules: {e}"); sys.exit(1)

def send_report(status, message):
    try:
        payload = {
            "hostname": platform.node(), "os": "Linux",
            "status": status, "message": message,
            "cpu": utils.get_cpu_usage(), "ram": utils.get_ram_usage(), "disk": utils.get_disk_usage()
        }
        requests.post(f"{SERVER_URL}/api/report", json=payload, headers={"X-Api-Key": API_SECRET_KEY}, timeout=2)
        print(f" -> [REPORT] Sent: {RED if status == 'DRIFT' else GREEN}{status}{RESET}")
    except: pass

def main():
    if os.geteuid() != 0: sys.exit(1)
    print(f"{CYAN}=== LINUX AGENT (4 MODULES ACTIVE) ==={RESET}")

    while True:
        print(f"\n{CYAN}[SCAN] Auditing...{RESET}")
        try:
            p = requests.get(f"{SERVER_URL}/api/policy", timeout=2).json().get("linux", {})
        except: p = {}
        
        drift = False; msgs = []

        # 1. SSH Enforcer
        if 'ssh_config' in p:
            d, m = ssh_monitor.check_ssh_drift(p['ssh_config'])
            if d: drift = True; msgs.append(m); print(f"   {RED}[SSH] {m}{RESET}")

        # 2. File Guard
        if 'file_permissions' in p:
            d, m = file_guard.check_and_enforce_perms(p['file_permissions'])
            if d: drift = True; msgs.append(m); print(f"   {RED}[FILE] {m}{RESET}")

        # 3. Service Watchdog
        if 'critical_services' in p:
            d, m = service_watchdog.check_and_enforce_services(p['critical_services'])
            if d: drift = True; msgs.append(m); print(f"   {RED}[SVC] {m}{RESET}")

        # 4. Net Guard
        if 'allowed_ports' in p:
            d, m = net_guard.check_and_enforce_ports(p['allowed_ports'])
            if d: drift = True; msgs.append(m); print(f"   {RED}[NET] {m}{RESET}")

        send_report("DRIFT" if drift else "SAFE", " | ".join(msgs) if drift else "Compliant")
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()