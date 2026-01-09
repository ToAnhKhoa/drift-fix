import subprocess
import shutil

# Tìm đường dẫn chính xác của lệnh systemctl trên máy Rocky Linux
SYSTEMCTL_PATH = shutil.which("systemctl") or "/usr/bin/systemctl"

def run_command(cmd_str):
    """Chạy lệnh và lấy cả lỗi (stderr) nếu có"""
    try:
        # Chạy lệnh với shell=True
        result = subprocess.run(
            cmd_str, 
            shell=True, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True
        )
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except Exception as e:
        return -1, "", str(e)

def check_and_heal_services(service_list):
    drift_detected = False
    details = []

    for service in service_list:
        # 1. Kiểm tra trạng thái
        cmd_check = f"{SYSTEMCTL_PATH} is-active {service}"
        code, status, err = run_command(cmd_check)
        
        # Nếu service không active (inactive, failed, unknown...)
        if status != "active":
            drift_detected = True
            details.append(f"{service} is {status}")
            
            # 2. Thử sửa lỗi (Auto-healing)
            print(f"   [SERVICE FIX] Restarting {service} via {SYSTEMCTL_PATH}...")
            
            cmd_restart = f"{SYSTEMCTL_PATH} restart {service}"
            res_code, res_out, res_err = run_command(cmd_restart)
            
            if res_code != 0:
                print(f"   [FIX ERROR] Failed to restart {service}. Error: {res_err}")
            else:
                print(f"   [FIX SUCCESS] Restart command sent for {service}")

    if drift_detected:
        # Kiểm tra lại lần cuối
        fixed_count = 0
        still_dead = []
        
        for service in service_list:
             _, status, _ = run_command(f"{SYSTEMCTL_PATH} is-active {service}")
             if status == "active":
                 fixed_count += 1
             else:
                 still_dead.append(service)
        
        if fixed_count == len(service_list):
            return True, f"Fixed: {', '.join(details)}"
        else:
            return True, f"Failed to Fix: {', '.join(still_dead)}"

    return False, None