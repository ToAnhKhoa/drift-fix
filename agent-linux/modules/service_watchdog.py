import subprocess

def run_command(cmd):
    """Chạy lệnh shell và trả về kết quả"""
    try:
        result = subprocess.run(cmd, shell=True, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return result.returncode, result.stdout.decode().strip()
    except:
        return -1, ""

def check_and_heal_services(service_list):
    """
    Kiểm tra danh sách dịch vụ.
    Nếu dịch vụ chết -> Tự động Restart.
    Trả về: (is_drift, message)
    """
    drift_detected = False
    details = []

    for service in service_list:
        # 1. Kiểm tra trạng thái (is-active trả về 0 nếu đang chạy)
        code, status = run_command(f"systemctl is-active {service}")
        
        if status != "active":
            drift_detected = True
            details.append(f"{service} is {status}")
            
            # --- AUTO-HEALING (TỰ SỬA LỖI) ---
            print(f"   [SERVICE FIX] Restarting {service}...")
            run_command(f"systemctl restart {service}")

    if drift_detected:
        # Kiểm tra lại lần nữa xem đã sửa được chưa
        fixed_count = 0
        for service in service_list:
             _, status = run_command(f"systemctl is-active {service}")
             if status == "active":
                 fixed_count += 1
        
        if fixed_count == len(service_list):
            return True, f"Restarted services: {', '.join(details)}"
        else:
            return True, f"Critical Services Down: {', '.join(details)}"

    return False, None