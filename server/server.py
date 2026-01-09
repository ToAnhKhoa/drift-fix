import json
import os
from flask import Flask, request, jsonify, render_template
from datetime import datetime

app = Flask(__name__)

# ==========================================
# CẤU HÌNH (CONFIGURATION)
# ==========================================
API_SECRET_KEY = "prethesis"
device_inventory = {} # Lưu trữ tạm thời trạng thái các máy (RAM)

# Đường dẫn tuyệt đối (Giúp tránh lỗi khi chạy từ thư mục khác)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
POLICY_DIR = os.path.join(BASE_DIR, 'policies')
POLICY_FILE = os.path.join(POLICY_DIR, 'policy.json')
LOG_DIR = os.path.join(BASE_DIR, 'logs')

# 1. Tạo thư mục Logs nếu chưa có
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# 2. Tạo thư mục Policies nếu chưa có
if not os.path.exists(POLICY_DIR):
    os.makedirs(POLICY_DIR)

# 3. Tạo file policy.json mặc định nếu chưa có (Tránh lỗi crash server)
if not os.path.exists(POLICY_FILE):
    print("[INIT] Policy file not found. Creating default...")
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
# HÀM HỖ TRỢ (HELPER FUNCTIONS)
# ==========================================

def save_log_to_file(hostname, data):
    """Ghi log báo cáo từ Agent vào file"""
    log_file = os.path.join(LOG_DIR, 'agent_history.log')
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    log_entry = f"[{timestamp}] HOST: {hostname} | STATUS: {data.get('status')} | MSG: {data.get('message')}\n"
    
    try:
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry)
    except Exception as e:
        print(f"[ERROR] Could not write to log file: {e}")

def check_auth(req):
    """Kiểm tra Key bảo mật"""
    return req.headers.get('X-Api-Key') == API_SECRET_KEY

# ==========================================
# API ENDPOINTS (CHO AGENT & DASHBOARD)
# ==========================================

@app.route('/')
def home():
    """Giao diện chính (Dashboard)"""
    return render_template('index.html')

@app.route('/blocked_warning')
def blocked_page():
    """Trang cảnh báo khi người dùng truy cập web cấm"""
    return render_template('blocked.html')

# Chặn tất cả các trang 404 để hiển thị cảnh báo (Hỗ trợ chuyển hướng DNS)
@app.errorhandler(404)
def page_not_found(e):
    return render_template('blocked.html'), 404

@app.route('/api/policy', methods=['GET'])
def get_policy():
    """Agent gọi vào đây để lấy Policy về thực thi"""
    try:
        with open(POLICY_FILE, 'r') as f:
            policy_data = json.load(f)
            return jsonify(policy_data)
    except Exception as e:
        # Trả về lỗi JSON để Agent biết đường xử lý
        return jsonify({"error": "Cannot read policy file", "details": str(e)}), 500

@app.route('/api/report', methods=['POST'])
def receive_report():
    """Nhận báo cáo từ Agent"""
    if not check_auth(request):
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json
    hostname = data.get('hostname')
    status = data.get('status') 
    
    # Cập nhật Inventory (RAM)
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

    # Ghi log ra file (HDD)
    save_log_to_file(hostname, data)
    
    # In ra màn hình console Server để bạn dễ debug
    print(f"\n[REPORT] From {hostname} | Status: {status} | Msg: {data.get('message')}")
    
    return jsonify({"message": "Report received", "server_time": str(datetime.now())}), 200

@app.route('/api/inventory', methods=['GET'])
def get_inventory():
    """API cho Dashboard AJAX lấy danh sách máy"""
    return jsonify(device_inventory)

# ==========================================
# ADMIN PORTAL (GIAO DIỆN QUẢN TRỊ)
# ==========================================

@app.route('/admin')
def admin_page():
    """Hiển thị trang Admin để chỉnh sửa Policy"""
    try:
        with open(POLICY_FILE, 'r') as f:
            policy = json.load(f)
        return render_template('admin.html', policy=policy)
    except:
        return "Error loading policy file. Please check server logs."

@app.route('/admin/save', methods=['POST'])
def save_policy():
    """Xử lý khi bấm nút SAVE trên trang Admin"""
    
    # 1. Xử lý danh sách Web bị chặn (Chuyển từ chuỗi JSON sang List Python)
    blocked_sites_raw = request.form.get('blocked_sites_json')
    try:
        blocked_list = json.loads(blocked_sites_raw) if blocked_sites_raw else []
    except:
        blocked_list = []

    # 2. Tạo cấu trúc Policy mới
    new_policy = {
        "windows": {
            # Lưu ý: Code này dùng service_name (đơn) theo yêu cầu của bạn. 
            # Nếu Agent dùng restricted_services (list), bạn cần sửa lại HTML và Server.
            "service_name": request.form.get('win_service'), 
            "desired_state": request.form.get('win_state'),
            "firewall": request.form.get('win_firewall'),
            "blocked_sites": blocked_list  # Đây là phần quan trọng để chặn web
        },
        "linux": {
            "prohibited_file": request.form.get('linux_file')
        }
    }
    
    # 3. Ghi đè vào file policy.json
    try:
        with open(POLICY_FILE, 'w') as f:
            json.dump(new_policy, f, indent=4)
        
        print(f"[ADMIN] Policy updated! Blocked sites count: {len(blocked_list)}")
        # Load lại trang Admin với dữ liệu mới
        return render_template('admin.html', policy=new_policy)
    except Exception as e:
        return f"Error saving policy: {e}"

if __name__ == '__main__':
    # Host '0.0.0.0' để máy khác trong mạng (máy ảo) có thể kết nối được
    print(f"[*] Master Server Online on Port 5000...")
    app.run(host='0.0.0.0', port=5000, debug=True)