"""
debug_pipeline.py — Step-by-step pipeline diagnostics
Run from the project root:  python debug_pipeline.py

This script tests every layer independently and prints exactly what's
happening so you can pinpoint the stuck component.
"""

import sys, os
from pathlib import Path

# Match main.py's path setup exactly
sys.path.insert(0, str(Path(__file__).parent))          # root
sys.path.insert(0, str(Path(__file__).parent / "backend"))  # backend/

from dotenv import load_dotenv
load_dotenv(dotenv_path=Path(__file__).parent / "backend" / ".env")

# ── Reconfigure stdout for Bangla ──────────────────────────────────────────
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

EASY_TEXT  = "এ দেশ অনেক সুন্দর। এ দেশে আছে বিচিত্র ধরনের পাখি।"
HARD_TEXT  = ("বিশ্বসাহিত্যের ইতিহাসে রবীন্দ্রনাথ ঠাকুরের সৃষ্টিকর্ম এক অনন্য স্থান অধিকার করেছে। "
              "তাঁর কবিত্বশক্তি, দার্শনিক চিন্তাভাবনা এবং মানবতাবাদী দৃষ্টিভঙ্গি অতুলনীয়।")

SEP = "=" * 65

# ── STEP 1: Environment variables ─────────────────────────────────────────────
print(SEP)
print("STEP 1 — Environment Variables")
print(SEP)
api_key = os.getenv("GEMINI_API_KEY", "")
if not api_key or api_key == "your_gemini_api_key_here":
    print("❌  GEMINI_API_KEY is NOT set or still a placeholder!")
    print("    → Get a free key at https://aistudio.google.com/apikey")
    print("    → Add it to backend/.env as: GEMINI_API_KEY=AIzaSy...")
else:
    masked = api_key[:8] + "..." + api_key[-4:]
    print(f"✅  GEMINI_API_KEY loaded: {masked}")

# ── STEP 2: Readability scorer ────────────────────────────────────────────
print()
print(SEP)
print("STEP 2 — Readability Scorer")
print(SEP)
try:
    from ml.readability_scorer import compute_readability, init_scorer, EASY_WORDS
    init_scorer()
    from ml.readability_scorer import EASY_WORDS  # reload after init
    print(f"Easy words loaded: {len(EASY_WORDS)}")

    easy_result = compute_readability(EASY_TEXT)
    hard_result = compute_readability(HARD_TEXT)

    print(f"\nEASY text  → score={easy_result['score']:.4f}  tier={easy_result['tier']}")
    print(f"HARD text  → score={hard_result['score']:.4f}  tier={hard_result['tier']}")

    if easy_result['score'] == hard_result['score']:
        print("❌  BOTH SCORES ARE IDENTICAL — scorer is broken!")
        print("   Likely cause: easy_word_list.txt or conjunct_list.txt not found.")
        print("   Features:")
        for k, v in easy_result['features'].items():
            print(f"     {k}: {v}")
    elif abs(easy_result['score'] - hard_result['score']) < 0.05:
        print("⚠️   Scores are very close — scorer may have low sensitivity")
    else:
        print("✅  Scores differ correctly between easy and hard text")
except Exception as e:
    print(f"❌  Scorer failed: {e}")
    import traceback; traceback.print_exc()

# ── STEP 3: Sentence Router ───────────────────────────────────────────────
print()
print(SEP)
print("STEP 3 — Sentence Router (BanglaBERT ONNX)")
print(SEP)
try:
    from ml.sentence_router import SentenceRouter
    router = SentenceRouter()

    easy_sent = "এ দেশ অনেক সুন্দর।"
    hard_sent  = "বিশ্বসাহিত্যের ইতিহাসে রবীন্দ্রনাথ ঠাকুরের সৃষ্টিকর্ম এক অনন্য স্থান অধিকার করেছে।"

    r_easy = router.classify(easy_sent)
    r_hard = router.classify(hard_sent)

    print(f"Easy sentence → label={r_easy['label']!r}  score={r_easy['score']:.4f}")
    print(f"Hard sentence → label={r_hard['label']!r}  score={r_hard['score']:.4f}")
    print(f"Full id2label map from model config: {getattr(router.model.config, 'id2label', 'NOT FOUND')}")

    if r_easy['label'] == 'Complex' and r_hard['label'] == 'Simple':
        print("❌  LABELS ARE SWAPPED! The model's id2label is reversed.")
        print("   Fix: swap the labels in sentence_router.py or retrain with correct mapping.")
    elif r_easy['label'] == r_hard['label']:
        print("⚠️   Both sentences get the SAME label — router is not discriminating.")
        print("   This means NOTHING gets sent to the LLM. Output = input.")
    else:
        print("✅  Router correctly labels easy=Simple, hard=Complex")
except Exception as e:
    print(f"❌  Router failed: {e}")
    import traceback; traceback.print_exc()

# ── STEP 4: Gemini LLM call ────────────────────────────────────────────
print()
print(SEP)
print("STEP 4 — Gemini LLM (simplify_sentence_with_llm)")
print(SEP)
try:
    from simplify import simplify_sentence_with_llm, MODEL_NAME
    print(f"Model: {MODEL_NAME}")
    test_sentence = "বিশ্বসাহিত্যের ইতিহাসে রবীন্দ্রনাথ ঠাকুরের সৃষ্টিকর্ম এক অনন্য স্থান অধিকার করেছে।"
    print(f"Input:  {test_sentence}")
    print("Calling Gemini... (may take a few seconds)")
    result = simplify_sentence_with_llm(test_sentence)
    print(f"Output: {result}")
    if result == test_sentence:
        print("⚠️   LLM returned the EXACT same sentence — check GEMINI_API_KEY in backend/.env")
    else:
        print("✅  LLM returned a different (simplified) sentence")
except Exception as e:
    print(f"❌  LLM call failed: {e}")
    import traceback; traceback.print_exc()

# ── STEP 5: Full pipeline end-to-end ──────────────────────────────────────
print()
print(SEP)
print("STEP 5 — Full simplify_text() pipeline")
print(SEP)
try:
    from bnlp import NLTKTokenizer
    from simplify import simplify_text
    tokenizer = NLTKTokenizer()
    result = simplify_text(HARD_TEXT, tokenizer, router)
    print(f"Input:   {HARD_TEXT}")
    print(f"Output:  {result['simplified_text']}")
    print(f"\nSentence breakdown:")
    for i, s in enumerate(result.get('sentence_breakdown', []), 1):
        print(f"  [{i}] label={s['label']!r} conf={s['confidence']:.3f}")
        print(f"       original:   {s['original']}")
        print(f"       simplified: {s['simplified']}")
    if result['simplified_text'] == HARD_TEXT:
        print("\n⚠️   Output == Input — sentences were all labeled Simple or LLM returned same text.")
    else:
        print("\n✅  Simplification changed the text")
except Exception as e:
    print(f"❌  Pipeline failed: {e}")
    import traceback; traceback.print_exc()

print()
print(SEP)
print("Diagnostics complete.")
print(SEP)
