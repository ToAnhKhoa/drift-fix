from flask import Flask, request, jsonify
from datetime import datetime

app = Flask(__name__)
# CẤU HÌNH BẢO MẬT & DATABASE GIẢ LẬP
API_SECRET_KEY = "prethesis"

# Database tạm thời
# Cấu trúc: { "hostname": { "ip": "...", "status": "...", "last_seen": "..." } }
device_inventory = {}
# CENTRALIZED POLICY (Luật tập trung)
current_policy = {
    "windows": {
        "service_name": "Spooler",  
        "desired_state": "STOPPED"
    },
    "linux": {
        "prohibited_file": "/tmp/virus.txt" 
    }
}
# CÁC HÀM HỖ TRỢ (HELPER)
def check_auth(req):
    """Kiểm tra xem Agent có gửi đúng Key không"""
    token = req.headers.get('X-Api-Key')
    if token == API_SECRET_KEY:
        return True
    return False
# API ENDPOINTS

@app.route('/')
def home():
    """Trang chủ đơn giản để test server sống hay chết"""
    return "<h1>MASTER SERVER IS ONLINE 🚀</h1><p>Ready to receive reports.</p>"

@app.route('/api/report', methods=['POST'])
def receive_report():
    """API nhận báo cáo từ Agent"""
    # 1. Kiểm tra bảo mật
    if not check_auth(request):
        return jsonify({"error": "Unauthorized. Sai API Key!"}), 401

    # 2. Lấy dữ liệu JSON gửi lên
    data = request.json
    hostname = data.get('hostname')
    status = data.get('status') # SAFE hoặc DRIFT
    
    # 3. Lưu vào 'Database'
    device_inventory[hostname] = {
        "ip": request.remote_addr,
        "status": status,
        "last_seen": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "details": data
    }
    
    print(f"\n[REPORT] Nhan tin hieu tu {hostname} | Trang thai: {status}")
    return jsonify({"message": "Report received", "server_time": datetime.now()}), 200

@app.route('/api/inventory', methods=['GET'])
def get_inventory():
    """API xem danh sách thiết bị (Dùng cho Dashboard sau này)"""
    return jsonify(device_inventory)
@app.route('/api/policy', methods=['GET'])
def get_policy():
    """API để Agent tải cấu hình về"""
    return jsonify(current_policy)
if __name__ == '__main__':
    # Chạy server trên tất cả các IP (0.0.0.0) ở port 5000
    print(f"[*] Server dang khoi dong... API Key: {API_SECRET_KEY}")
    app.run(host='0.0.0.0', port=5000, debug=True)