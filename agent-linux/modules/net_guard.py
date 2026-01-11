import subprocess
import shutil


CMD_FIREWALL = shutil.which("firewall-cmd")

def check_and_enforce_ports(allowed_ports):
    """
    Input: Danh sách port [80, 443, 22]
    Logic: Kiểm tra port đã mở chưa. Nếu chưa -> Mở (Runtime + Permanent).
    """
    if not CMD_FIREWALL:
        return False, "Firewall-cmd not found"

    drift_detected = False
    details = []
    
    # 1. Lấy danh sách port đang mở hiện tại
    try:
        res = subprocess.run(f"{CMD_FIREWALL} --list-ports", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        current_open_ports = res.stdout.strip()
    except:
        return False, "Could not list ports"

    # 2. Quét qua danh sách được phép (Allowed List)
    for port in allowed_ports:
        port_str = f"{port}/tcp" 
        
        # Nếu port chưa có trong danh sách đang mở
        if port_str not in current_open_ports:
            drift_detected = True
            print(f"   [NET FIX] Port {port} is closed. Opening now...")
            
            # 3. Auto-Fix: Mở port
            # Bước A: Mở ngay lập tức
            subprocess.run(f"{CMD_FIREWALL} --add-port={port_str}", shell=True)
            # Bước B: Ghi vào cấu hình vĩnh viễn
            subprocess.run(f"{CMD_FIREWALL} --add-port={port_str} --permanent", shell=True)
            
            details.append(f"Opened {port}")

    if drift_detected:
        return True, f"Firewall Ports Enforced: {', '.join(details)}"
    
    return False, None