import concurrent.futures
import requests
import time

API_URL = "http://127.0.0.1:8000/process"

test_texts = [
    "বিশ্বসাহিত্যের ইতিহাসে রবীন্দ্রনাথ ঠাকুরের সৃষ্টিকর্ম এক অনন্য স্থান অধিকার করেছে।",
    "বাংলাদেশের অর্থনীতি মূলত কৃষিনির্ভর। দেশের মোট শ্রমশক্তির একটি বড় অংশ কৃষিকাজে নিয়োজিত।",
    "এ দেশ অনেক সুন্দর। এ দেশে আছে বিচিত্র ধরনের পাখি।",
] * 4  # 12 requests total, using repeats on purpose to also exercise the cache


def call_process(text):
    start = time.time()
    resp = requests.post(API_URL, json={"text": text}, timeout=60)
    elapsed = time.time() - start
    return resp.status_code, elapsed, resp.json() if resp.status_code == 200 else resp.text


print(f"Firing {len(test_texts)} concurrent requests...")
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
    futures = [executor.submit(call_process, t) for t in test_texts]
    for i, future in enumerate(concurrent.futures.as_completed(futures)):
        status, elapsed, result = future.result()
        ok = "OK" if status == 200 else "FAIL"
        print(f"  [{i+1}] {ok} ({elapsed:.2f}s) status={status}")

print("\nDone. Check above for any FAIL lines or unexpectedly long times.")