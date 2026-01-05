import os
import time
import socket
import requests

SERVER_URL = "http://10.0.0.10:5000"
API_SECRET_KEY = "prethesis"

def get_policy():
    try:
        response = requests.get(f"{SERVER_URL}/api/policy", timeout=2)
        if response.status_code == 200:
            data = response.json()
            return data.get("linux")
    except:
        return None
    return None

def send_report(status, message):
    try:
        payload = {
            "hostname": socket.gethostname(),
            "os": "Linux",
            "status": status,
            "message": message
        }
        headers = {"X-Api-Key": API_SECRET_KEY}
        requests.post(f"{SERVER_URL}/api/report", json=payload, headers=headers, timeout=2)
        print("   -> [REPORT] Sent successfully.")
    except:
        print("   -> [REPORT] Failed to send.")

def run_agent_job():
    print(f"\n[SYNC] Pulling Policy from Server...")
    policy = get_policy()
    
    if not policy:
        print("   -> Connection failed. Using fallback.")
        target_file = "/tmp/virus.txt"
    else:
        target_file = policy["prohibited_file"]
        print(f"   -> Policy: Prohibited file '{target_file}'")

    if os.path.exists(target_file):
        print("   -> WARNING: Violation Detected!")
        send_report("DRIFT", f"Found prohibited file: {target_file}")
        
        print("   [ACTION] Deleting file...")
        try:
            os.remove(target_file)
            print("   -> File deleted.")
            send_report("SAFE", "Auto-remediation success")
        except:
            print("   -> Failed to delete.")
    else:
        print("   -> OK: System Clean.")
        send_report("SAFE", "System Clean")

if __name__ == "__main__":
    print("Linux Agent (Smart Mode) starting...")
    while True:
        run_agent_job()
        time.sleep(10)