import subprocess
import utils

def check_and_fix_service(svc_name, desired_state):
    try:
        res = subprocess.run(["sc", "query", svc_name], capture_output=True, text=True)
        current = "RUNNING" if "RUNNING" in res.stdout else "STOPPED"
        
        if current != desired_state:
            action = "start" if desired_state == "RUNNING" else "stop"
            print(f"   [SYS FIX] Service {svc_name} -> {action}")
            subprocess.run(f"net {action} {svc_name}", shell=True, capture_output=True)
            
            # --- GHI LOG ---
            utils.write_local_log(
                "SERVICE_DRIFT", 
                f"Service '{svc_name}' was {current}", 
                f"Forced to {desired_state}"
            )
            return True
        return False
    except: return False

def check_services_list(services_list, desired_state):
    """Duyệt qua danh sách các service cần quản lý"""
    if not services_list: return False, []
    
    fixed_services = []
    for svc in services_list:
        if check_and_fix_service(svc, desired_state):
            fixed_services.append(svc)
            
    if fixed_services:
        return True, f"Services Fixed: {', '.join(fixed_services)}"
    return False, None

def check_and_fix_firewall(policy_state):
    try:
        res = subprocess.run("netsh advfirewall show allprofiles state", capture_output=True, text=True, shell=True)
        current = "ON" if "ON" in res.stdout else "OFF"
        
        if policy_state and current != policy_state:
            print(f"   [SYS FIX] Firewall -> {policy_state}")
            subprocess.run(f"netsh advfirewall set allprofiles state {policy_state}", shell=True, capture_output=True)
            
            # --- GHI LOG ---
            utils.write_local_log(
                "FIREWALL_DRIFT", 
                f"Firewall state was {current}", 
                f"Forced to {policy_state}"
            )
            return True, "Firewall State Enforced"
        return False, None
    except: return False, None