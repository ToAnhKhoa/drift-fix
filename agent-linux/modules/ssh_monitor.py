import os
import subprocess
import shutil

SSH_PATH = "/etc/ssh/sshd_config"
SYSTEMCTL_PATH = shutil.which("systemctl") or "/usr/bin/systemctl"

def run_command(cmd):
    try:
        subprocess.run(cmd, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except: pass

def check_ssh_drift(policy_config):
    """
    Input: policy_config = {"PermitRootLogin": "no", "MaxAuthTries": "3", ...}
    Nhiệm vụ: Đảm bảo file config trên máy có đúng các dòng này.
    """
    if not os.path.exists(SSH_PATH):
        return False, "Config file not found"

    drift_detected = False
    details = []
    
    # 1. Đọc nội dung file hiện tại
    with open(SSH_PATH, 'r') as f:
        lines = f.readlines()

    new_lines = []
    # Tạo bản sao dictionary để đánh dấu những key đã xử lý
    remaining_policy = policy_config.copy()

    # 2. Quét qua từng dòng của file hiện tại để SỬA
    for line in lines:
        clean_line = line.strip()
        if not clean_line or clean_line.startswith('#'):
            new_lines.append(line)
            continue
        
        # Kiểm tra xem dòng này có phải là key chúng ta đang quản lý không
        current_key = clean_line.split()[0] # Lấy từ đầu tiên
        
        if current_key in remaining_policy:
            # Đây là dòng cần quản lý!
            target_val = str(remaining_policy[current_key])
            
            # Kiểm tra xem giá trị hiện tại
            parts = clean_line.split()
            if len(parts) >= 2 and parts[1] == target_val:
                new_lines.append(line)
            else:
                drift_detected = True
                print(f"   [SSH FIX] Updating {current_key} to {target_val}...")
                new_lines.append(f"{current_key} {target_val}\n")
                details.append(f"Fixed {current_key}")
            
            del remaining_policy[current_key]
        else:
            new_lines.append(line)

    # 3. Xử lý những key còn thiếu (Append)
    for key, val in remaining_policy.items():
        drift_detected = True
        print(f"   [SSH FIX] Adding missing config: {key} {val}...")
        new_lines.append(f"{key} {val}\n")
        details.append(f"Added {key}")

    # 4. Ghi lại file nếu có thay đổi
    if drift_detected:
        try:
            with open(SSH_PATH, 'w') as f:
                f.writelines(new_lines)
            
            # Quan trọng: Reload lại SSHD để nhận cấu hình mới
            print("   [SSH FIX] Reloading SSH Service...")
            run_command(f"{SYSTEMCTL_PATH} reload sshd")
            
            return True, f"SSH Config Enforced: {', '.join(details)}"
        except Exception as e:
            return True, f"Failed to write SSH config: {e}"

    return False, None