import socket

def get_all_ips():
    print("\n" + "="*40)
    print("  DANH SÁCH IP TRÊN MÁY NÀY")
    print("="*40)

    # 1: Thử kết nối ra Internet 
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        print(f" IP Internet (NAT):  {s.getsockname()[0]}")
        s.close()
    except:
        pass

    # 2: Thử kết nối vào mạng LAB 
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("10.0.0.10", 80)) 
        ip_lab = s.getsockname()[0]
        print(f" IP Mạng Lab (LAN):  {ip_lab}")
        
        if ip_lab == "10.0.0.30":
            print("   ->  OK! Đúng IP cần tìm.")
        else:
            print("   ->  Sai IP Lab, kiểm tra lại cài đặt mạng.")
            
    except Exception as e:
        print(f" Không tìm thấy mạng Lab: {e}")

    # 3: Liệt kê thủ công
    print("-" * 20)
    print("Chi tiết các card mạng:")
    hostname = socket.gethostname()
    try:
        # Lấy tất cả IP gắn với hostname
        addr_info = socket.getaddrinfo(hostname, None)
        seen_ips = set()
        for info in addr_info:
            ip = info[4][0]
            if ip not in seen_ips and ":" not in ip: # Chỉ lấy IPv4
                print(f" - {ip}")
                seen_ips.add(ip)
    except:
        print("Không liệt kê được chi tiết.")

    print("="*40 + "\n")

if __name__ == "__main__":
    get_all_ips()