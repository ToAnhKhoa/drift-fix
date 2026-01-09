import psutil
import datetime
import os

def get_cpu_usage():
    """Returns CPU usage percentage."""
    try:
        return psutil.cpu_percent(interval=None)
    except: return 0

def get_ram_usage():
    """Returns RAM usage percentage."""
    try:
        return psutil.virtual_memory().percent
    except: return 0

def get_disk_usage():
    """Returns Disk usage percentage (Root partition)."""
    try:
        # Linux uses '/' as root, unlike 'C:\\' in Windows
        return psutil.disk_usage('/').percent
    except: return 0

def write_local_log(category, action, details):
    """Appends logs to a local file."""
    # Linux path uses forward slashes
    log_dir = "/var/log/driftguard"
    log_file = os.path.join(log_dir, "agent.log")
    
    # Ensure directory exists (Linux specific)
    if not os.path.exists(log_dir):
        try:
            os.makedirs(log_dir, exist_ok=True)
        except: 
            # Fallback to current directory if permission denied
            log_file = "agent_history.log"

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] [{category}] {action} - {details}\n")
    except Exception as e:
        print(f"Error writing log: {e}")