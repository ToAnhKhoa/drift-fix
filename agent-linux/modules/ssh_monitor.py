import os

def parse_ssh_config(config_path):
    """Reads sshd_config and returns a dictionary of settings."""
    config = {}
    if not os.path.exists(config_path):
        return config

    try:
        with open(config_path, 'r') as f:
            for line in f:
                line = line.strip()
                # Ignore comments and empty lines
                if not line or line.startswith('#'):
                    continue
                
                parts = line.split()
                if len(parts) >= 2:
                    key = parts[0]
                    value = parts[1]
                    config[key] = value
    except Exception as e:
        print(f"   [SSH ERROR] Could not read config: {e}")
    
    return config

def check_ssh_drift(policy_config):
    """
    Compares current SSH config against Policy.
    Returns: (is_drift, message)
    """
    # Hardcoded path for now, should come from config
    SSH_PATH = "/etc/ssh/sshd_config"
    
    current_config = parse_ssh_config(SSH_PATH)
    drift_details = []

    # Example Policy: {"PermitRootLogin": "no", "PasswordAuthentication": "no"}
    for key, expected_value in policy_config.items():
        # Default to "yes" (insecure) if key is missing in file
        actual_value = current_config.get(key, "Unknown")
        
        if actual_value != expected_value:
            drift_details.append(f"{key}: Expected '{expected_value}' but found '{actual_value}'")

    if drift_details:
        return True, " | ".join(drift_details)
    
    return False, None