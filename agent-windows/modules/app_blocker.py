# modules/app_blocker.py
import ctypes
import time
import webbrowser
import utils
from config import WARNING_PAGE, WARNING_COOLDOWN

user32 = ctypes.windll.user32
last_warn = 0

def get_active_title():
    try:
        hwnd = user32.GetForegroundWindow()
        length = user32.GetWindowTextLengthW(hwnd)
        buff = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buff, length + 1)
        return buff.value.lower()
    except:
        return ""

def check_window_title(blocked_list):
    global last_warn
    if not blocked_list: return False, None
    
    title = get_active_title()
    if not title: return False, None
    
    for site in blocked_list:
        keyword = site.replace("www.", "").split('.')[0]
        
        if keyword in title:
            print(f"   [APP ALERT] Detected: {title}")
            
            if time.time() - last_warn > WARNING_COOLDOWN:
                print("   [ACTION] Opening Warning Page...")
                webbrowser.open(WARNING_PAGE)
                last_warn = time.time()
                
                # --- GHI LOG ---
                utils.write_local_log(
                    "APP_VIOLATION", 
                    f"User opened blocked window: '{title}'", 
                    "Redirected to Warning Page"
                )
                
                return True, f"Blocked App Access: {title}"
                
    return False, None