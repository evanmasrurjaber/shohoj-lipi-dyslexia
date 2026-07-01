import sys
sys.path.insert(0, '.')
from backend.main import route_and_simplify

edge_cases = [
    ("", "Empty Input"),
    ("Hello, how are you today?", "Pure English"),
    ("বাংলাদেশের economy is growing very fast.", "Mixed Script (Bangla/English)"),
    ("!@#$%^&*()_+", "Pure Gibberish/Punctuation"),
]

print("Testing Pipeline Edge Cases...\n")

for text, desc in edge_cases:
    print(f"--- [{desc}] ---")
    print(f"Input: '{text}'")
    try:
        res = route_and_simplify(text)
        print(f"Output: '{res['final_text']}'")
        print("Status: SUCCESS (Didn't crash)\n")
    except Exception as e:
        print(f"Status: FAILED - {e}\n")
