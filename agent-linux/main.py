import time
import os
import requests
import json
import platform
import sys

# --- MÀU SẮC TERMINAL ---
RED     = "\033[91m"
GREEN   = "\033[92m"
YELLOW  = "\033[93m"
CYAN    = "\033[96m"
RESET   = "\033[0m"

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from modules import utils, ssh_monitor
    from config import SERVER_URL, API_SECRET_KEY, CHECK_INTERVAL
except ImportError as e:
    print(f"{RED}[CRITICAL] Missing modules: {e}{RESET}")
    sys.exit(1)

def check_root():
    if os.geteuid() != 0:
        print(f"{RED}[ERROR] This agent must be run as ROOT/SUDO.{RESET}")
        sys.exit(1)

def get_linux_distro():
    """Lấy tên OS chi tiết (VD: Rocky Linux 9.7)"""
    try:
        if os.path.exists("/etc/os-release"):
            with open("/etc/os-release", "r") as f:
                for line in f:
                    if line.startswith("PRETTY_NAME="):
                        return line.split("=", 1)[1].strip().strip('"')
    except Exception:
        pass
    return f"{platform.system()} {platform.release()}"

def get_system_payload(status, message):
    return {
        "hostname": platform.node(),
        "os": "Linux",
        "os_full": get_linux_distro(), # Tên OS đầy đủ
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
    except:
        return {}

def send_report(status, message):
    payload = get_system_payload(status, message)
    headers = {"X-Api-Key": API_SECRET_KEY, "Content-Type": "application/json"}
    
    try:
        requests.post(f"{SERVER_URL}/api/report", json=payload, headers=headers, timeout=3)
        if status == "DRIFT":
            print(f" -> [REPORT] Sent: {RED}{status}{RESET}")
        else:
            print(f" -> [REPORT] Sent: {GREEN}{status}{RESET}")
    except Exception as e:
        print(f" -> {YELLOW}[REPORT ERROR] Upload failed: {e}{RESET}")

def main():
    check_root()
    print(f"{CYAN}=== LINUX DRIFT AGENT v1.4 (STABLE EDITION) ==={RESET}")
    print(f"Server: {SERVER_URL}")
    print("---------------------------------------")

    while True:
        timestamp = time.strftime("%H:%M:%S")
        print(f"\n{CYAN}[SCAN] {timestamp} Starting audit...{RESET}")
        
        linux_policy = fetch_policy()
        ssh_policy = linux_policy.get("ssh", {})
        
        is_drift = False
        drift_messages = []

        if ssh_policy:
            ssh_drift, ssh_msg = ssh_monitor.check_ssh_drift(ssh_policy)
            if ssh_drift:
                is_drift = True
                print(f"   {RED}[SSH] ❌ Drift Detected: {ssh_msg}{RESET}")
                drift_messages.append(f"SSH: {ssh_msg}")
            else:
                print(f"   {GREEN}[SSH] ✅ System Safe{RESET}")

        if is_drift:
            final_status = "DRIFT"
            final_msg = " | ".join(drift_messages)
        else:
            # --- ĐÃ SỬA THÀNH: System Stable ---
            final_status = "SAFE"
            final_msg = "System Stable"
            # -----------------------------------

        send_report(final_status, final_msg)
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()