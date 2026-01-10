import subprocess
import shutil

CMD_FIREWALL = shutil.which("firewall-cmd")

def run_command(cmd):
    try:
        subprocess.run(cmd, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except: return False

def check_and_enforce_ports(allowed_ports):
    """
    Đảm bảo các port trong whitelist được cho phép qua Firewall.
    """
    if not CMD_FIREWALL:
        return False, None

    drift_detected = False
    details = []

    # Lấy danh sách port đang mở hiện tại
    # firewall-cmd --list-ports -> "80/tcp 443/tcp"
    try:
        res = subprocess.run(f"{CMD_FIREWALL} --list-ports", shell=True, stdout=subprocess.PIPE, text=True)
        current_open = res.stdout.strip()
    except:
        return False, None

    for port in allowed_ports:
        port_str = f"{port}/tcp"
        
        # Nếu port chưa được mở
        if port_str not in current_open:
            drift_detected = True
            print(f"   [NET FIX] Opening firewall port: {port}...")
            
            # Mở port (cả runtime và permanent)
            run_command(f"{CMD_FIREWALL} --add-port={port_str}")
            run_command(f"{CMD_FIREWALL} --add-port={port_str} --permanent")
            
            details.append(f"Opened {port}")

    if drift_detected:
        return True, f"Firewall Ports Enforced: {', '.join(details)}"
    
    return False, None