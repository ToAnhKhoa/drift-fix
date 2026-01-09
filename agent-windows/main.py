# main.py
import time
import datetime
import utils
import config
from modules import net_blocker, app_blocker, sys_guard

# 1. Yêu cầu quyền Admin
utils.force_admin()

print(f"=== WINDOWS AGENT v6.0 (MODULAR) STARTING ===")
print(f"Server: {config.SERVER_URL}")

last_hb_time = 0

while True:
    print(f"\n[SCAN] {datetime.datetime.now().strftime('%H:%M:%S')}")
    
    # 2. Lấy Policy
    policy = utils.get_policy()
    
    if policy:
        drift_logs = []
        is_drift = False

        # --- MODULE 1: NETWORK BLOCK ---
        sites = policy.get("blocked_sites", [])
        status, msg = net_blocker.update_hosts_file(sites)
        if status:
            drift_logs.append(msg)
            is_drift = True
            
        # --- MODULE 2: APP BLOCK ---
        status, msg = app_blocker.check_window_title(sites)
        if status:
            drift_logs.append(msg)
            is_drift = True
            
        # --- MODULE 3: SYSTEM GUARD (SERVICES LIST) ---
        target_services = policy.get("restricted_services", [])
        desired_svc_state = policy.get("desired_state", "STOPPED")
        
        status, msg = sys_guard.check_services_list(target_services, desired_svc_state)
        if status:
            drift_logs.append(msg)
            is_drift = True
            
        # --- MODULE 4: FIREWALL ---
        status, msg = sys_guard.check_and_fix_firewall(policy.get("firewall"))
        if status:
            drift_logs.append(msg)
            is_drift = True
            
        # --- REPORTING ---
        if is_drift:
            full_msg = " | ".join(drift_logs)
            utils.send_report("DRIFT", full_msg)
        elif (time.time() - last_hb_time) > config.HEARTBEAT_INTERVAL:
            utils.send_report("SAFE", "System Stable")
            last_hb_time = time.time()
        else:
            print("   -> System Green.")
            
    else:
        print("   -> Cannot connect to Server.")

    time.sleep(config.CHECK_INTERVAL)