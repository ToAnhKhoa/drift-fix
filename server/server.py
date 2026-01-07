import json
import os
from flask import Flask, request, jsonify, render_template
from datetime import datetime

app = Flask(__name__)

# ==========================================
# STUDENT INFO
# ==========================================
# Name:  [DIEN_TEN_BAN_VAO_DAY]
# Class: [DIEN_LOP_VAO_DAY]

# ==========================================
# CONFIGURATION
# ==========================================
API_SECRET_KEY = "prethesis"
device_inventory = {} # In-memory storage for Dashboard

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
POLICY_FILE = os.path.join(BASE_DIR, 'policies', 'policy.json')
LOG_DIR = os.path.join(BASE_DIR, 'logs')

# Ensure logs directory exists
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# ==========================================
# HELPER FUNCTIONS
# ==========================================

def save_log_to_file(hostname, data):
    """Save report to persistent log file"""
    log_file = os.path.join(LOG_DIR, 'agent_history.log')
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    log_entry = f"[{timestamp}] HOST: {hostname} | STATUS: {data.get('status')} | MSG: {data.get('message')}\n"
    
    try:
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry)
    except Exception as e:
        print(f"[ERROR] Could not write to log file: {e}")

def check_auth(req):
    return req.headers.get('X-Api-Key') == API_SECRET_KEY

# ==========================================
# API ENDPOINTS
# ==========================================

@app.route('/')
def home():
    """Dashboard Interface"""
    return render_template('index.html')

@app.route('/blocked_warning')
def blocked_page():
    """Show Access Denied page for blocked sites"""
    return render_template('blocked.html')

# Catch-all for 404 to support DNS redirection
@app.errorhandler(404)
def page_not_found(e):
    return render_template('blocked.html'), 404

@app.route('/api/policy', methods=['GET'])
def get_policy():
    """Serve policy.json to Agents"""
    try:
        with open(POLICY_FILE, 'r') as f:
            policy_data = json.load(f)
            return jsonify(policy_data)
    except Exception as e:
        return jsonify({"error": "Cannot read policy file", "details": str(e)}), 500

@app.route('/api/report', methods=['POST'])
def receive_report():
    """Handle reports from Agents"""
    if not check_auth(request):
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json
    hostname = data.get('hostname')
    status = data.get('status') 
    
    # 1. Update Inventory (RAM)
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

    # 2. Save to Log File (HDD)
    save_log_to_file(hostname, data)
    
    # Log to Console
    print(f"\n[REPORT] From {hostname} | Status: {status} | Msg: {data.get('message')}")
    
    return jsonify({"message": "Report received", "server_time": datetime.now()}), 200

@app.route('/api/inventory', methods=['GET'])
def get_inventory():
    """API for Dashboard AJAX"""
    return jsonify(device_inventory)

# ==========================================
# ADMIN PORTAL
# ==========================================

@app.route('/admin')
def admin_page():
    """Render Admin Interface"""
    try:
        with open(POLICY_FILE, 'r') as f:
            policy = json.load(f)
        return render_template('admin.html', policy=policy)
    except:
        return "Error loading policy file. Please check server logs."

@app.route('/admin/save', methods=['POST'])
def save_policy():
    """Save Policy from Admin Form"""
    
    # --- HANDLING BLOCKED SITES LIST ---
    blocked_sites_raw = request.form.get('blocked_sites_json')
    try:
        # Parse JSON string to Python List
        blocked_list = json.loads(blocked_sites_raw) if blocked_sites_raw else []
    except:
        blocked_list = []

    new_policy = {
        "windows": {
            "service_name": request.form.get('win_service'),
            "desired_state": request.form.get('win_state'),
            "firewall": request.form.get('win_firewall'),
            "blocked_sites": blocked_list  # Save as List
        },
        "linux": {
            "prohibited_file": request.form.get('linux_file')
        }
    }
    
    # --- MISSING PART ADDED BELOW ---
    try:
        with open(POLICY_FILE, 'w') as f:
            json.dump(new_policy, f, indent=4)
        
        print(f"[ADMIN] Policy updated! Blocked sites count: {len(blocked_list)}")
        return render_template('admin.html', policy=new_policy)
    except Exception as e:
        return f"Error saving policy: {e}"

if __name__ == '__main__':
    print(f"[*] Master Server Online on Port 5000...")
    app.run(host='0.0.0.0', port=5000, debug=True)