import os
import sys
import subprocess

# 1. XÁC ĐỊNH MÔI TRƯỜNG PYTHON
is_64bits = sys.maxsize > 2**32
arch = "64-bit" if is_64bits else "32-bit"
print(f"=== DIAGNOSTIC TOOL ===")
print(f"[*] Python Architecture: {arch}")

# 2. XÁC ĐỊNH ĐƯỜNG DẪN MÀ CODE ĐANG DÙNG
if os.path.exists(r"C:\Windows\Sysnative"):
    HOSTS_PATH = r"C:\Windows\Sysnative\drivers\etc\hosts"
    print("[*] Detected Sysnative. Target Path: " + HOSTS_PATH)
else:
    HOSTS_PATH = r"C:\Windows\System32\drivers\etc\hosts"
    print("[*] Standard Path: " + HOSTS_PATH)

# 3. ĐỌC THỰC TẾ FILE ĐÓ (PYTHON NHÌN THẤY GÌ?)
print("\n[*] Reading file content via Python...")
try:
    with open(HOSTS_PATH, 'r') as f:
        content = f.read()
        if "DRIFTGUARD" in content:
            print("   ✅ YES! Python found 'DRIFTGUARD' in the file.")
            print("   --- Content Snippet ---")
            print(content[-200:]) # In 200 ký tự cuối
            print("   -----------------------")
        else:
            print("   ❌ NO! File is clean (No blocking rules found).")
            print(f"   -> File size: {len(content)} bytes")
except Exception as e:
    print(f"   ❌ Error reading file: {e}")

# 4. KIỂM TRA "PING" (HỆ ĐIỀU HÀNH THẤY GÌ?)
print("\n[*] Pinging facebook.com to check resolution...")
try:
    # Ping 1 lần (-n 1) để xem nó ra IP nào
    output = subprocess.check_output("ping -n 1 facebook.com", shell=True).decode()
    if "127.0.0.1" in output:
        print("   ✅ SUCCESS: facebook.com resolves to 127.0.0.1")
        print("   -> Hosts file IS WORKING properly.")
    else:
        print("   ❌ FAIL: facebook.com resolves to Real IP.")
        print("   -> Hosts file is IGNORED or EMPTY.")
        # Lọc ra dòng chứa IP để bạn xem
        for line in output.split('\n'):
            if "Pinging" in line: print("   -> " + line.strip())
            if "Reply from" in line: print("   -> " + line.strip())
except:
    print("   ❌ Ping command failed.")

print("\n=== END ===")
input("Press Enter to exit...")