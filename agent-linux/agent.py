import os
import time
import socket

# ==========================================
# LINUX AGENT - FILE INTEGRITY MONITOR
# ==========================================

# Cấu hình file cấm (Giả lập file rác hoặc malware)
PROHIBITED_FILE = "/tmp/virus.txt"

def check_file_drift():
    """Kiểm tra xem file cấm có tồn tại không"""
    if os.path.exists(PROHIBITED_FILE):
        return "DRIFT" # Phát hiện lỗi
    else:
        return "SAFE"  # An toàn

def fix_drift():
    """Hành động sửa lỗi: Xóa file cấm"""
    print(f"   [ACTION] Phat hien file cam: {PROHIBITED_FILE}. Dang xoa...")
    try:
        os.remove(PROHIBITED_FILE)
        print("   -> Da xoa file thanh cong.")
        return True
    except OSError as e:
        print(f"   -> Loi: Khong the xoa file. {e}")
        return False

def run_agent_job():
    print(f"\n[CHECK] Kiem tra su ton tai cua file: {PROHIBITED_FILE}...")
    status = check_file_drift()
    
    if status == "SAFE":
        print("   -> OK: He thong sach se.")
    else:
        print("   -> CANH BAO: Phat hien file vi pham chinh sach!")
        # Kích hoạt tự động sửa lỗi
        fix_drift()

if __name__ == "__main__":
    # Lấy thông tin máy để hiển thị
    hostname = socket.gethostname()
    print(f"Khoi dong Linux Agent tren {hostname}...")
    print("Nhan Ctrl+C de dung chuong trinh.\n")

    while True:
        run_agent_job()
        time.sleep(5) # Chạy chu kỳ 5 giây/lần