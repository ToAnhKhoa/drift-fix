import os

def parse_ssh_config(path):
    config = {}
    if not os.path.exists(path):
        return config
    
    with open(path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            # Tách Key và Value (VD: "PermitRootLogin no")
            parts = line.split(maxsplit=1)
            if len(parts) == 2:
                key = parts[0]
                val = parts[1]
                config[key] = val
    return config

def check_ssh_drift(policy_config):
    SSH_PATH = "/etc/ssh/sshd_config"
    current_config = parse_ssh_config(SSH_PATH)
    
    drift_detected = False
    details = []

    for key, expected_val in policy_config.items():
        # Agent đọc file config, nếu không có key đó thì trả về 'Unknown'
        actual_val = current_config.get(key, "Unknown")
        
        # So sánh (chuyển hết về string để so sánh cho chuẩn)
        if str(actual_val) != str(expected_val):
            drift_detected = True
            details.append(f"{key}: Expected '{expected_val}' but found '{actual_val}'")

    if drift_detected:
        return True, " | ".join(details)
    
    return False, None