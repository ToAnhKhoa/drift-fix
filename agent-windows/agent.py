import subprocess
import time
import ctypes, sys

# ==========================================
# WINDOWS AGENT - AUTO REMEDIATION
# ==========================================

SERVICE_NAME = "Spooler"
DESIRED_STATE = "STOPPED"

def is_admin():
    """Kiểm tra xem Python có đang chạy với quyền Admin không"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def check_service_status(service_name):
    try:
        cmd = ["sc", "query", service_name]
        # Dùng shell=True để giấu cửa sổ đen pop-up
        result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
        if "RUNNING" in result.stdout:
            return "RUNNING"
        elif "STOPPED" in result.stdout:
            return "STOPPED"
        else:
            return "UNKNOWN"
    except:
        return "ERROR"

def fix_drift(service_name):
    """Hàm thực thi hành động sửa lỗi"""
    print(f"   🚑 ACTION: Đang kích hoạt quy trình sửa lỗi cho {service_name}...")
    try:
        # Lệnh net stop sẽ đợi dịch vụ tắt hẳn mới xong (tốt hơn sc stop)
        cmd = f"net stop {service_name}"
        subprocess.run(cmd, shell=True, check=True, capture_output=True)
        print(f"   -> ✅ Đã gửi lệnh tắt dịch vụ thành công!")
    except subprocess.CalledProcessError:
        print(f"   -> ❌ Thất bại! Bạn có đang chạy với quyền Administrator không?")

def run_agent_job():
    print(f"\n🔍 [CHECK] Kiểm tra dịch vụ: {SERVICE_NAME}...")
    current_state = check_service_status(SERVICE_NAME)
    
    if current_state == DESIRED_STATE:
        print(f"   -> ✅ OK: Hệ thống ổn định ({current_state}).")
    else:
        print(f"   -> ⚠️ DRIFT: Phát hiện lệch cấu hình! (Đang: {current_state} | Cần: {DESIRED_STATE})")
        
        # GỌI HÀM SỬA LỖI NGAY LẬP TỨC
        fix_drift(SERVICE_NAME)
        
        # Kiểm tra lại ngay sau khi sửa
        time.sleep(2)
        final_state = check_service_status(SERVICE_NAME)
        if final_state == DESIRED_STATE:
            print(f"   -> 🎉 REMEDIATION SUCCESS: Đã tự động sửa lỗi thành công!")
        else:
            print(f"   -> 💀 REMEDIATION FAILED: Vẫn chưa sửa được.")

if __name__ == "__main__":
    if not is_admin():
        print("❌ CẢNH BÁO: Bạn chưa chạy script với quyền Admin (Run as Administrator).")
        print("   Agent sẽ không thể tắt dịch vụ được!")
        print("   -> Hãy tắt VS Code và mở lại bằng chuột phải -> 'Run as administrator'.")
        input("\nBấm Enter để thoát...")
    else:
        print("🛡️ AGENT ĐANG CHẠY (ADMIN MODE)... Bấm Ctrl+C để dừng.")
        while True:
            run_agent_job()
            print("zzz... Chờ 5 giây...")
            time.sleep(5)