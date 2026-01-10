import sys
import os

# Thêm đường dẫn để tìm thấy module
sys.path.append("/root/drift-fix/agent-linux")
from modules import file_guard

# 1. Tạo file giả để test
test_file = "/tmp/test_hacker.conf"
with open(test_file, "w") as f:
    f.write("password=123")

# 2. Tình huống giả định: File bị chmod 777 (Ai cũng xem được)
os.chmod(test_file, 0o777)
print(f"❌ Quyền ban đầu: {oct(os.stat(test_file).st_mode)[-3:]}")

# 3. Gọi File Guard để sửa về 600
print("Dang goi File Guard...")
policy = [{"path": test_file, "mode": "600"}]
drift, msg = file_guard.check_and_enforce_perms(policy)

# 4. Kiểm tra kết quả
final_mode = oct(os.stat(test_file).st_mode)[-3:]
print(f"✅ Quyền sau khi fix: {final_mode}")
print(f"Log: {msg}")

# Dọn dẹp
if os.path.exists(test_file):
    os.remove(test_file)