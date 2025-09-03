import requests

BASE_URL = "http://127.0.0.1:8081"

# 1. Send frame
with open("test1.jpeg", "rb") as f:
    r = requests.post(f"{BASE_URL}/frame", data=f, headers={"Content-Type": "image/jpeg"})
print("Frame:", r.json())

# 2. Get detections
r = requests.get(f"{BASE_URL}/get_detections")
print("Detections:", r.json())

# 3. Ask a question
r = requests.post(f"{BASE_URL}/question", json={"question": "What objects are present?"})
print("Question:", r.json())

# 4. Health check
r = requests.get(f"{BASE_URL}/health")
print("Health:", r.json())
