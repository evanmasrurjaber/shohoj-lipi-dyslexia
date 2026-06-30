import sys
sys.path.insert(0, '.')
from ml.sentence_router import SentenceRouter

router = SentenceRouter()

tests = [
    ("নয়",                                                          "expected: Simple (class 0)"),
    ("বস বলছি",                                                     "expected: Simple (class 0)"),
    ("শুরু হলাে প্রচণ্ড বৃষ্টি",                                    "expected: Complex (class 1)"),
    ("এ দেশ অনেক সুন্দর",                                           "short - expected: Simple"),
    ("বিশ্বসাহিত্যের ইতিহাসে রবীন্দ্রনাথ ঠাকুরের সৃষ্টিকর্ম এক অনন্য স্থান অধিকার করেছে", "long - expected: Complex"),
]

print("--- Sentence Router Test ---")
for text, note in tests:
    r = router.classify(text)
    label = r["label"]
    conf  = r["score"]
    probs = r["probabilities"]
    print(f"Label: {label} | Conf: {conf:.3f} | {note}")
    print(f"  Probs: {probs}")
    print(f"  Text: {text[:60]}")
    print()
