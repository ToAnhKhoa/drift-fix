import os
# 1. HỆ THỐNG FILE (AUTO-DETECT LOGIC)
# Logic này giúp Python tìm đúng đường dẫn file hosts thật, 
# tránh bị Windows lừa vào thư mục ảo (SysWOW64).

if os.path.exists(r"C:\Windows\Sysnative"):
    # Nếu tìm thấy Sysnative -> Python 32-bit đang chạy trên Win 64-bit
    HOSTS_PATH = r"C:\Windows\Sysnative\drivers\etc\hosts"
    print("   [CONFIG] Detected 32-bit Python. Using Sysnative path.")
else:
    # Trường hợp bình thường (Python 64-bit hoặc Win 32-bit)
    HOSTS_PATH = r"C:\Windows\System32\drivers\etc\hosts"
# 2. CẤU HÌNH SERVER
SERVER_URL = "http://10.0.0.10:5000"
API_SECRET_KEY = "prethesis"
WARNING_PAGE = f"{SERVER_URL}/blocked_warning"
# 3. CẤU HÌNH AGENT
REDIRECT_IP = "127.0.0.1"
# 4. THỜI GIAN & HIỆU NĂNG
CHECK_INTERVAL = 5        
HEARTBEAT_INTERVAL = 1800 
WARNING_COOLDOWN = 15     
# 5. LOGGING
LOG_FILE = "drift_history.txt"