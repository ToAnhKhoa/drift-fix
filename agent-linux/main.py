import time
import os
import requests
import sys
import platform

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
RED = "\033[91m"; GREEN = "\033[92m"; CYAN = "\033[96m"; RESET = "\033[0m"

try:
    from config import SERVER_URL, API_SECRET_KEY, CHECK_INTERVAL
    # Import ĐẦY ĐỦ 5 anh em siêu nhân
    from modules import utils, ssh_monitor, service_watchdog, file_guard, net_guard, sudo_audit
except ImportError as e:
    print(f"Missing modules: {e}"); sys.exit(1)

# [MỚI] Hàm lấy tên hệ điều hành chi tiết (VD: Rocky Linux 9.7)
def get_os_details():
    pretty_name = "Linux Generic"
    try:
        if os.path.exists("/etc/os-release"):
            with open("/etc/os-release", "r") as f:
                for line in f:
                    if line.startswith("PRETTY_NAME="):
                        # Lấy nội dung trong ngoặc kép
                        pretty_name = line.split("=", 1)[1].strip().strip('"')
                        break
    except: pass
    return pretty_name

def send_report(status, message):
    try:
        # [CẬP NHẬT] Thêm os_full và os_release vào gói tin gửi đi
        payload = {
            "hostname": platform.node(), 
            "os": "Linux",
            "os_full": get_os_details(),       # <--- Thêm dòng này
            "os_release": platform.release(),  # <--- Thêm dòng này (Kernel info)
            "status": status, 
            "message": message,
            "cpu": utils.get_cpu_usage(), 
            "ram": utils.get_ram_usage(), 
            "disk": utils.get_disk_usage()
        }
        requests.post(f"{SERVER_URL}/api/report", json=payload, headers={"X-Api-Key": API_SECRET_KEY}, timeout=2)
        print(f" -> [REPORT] Sent: {RED if status == 'DRIFT' else GREEN}{status}{RESET}")
    except: pass

def main():
    if os.geteuid() != 0: sys.exit(1)
    print(f"{CYAN}=== LINUX AGENT ENTERPRISE (FULL 5 MODULES) ==={RESET}")
    print(f"OS Detected: {get_os_details()}") # In ra màn hình để kiểm tra

    while True:
        print(f"\n{CYAN}[SCAN] Auditing System...{RESET}")
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

        # 5. Sudo Audit 
        if 'allowed_admins' in p:
            d, m = sudo_audit.check_and_remediate_admins(p['allowed_admins'])
            if d: drift = True; msgs.append(m); print(f"   {RED}[USER] {m}{RESET}")

        send_report("DRIFT" if drift else "SAFE", " | ".join(msgs) if drift else "Compliant")
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()