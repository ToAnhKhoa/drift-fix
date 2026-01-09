import time
import os
import requests
import json
import platform
import sys

# Add current directory to path to find modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from modules import utils, ssh_monitor
    from config import SERVER_URL, API_SECRET_KEY, CHECK_INTERVAL
except ImportError as e:
    print(f"[CRITICAL] Missing modules: {e}")
    sys.exit(1)

def check_root():
    """Ensure the script is running as root (Required for Linux admin tasks)."""
    if os.geteuid() != 0:
        print("[ERROR] This agent must be run as ROOT/SUDO to access /etc config files.")
        sys.exit(1)

def get_system_payload(status, message):
    """Constructs the JSON report payload."""
    return {
        "hostname": platform.node(),
        "os": "Linux",
        "os_full": f"{platform.system()} {platform.release()}",
        "os_release": platform.version(),
        "cpu": utils.get_cpu_usage(),
        "ram": utils.get_ram_usage(),
        "disk": utils.get_disk_usage(),
        "status": status,
        "message": message
    }

def fetch_policy():
    """Fetches the latest policy from the Master Server."""
    try:
        resp = requests.get(f"{SERVER_URL}/api/policy", timeout=3)
        if resp.status_code == 200:
            return resp.json().get("linux", {})
        return {}
    except Exception as e:
        print(f"   [NET ERROR] Could not fetch policy: {e}")
        return {}

def send_report(status, message):
    """Sends the health report to the Master Server."""
    payload = get_system_payload(status, message)
    headers = {"X-Api-Key": API_SECRET_KEY, "Content-Type": "application/json"}
    
    try:
        requests.post(f"{SERVER_URL}/api/report", json=payload, headers=headers, timeout=3)
        print(f" -> [REPORT] Sent: {status}")
    except Exception as e:
        print(f" -> [REPORT ERROR] Upload failed: {e}")

def main():
    # 1. Root Check
    check_root()

    print(f"=== LINUX DRIFT AGENT v1.0 STARTING ===")
    print(f"Server: {SERVER_URL}")
    print("---------------------------------------")

    while True:
        print(f"\n[SCAN] Starting system audit...")
        
        # 2. Get Policy
        linux_policy = fetch_policy()
        
        # Extract specific modules policies
        ssh_policy = linux_policy.get("ssh", {})
        
        # Default State
        is_drift = False
        drift_messages = []

        # ----------------------------------------
        # MODULE 1: SSH CONFIG MONITOR
        # ----------------------------------------
        if ssh_policy:
            ssh_drift, ssh_msg = ssh_monitor.check_ssh_drift(ssh_policy)
            if ssh_drift:
                is_drift = True
                print(f"   [SSH ALERT] Drift Detected: {ssh_msg}")
                drift_messages.append(f"SSH: {ssh_msg}")
            else:
                print(f"   [SSH] Config is secure.")
        
        # ----------------------------------------
        # FUTURE MODULES (Service Watchdog, etc.)
        # ----------------------------------------
        # if service_policy: ...

        # ----------------------------------------
        # REPORTING
        # ----------------------------------------
        if is_drift:
            final_status = "DRIFT"
            final_msg = " | ".join(drift_messages)
        else:
            final_status = "SECURE"
            final_msg = "System Compliant"

        send_report(final_status, final_msg)
        
        # Sleep
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()