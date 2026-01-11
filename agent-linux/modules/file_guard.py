import os
import stat

def check_and_enforce_perms(file_policy_list):
    """
    Input: Danh sách [{'path': '/etc/shadow', 'mode': '000'}, ...]
    Logic: So sánh mode hiện tại vs mode yêu cầu. Nếu sai -> chmod.
    """
    drift_detected = False
    details = []

    for item in file_policy_list:
        fpath = item.get("path")
        target_mode_str = item.get("mode") # string "600"

        
        if not os.path.exists(fpath):
            continue 

        try:
            # 1. Lấy quyền hiện tại 
            st = os.stat(fpath)
            current_mode = oct(st.st_mode)[-3:] 
            
            # 2. So sánh
            if current_mode != target_mode_str:
                drift_detected = True
                print(f"   [FILE FIX] {fpath}: Found {current_mode}, expected {target_mode_str}. Fixing...")
                
                # 3. Sửa quyền (Convert string '600' sang int octal 0o600)
                os.chmod(fpath, int(target_mode_str, 8))
                
                details.append(f"Fixed {fpath}")

        except Exception as e:
            print(f"   [FILE ERROR] Could not fix {fpath}: {e}")

    if drift_detected:
        return True, f"Permissions Fixed: {', '.join(details)}"
    
    return False, None