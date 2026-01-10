import shutil
import subprocess

SYSTEMCTL_PATH = shutil.which("systemctl") or "/usr/bin/systemctl"

def run_command(cmd_str):
    try:
        res = subprocess.run(cmd_str, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return res.returncode, res.stdout.strip()
    except: return -1, ""

def check_and_enforce_services(policy_services):
    """
    Xử lý 2 danh sách:
    - ensure_active: Phải chạy (Nếu tắt -> Start)
    - ensure_inactive: Phải tắt (Nếu chạy -> Stop & Disable)
    """
    active_list = policy_services.get("ensure_active", [])
    inactive_list = policy_services.get("ensure_inactive", [])
    
    details = []
    drift_detected = False

    # 1. Xử lý nhóm CẦN BẬT
    for svc in active_list:
        code, status = run_command(f"{SYSTEMCTL_PATH} is-active {svc}")
        if status != "active":
            drift_detected = True
            print(f"   [SVC FIX] Starting required service: {svc}...")
            run_command(f"{SYSTEMCTL_PATH} start {svc}")
            run_command(f"{SYSTEMCTL_PATH} enable {svc}") # Bật khởi động cùng win/linux
            details.append(f"Started {svc}")

    # 2. Xử lý nhóm CẦN TẮT
    for svc in inactive_list:
        code, status = run_command(f"{SYSTEMCTL_PATH} is-active {svc}")
        if status == "active":
            drift_detected = True
            print(f"   [SVC FIX] Stopping prohibited service: {svc}...")
            run_command(f"{SYSTEMCTL_PATH} stop {svc}")
            run_command(f"{SYSTEMCTL_PATH} disable {svc}") # Cấm khởi động lại
            details.append(f"Stopped {svc}")

    if drift_detected:
        return True, f"Service Config Enforced: {', '.join(details)}"
    
    return False, None