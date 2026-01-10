import grp
import subprocess

def check_and_remediate_admins(allowed_list):
    
    ADMIN_GROUP = "wheel" 
    drift_detected = False
    details = []

    try:
     
        current_admins = grp.getgrnam(ADMIN_GROUP).gr_mem
    except KeyError:
        return True, f"Critical: Group '{ADMIN_GROUP}' not found!"

    
    unauthorized_users = [user for user in current_admins if user not in allowed_list]

    if unauthorized_users:
        drift_detected = True
        
        for user in unauthorized_users:
            print(f"   [SECURITY FIX] Removing UNAUTHORIZED ADMIN: {user}...")
            
           
            cmd = f"gpasswd -d {user} {ADMIN_GROUP}"
            subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            details.append(f"Removed '{user}'")

    if drift_detected:
        return True, f"Admin Group Cleaned: {', '.join(details)}"
    
    return False, None