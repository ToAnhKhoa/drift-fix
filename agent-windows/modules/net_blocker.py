# agent-windows/modules/net_blocker.py (Phiên bản Final Fix Permissions)
import subprocess
import os
import sys
import utils
from config import HOSTS_PATH, REDIRECT_IP

def run_command(cmd):
    try:
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        res = subprocess.run(cmd, capture_output=True, text=True, shell=True, startupinfo=startupinfo)
        return res.stdout.strip()
    except: return ""

def normalize_content(content_lines):
    normalized = []
    for line in content_lines:
        s = line.strip()
        if s: normalized.append(s)
    return "\n".join(normalized)

def update_hosts_file(blocked_list):
    # 1. Ép buộc đường dẫn chính xác (Fix triệt để vấn đề 32/64 bit)
    real_path = r"C:\Windows\System32\drivers\etc\hosts"
    if os.path.exists(r"C:\Windows\Sysnative"):
        real_path = r"C:\Windows\Sysnative\drivers\etc\hosts"
    
    # In ra để chắc chắn
    print(f"   [NET TARGET] Path: {real_path}")

    if blocked_list is None: blocked_list = []

    try:
        # Tạo file nếu chưa có
        if not os.path.exists(real_path):
            with open(real_path, 'w') as f: f.write("")

        # 2. ĐỌC FILE
        with open(real_path, 'r') as f:
            current_lines = f.readlines()

        # 3. CHUẨN BỊ NỘI DUNG
        clean_lines = [line for line in current_lines if "DRIFTGUARD" not in line and REDIRECT_IP not in line]
        new_content_lines = clean_lines.copy()
        
        if new_content_lines and not new_content_lines[-1].endswith('\n'):
            new_content_lines[-1] += '\n'

        if blocked_list:
            new_content_lines.append("\n# --- DRIFTGUARD BLOCK LIST ---\n")
            for site in blocked_list:
                site_clean = site.replace("www.", "").strip()
                new_content_lines.append(f"{REDIRECT_IP}       {site_clean}\n")
                new_content_lines.append(f"{REDIRECT_IP}       www.{site_clean}\n")

        # 4. SO SÁNH
        if normalize_content(current_lines) == normalize_content(new_content_lines):
            return False, None 

        print(f"   [NET DEBUG] Content changed. Applying PERMISSION FIX update...")

        # 5. GHI FILE & CẤP QUYỀN (QUAN TRỌNG NHẤT)
        # Mở khóa file cũ để xóa
        run_command(f'attrib -r -s -h "{real_path}"')
        run_command(f'icacls "{real_path}" /grant Administrators:F /t /c /q')

        # Xóa và ghi lại
        if os.path.exists(real_path): os.remove(real_path)
        
        with open(real_path, 'w') as f:
            f.writelines(new_content_lines)
            
        # --- CẤP QUYỀN CHO WINDOWS ĐỌC ĐƯỢC ---
        # Cấp quyền đọc cho tất cả Users (để Notepad mở được)
        run_command(f'icacls "{real_path}" /grant Users:R /t /c /q')
        # Cấp quyền cho Dịch vụ Mạng (để chặn web được)
        run_command(f'icacls "{real_path}" /grant "Network Service":R /t /c /q')
        # ---------------------------------------

        print("   [NET SUCCESS] ✅ File updated & Permissions fixed!")
            
        run_command("ipconfig /flushdns")
        
        action = "Updated Blocklist"
        utils.write_local_log("NETWORK_DRIFT", "Hosts file modified", action)
        return True, action

    except Exception as e:
        print(f"   [NET CRASH] {e}")
        return False, None