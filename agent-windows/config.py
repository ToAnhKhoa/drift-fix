# config.py

# Server Settings
SERVER_URL = "http://10.0.0.10:5000"
API_SECRET_KEY = "prethesis"
WARNING_PAGE = f"{SERVER_URL}/blocked_warning"

# Agent Settings
REDIRECT_IP = "127.0.0.1"
HOSTS_PATH = r"C:\Windows\System32\drivers\etc\hosts"

# Timers (Seconds)
CHECK_INTERVAL = 5        # Quét 5s/lần
HEARTBEAT_INTERVAL = 1800 # Báo cáo 30p/lần
WARNING_COOLDOWN = 15     # Không spam tab cảnh báo quá 15s

# Log Settings
LOG_FILE = "drift_history.txt"  # Create Logs