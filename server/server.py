import json
import os
from flask import Flask, request, jsonify, render_template
from datetime import datetime

app = Flask(__name__)

# ==========================================
# CONFIGURATION
# ==========================================
API_SECRET_KEY = "prethesis"
device_inventory = {}  # In-memory storage for device status

# Absolute paths to ensure stability across environments
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
POLICY_DIR = os.path.join(BASE_DIR, 'policies')
POLICY_FILE = os.path.join(POLICY_DIR, 'policy.json')
LOG_DIR = os.path.join(BASE_DIR, 'logs')

# 1. Initialize Log Directory
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# 2. Initialize Policy Directory
if not os.path.exists(POLICY_DIR):
    os.makedirs(POLICY_DIR)

# 3. Create Default Policy if missing (Fail-safe)
if not os.path.exists(POLICY_FILE):
    print("[INIT] Policy file not found. Creating default configuration...")
    default_policy = {
        "windows": {
            "blocked_sites": [],
            "service_name": "Spooler",
            "desired_state": "STOPPED",
            "firewall": "OFF"
        },
        "linux": {
            "prohibited_file": ""
        }
    }
    with open(POLICY_FILE, 'w') as f:
        json.dump(default_policy, f, indent=4)

# ==========================================
# HELPER FUNCTIONS
# ==========================================

def save_log_to_file(hostname, data):
    """Persist agent reports to disk."""
    log_file = os.path.join(LOG_DIR, 'agent_history.log')
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    log_entry = f"[{timestamp}] HOST: {hostname} | STATUS: {data.get('status')} | MSG: {data.get('message')}\n"
    
    try:
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry)
    except Exception as e:
        print(f"[ERROR] Failed to write log: {e}")

def check_auth(req):
    """Validate API Key."""
    return req.headers.get('X-Api-Key') == API_SECRET_KEY

# ==========================================
# API ENDPOINTS
# ==========================================

@app.route('/')
def home():
    """Dashboard Home."""
    return render_template('index.html')

@app.route('/blocked_warning')
def blocked_page():
    """Render the Access Denied page."""
    return render_template('blocked.html')

# Catch-all 404 handler to redirect blocked DNS requests to warning page
@app.errorhandler(404)
def page_not_found(e):
    return render_template('blocked.html'), 404

@app.route('/api/policy', methods=['GET'])
def get_policy():
    """Endpoint for Agents to fetch the latest policy."""
    try:
        with open(POLICY_FILE, 'r') as f:
            policy_data = json.load(f)
            return jsonify(policy_data)
    except Exception as e:
        return jsonify({"error": "Failed to read policy file", "details": str(e)}), 500

@app.route('/api/report', methods=['POST'])
def receive_report():
    """Endpoint to receive status reports from Agents."""
    if not check_auth(request):
        return jsonify({"error": "Unauthorized Access"}), 401

    data = request.json
    hostname = data.get('hostname')
    status = data.get('status') 
    
    # Update In-Memory Inventory
    device_inventory[hostname] = {
        "ip": request.remote_addr,
        "status": status,
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

    # Save to Disk Log
    save_log_to_file(hostname, data)
    
    # Server Console Output
    print(f"\n[REPORT] From: {hostname} | Status: {status} | Msg: {data.get('message')}")
    
    return jsonify({"message": "Report acknowledged", "server_time": str(datetime.now())}), 200

@app.route('/api/inventory', methods=['GET'])
def get_inventory():
    """API for Dashboard to fetch live device list."""
    return jsonify(device_inventory)

# ==========================================
# ADMIN PORTAL
# ==========================================

@app.route('/admin')
def admin_page():
    """Render Admin Panel."""
    try:
        with open(POLICY_FILE, 'r') as f:
            policy = json.load(f)
        return render_template('admin.html', policy=policy)
    except:
        return "Error loading policy file. Please check server logs."

@app.route('/admin/save', methods=['POST'])
def save_policy():
    """Handle Policy Updates from Admin Panel."""
    
    # 1. Parse Blocked Sites List
    blocked_sites_raw = request.form.get('blocked_sites_json')
    try:
        blocked_list = json.loads(blocked_sites_raw) if blocked_sites_raw else []
    except:
        blocked_list = []

    # 2. Construct New Policy Object
    new_policy = {
        "windows": {
            "service_name": request.form.get('win_service'), 
            "desired_state": request.form.get('win_state'),
            "firewall": request.form.get('win_firewall'),
            "blocked_sites": blocked_list 
        },
        "linux": {
            "prohibited_file": request.form.get('linux_file')
        }
    }
    
    # 3. Save to Disk
    try:
        with open(POLICY_FILE, 'w') as f:
            json.dump(new_policy, f, indent=4)
        
        print(f"[ADMIN] Policy updated successfully. Blocked sites count: {len(blocked_list)}")
        return render_template('admin.html', policy=new_policy)
    except Exception as e:
        return f"Error saving policy: {e}"

if __name__ == '__main__':
    print(f"[*] Master Server initialized on Port 5000...")
    app.run(host='0.0.0.0', port=5000, debug=True)