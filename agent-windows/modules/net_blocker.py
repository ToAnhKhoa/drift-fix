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
    """Hàm chuẩn hóa để so sánh: Xóa dòng trống và khoảng trắng thừa"""
    normalized = []
    for line in content_lines:
        s = line.strip()
        if s:
            normalized.append(s)
    return "\n".join(normalized)

def update_hosts_file(blocked_list):
    if blocked_list is None: blocked_list = []

    try:
        if not os.path.exists(HOSTS_PATH):
            with open(HOSTS_PATH, 'w') as f: f.write("")

        # 1. ĐỌC FILE HIỆN TẠI
        with open(HOSTS_PATH, 'r') as f:
            current_lines = f.readlines()

        # 2. TẠO NỘI DUNG MONG MUỐN
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

        # 3. SO SÁNH
        current_normalized = normalize_content(current_lines)
        target_normalized = normalize_content(new_content_lines)

        if current_normalized == target_normalized:
            return False, None 

        print(f"   [NET DEBUG] Content changed. Updating...")

        # 4. GHI FILE
        run_command(f'attrib -r -s -h "{HOSTS_PATH}"')
        run_command(f'icacls "{HOSTS_PATH}" /grant Administrators:F /t /c /q')

        try:
            if os.path.exists(HOSTS_PATH):
                os.remove(HOSTS_PATH)
            
            with open(HOSTS_PATH, 'w') as f:
                f.writelines(new_content_lines)
            
            print("   [NET SUCCESS] ✅ File updated successfully!")

        except Exception as e:
            print(f"   [WRITE ERROR] {e}")
            return False, None
            
        run_command("ipconfig /flushdns")
        
        action = "Updated Blocklist"
        utils.write_local_log("NETWORK_DRIFT", "Hosts file modified", action)
        return True, action

    except Exception as e:
        print(f"   [NET CRASH] {e}")
        return False, None