# modules/net_blocker.py
import subprocess
import utils
from config import HOSTS_PATH, REDIRECT_IP

def update_hosts_file(blocked_list):
    """
    Cập nhật file hosts thông minh:
    Chỉ ghi file khi nội dung thực tế KHÁC với nội dung mong muốn.
    """
    if blocked_list is None: blocked_list = []
    
    try:
        # 1. Đọc nội dung hiện tại
        with open(HOSTS_PATH, 'r') as f:
            original_lines = f.readlines()
        
        # 2. Tách file thành 2 phần: Phần hệ thống (giữ lại) và Phần DriftGuard (bỏ đi để tạo lại)
        system_lines = []
        for line in original_lines:
            # Giữ lại dòng nếu nó KHÔNG PHẢI do DriftGuard tạo ra
            if "DRIFTGUARD" not in line and not (REDIRECT_IP in line and "localhost" not in line):
                system_lines.append(line)
        
        # 3. Tạo nội dung MONG MUỐN (System lines + New Block list)
        desired_lines = system_lines.copy()
        
        # Đảm bảo có dòng trống ngăn cách nếu cần
        if desired_lines and not desired_lines[-1].endswith('\n'):
            desired_lines[-1] += '\n'
            
        if blocked_list:
            desired_lines.append("\n# --- DRIFTGUARD BLOCK LIST ---\n")
            for site in blocked_list:
                site_clean = site.replace("www.", "").strip()
                desired_lines.append(f"{REDIRECT_IP}       {site_clean}\n")
                desired_lines.append(f"{REDIRECT_IP}       www.{site_clean}\n")

        # 4. SO SÁNH: Nội dung hiện tại vs Nội dung mong muốn
        # Chuyển thành chuỗi để so sánh cho chính xác
        current_content = "".join(original_lines)
        desired_content = "".join(desired_lines)

        if current_content == desired_content:
            # Nếu giống hệt nhau -> Không làm gì cả (SAFE)
            return False, None
        
        # 5. Nếu khác nhau -> Ghi đè (DRIFT FIX)
        print(f"   [NET DEBUG] Detected Drift. Updating hosts file...")
        with open(HOSTS_PATH, 'w') as f:
            f.writelines(desired_lines)
        
        subprocess.run("ipconfig /flushdns", shell=True, capture_output=True)
        
        # Ghi log
        action_msg = "Unblocked All" if not blocked_list else f"Updated Blocklist ({len(blocked_list)} sites)"
        utils.write_local_log("NETWORK_DRIFT", "Hosts file content mismatched policy", action_msg)
        
        return True, action_msg

    except Exception as e:
        print(f"   [NET ERROR] {e}")
        return False, None