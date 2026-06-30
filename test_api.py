"""
test_api.py — Quick test script for the FastAPI backend
"""
import urllib.request
import json

url = "http://localhost:8000/api/simplify"
payload = {
    "text": "বাংলাদেশের অর্থনীতি মূলত কৃষিনির্ভর। এখানকার মানুষ অত্যন্ত পরিশ্রমী।",
    "target_tier": "Easy"
}

req = urllib.request.Request(
    url, 
    data=json.dumps(payload).encode('utf-8'),
    headers={'Content-Type': 'application/json'}
)

print(f"Sending request to {url}...")
print(f"Input text: {payload['text']}")
print("-" * 50)

try:
    with urllib.request.urlopen(req) as response:
        result = json.loads(response.read().decode())
        print("✅ SUCCESS! Here is the JSON response:\n")
        print(json.dumps(result, indent=2, ensure_ascii=False))
except Exception as e:
    print(f"❌ ERROR: {e}")
    print("Make sure the backend is running (uvicorn backend.main:app --port 8000)")
