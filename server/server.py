import json
import os
from flask import Flask, request, jsonify, render_template
from datetime import datetime

app = Flask(__name__)
device_inventory = {}
# ==========================================
# CONFIGURATION
# ==========================================
API_SECRET_KEY = "prethesis"

# Path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
POLICY_FILE = os.path.join(BASE_DIR, 'policies', 'policy.json')
LOG_DIR = os.path.join(BASE_DIR, 'logs')
# Check if logs exist
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)
def save_log_to_file(hostname, data):
    """Lưu báo cáo vào file text để lưu trữ lâu dài"""
    log_file = os.path.join(LOG_DIR, 'agent_history.log')
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    log_entry = f"[{timestamp}] HOST: {hostname} | STATUS: {data.get('status')} | MSG: {data.get('message')}\n"
    
    # Ghi nối đuôi (append mode 'a')
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(log_entry)
# Centralized Policy
current_policy = {
    "windows": {
        "service_name": "Spooler",
        "desired_state": "STOPPED"
    },
    "linux": {
        "prohibited_file": "/tmp/virus.txt"
    }
}

device_inventory = {}

def check_auth(req):
    return req.headers.get('X-Api-Key') == API_SECRET_KEY

# ==========================================
# API ENDPOINTS
# ==========================================

@app.route('/')
def home():
    return render_template('index.html')
@app.route('/api/policy', methods=['GET'])
def get_policy():
    """Đọc cấu hình từ file JSON thật"""
    try:
        with open(POLICY_FILE, 'r') as f:
            policy_data = json.load(f)
            return jsonify(policy_data)
    except Exception as e:
        return jsonify({"error": "Cannot read policy file", "details": str(e)}), 500

@app.route('/api/report', methods=['POST'])
def receive_report():
    if not check_auth(request):
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json
    hostname = data.get('hostname')
    status = data.get('status') 
    
    # Update inventory
    # Temp save in RAM
    device_inventory[hostname] = {
        "ip": request.remote_addr,
        "status": data.get('status'),
        "os": data.get('os'),
        "os_full": data.get('os_full', 'Unknown'),
        "os_release": data.get('os_release', 'Unknown'),
        "open_ports": data.get('open_ports', []),
        "last_seen": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "message": data.get('message'),
        "cpu": data.get('cpu', 0),
        "ram": data.get('ram', 0),
        "disk": data.get('disk', 0)
    }
    # Save logs
    save_log_to_file(hostname, data)
    
    print(f"[LOG] Saved report from {hostname} to file.")
    return jsonify({"message": "Report logged successfully"}), 200
    
    # Log to console (English)
    print(f"\n[REPORT] Received from {hostname} | Status: {status} | OS: {data.get('os')}")
    return jsonify({"message": "Report received", "server_time": datetime.now()}), 200

@app.route('/api/inventory', methods=['GET'])
def get_inventory():
    return jsonify(device_inventory)
@app.route('/admin')
def admin_page():
    """Hiển thị trang chỉnh sửa Policy"""
    try:
        with open(POLICY_FILE, 'r') as f:
            policy = json.load(f)
        return render_template('admin.html', policy=policy)
    except:
        return "Error loading policy file."

@app.route('/admin/save', methods=['POST'])
def save_policy():
    """Lưu cấu hình từ Form vào file JSON"""
    new_policy = {
        "windows": {
            "service_name": request.form.get('win_service'),
            "desired_state": request.form.get('win_state'),
            "firewall": request.form.get('win_firewall'),       # <--- MỚI
            "blocked_site": request.form.get('win_blocked_site') # <--- MỚI
        },
        "linux": {
            "prohibited_file": request.form.get('linux_file')
        }
    }
    
    try:
        with open(POLICY_FILE, 'w') as f:
            json.dump(new_policy, f, indent=4)
        print("[ADMIN] Policy updated by Admin.")
        return render_template('admin.html', policy=new_policy) # Load lại trang với data mới
    except Exception as e:
        return f"Error saving policy: {e}"

if __name__ == '__main__':
    print(f"[*] Server File-Based Mode Started...")
    app.run(host='0.0.0.0', port=5000, debug=True)