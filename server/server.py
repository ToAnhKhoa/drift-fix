from flask import Flask, request, jsonify, render_template
from datetime import datetime

app = Flask(__name__)

# ==========================================
# CONFIGURATION
# ==========================================
API_SECRET_KEY = "prethesis"

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
    token = req.headers.get('X-Api-Key')
    return token == API_SECRET_KEY

# ==========================================
# API ENDPOINTS
# ==========================================

@app.route('/')
def home():
    """Dashboard Interface"""
    return render_template('index.html')
@app.route('/api/policy', methods=['GET'])
def get_policy():
    """API provide policy to Agents"""
    return jsonify(current_policy)

@app.route('/api/report', methods=['POST'])
def receive_report():
    """API receive reports from Agents"""
    if not check_auth(request):
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json
    hostname = data.get('hostname')
    status = data.get('status') 
    
    # Update inventory
    device_inventory[hostname] = {
        "ip": request.remote_addr,
        "status": status,
        "os": data.get('os'),
        "last_seen": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "message": data.get('message')
    }
    
    # Log to console (English)
    print(f"\n[REPORT] Received from {hostname} | Status: {status} | OS: {data.get('os')}")
    return jsonify({"message": "Report received", "server_time": datetime.now()}), 200

@app.route('/api/inventory', methods=['GET'])
def get_inventory():
    return jsonify(device_inventory)

if __name__ == '__main__':
    print(f"[*] Server starting... API Key: {API_SECRET_KEY}")
    app.run(host='0.0.0.0', port=5000, debug=True)