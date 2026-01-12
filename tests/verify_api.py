
import requests
import time
import sys

BASE_URL = "http://localhost:8000/api"

def test_health():
    print("Testing /health...", end=" ")
    try:
        r = requests.get(f"{BASE_URL}/health")
        if r.status_code == 200 and r.json()["status"] == "healthy":
            print("OK")
            return True
        else:
            print(f"Failed: {r.text}")
            return False
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_onboard():
    print("Testing /onboard...", end=" ")
    payload = {
        "name": "Test User",
        "email": "test@example.com",
        "phone": "(555) 123-4567",
        "session_id": "test_session_123"
    }
    try:
        r = requests.post(f"{BASE_URL}/onboard", json=payload)
        if r.status_code == 200 and r.json()["success"]:
            print("OK")
            return True
        else:
            print(f"Failed: {r.text}")
            return False
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_chat():
    print("Testing /chat...", end=" ")
    payload = {
        "message": "What services do you offer?",
        "session_id": "test_session_123",
        "onboarding": {"completed": True}
    }
    try:
        r = requests.post(f"{BASE_URL}/chat", json=payload)
        if r.status_code == 200:
            resp = r.json()
            if "response" in resp:
                print("OK")
                print(f"   Response: {resp['response'][:100]}...")
                return True
        print(f"Failed: {r.text}")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False

def main():
    print("Waiting for server to start...")
    for _ in range(10):
        try:
            requests.get(f"{BASE_URL}/health")
            break
        except:
            time.sleep(1)
    
    success = True
    success &= test_health()
    success &= test_onboard()
    success &= test_chat()
    
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()
