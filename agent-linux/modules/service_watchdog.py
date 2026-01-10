import shutil
import subprocess

# Tìm đường dẫn lệnh systemctl
SYSTEMCTL_PATH = shutil.which("systemctl") or "/usr/bin/systemctl"

def run_command(cmd_str):
    try:
        # Chạy lệnh và lấy kết quả text
        res = subprocess.run(cmd_str, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return res.returncode, res.stdout.strip()
    except: 
        return -1, ""

def check_and_enforce_services(policy_services):
    """
    Xử lý 2 danh sách:
    - ensure_active: Phải chạy (Nếu tắt -> Start)
    - ensure_inactive: Phải tắt (Nếu chạy -> Stop & Disable)
    """
    # Lấy danh sách từ Policy, nếu không có thì trả về list rỗng
    active_list = policy_services.get("ensure_active", [])
    inactive_list = policy_services.get("ensure_inactive", [])
    
    details = []
    drift_detected = False

    # 1. Xử lý nhóm CẦN BẬT (Ensure Active)
    for svc in active_list:
        code, status = run_command(f"{SYSTEMCTL_PATH} is-active {svc}")
        # Nếu trạng thái KHÁC active (tức là inactive, failed, unknown...)
        if status != "active":
            drift_detected = True
            print(f"   [SVC FIX] Starting required service: {svc}...")
            
            # Thực hiện sửa lỗi
            run_command(f"{SYSTEMCTL_PATH} start {svc}")
            run_command(f"{SYSTEMCTL_PATH} enable {svc}") # Đảm bảo khởi động cùng OS
            
            details.append(f"Started {svc}")

    # 2. Xử lý nhóm CẦN TẮT (Ensure Inactive)
    for svc in inactive_list:
        code, status = run_command(f"{SYSTEMCTL_PATH} is-active {svc}")
        # Nếu trạng thái LÀ active (đang chạy)
        if status == "active":
            drift_detected = True
            print(f"   [SVC FIX] Stopping prohibited service: {svc}...")
            
            # Thực hiện sửa lỗi
            run_command(f"{SYSTEMCTL_PATH} stop {svc}")
            run_command(f"{SYSTEMCTL_PATH} disable {svc}") # Cấm khởi động cùng OS
            
            details.append(f"Stopped {svc}")

    if drift_detected:
        return True, f"Service Config Enforced: {', '.join(details)}"
    
    return False, None