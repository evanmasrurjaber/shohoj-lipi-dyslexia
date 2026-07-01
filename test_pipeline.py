"""
Quick end-to-end pipeline test with real Gemini LLM.
"""
import sys
import os
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, '.')

from ml.readability_scorer import compute_readability, init_scorer
from backend.main import route_and_simplify

print("Initializing pipeline components...")
init_scorer()
# The backend main.py automatically initializes the router and LLM on import
print("All components loaded.\n")

test_passages = [
    "বাংলাদেশের অর্থনীতি মূলত কৃষিনির্ভর এবং বিশ্ববাজারে পোশাক রপ্তানিতে উল্লেখযোগ্য ভূমিকা রাখে।",
    "বিশ্বসাহিত্যের ইতিহাসে রবীন্দ্রনাথ ঠাকুরের সৃষ্টিকর্ম এক অনন্য স্থান অধিকার করেছে। তাঁর কবিতা ও গল্প বিশ্বের বিভিন্ন ভাষায় অনূদিত হয়েছে।",
]

print("=" * 60)
for i, passage in enumerate(test_passages, 1):
    print(f"\n[Passage {i}]")
    print(f"Original: {passage}")

    before = compute_readability(passage)
    print(f"Readability before: {before['tier']} (score={before['score']})")

    result = route_and_simplify(passage)
    simplified = result["final_text"]
    
    print(f"Simplified: {simplified}")
    
    after = compute_readability(simplified)
    print(f"Readability after: {after['tier']} (score={after['score']})")
    print(f"Score delta: {before['score'] - after['score']:+.3f}")
    
    print("Sentence Breakdown:")
    for step in result["processed"]:
        print(f"  - [{step['was_complex']}] Conf: {step['confidence']:.2f}")
        print(f"    In:  {step['original']}")
        print(f"    Out: {step['simplified']}")

print("\n" + "=" * 60)
print("Pipeline test complete!")
