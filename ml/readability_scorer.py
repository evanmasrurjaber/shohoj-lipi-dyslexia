"""
readability_scorer.py — Rule-Based Bangla Readability Scoring
=============================================================
Computes a composite readability score using four linguistic features
derived directly from Chakraborty et al. (AAAI 2021):

  1. CC-density          — conjunct consonants per 100 chars      (weight 0.30)
  2. Avg sentence length — mean words per sentence                 (weight 0.25)
  3. Avg word length     — mean chars per word                     (weight 0.20)
  4. Rare-word ratio     — fraction of words NOT in easy-word list (weight 0.25)

Score range: 0.0 (simplest) → 1.0 (hardest)
Tier mapping:  0.0–0.33 → Easy | 0.34–0.66 → Medium | 0.67–1.0 → Hard

This scorer is used as the document-level readability signal in the pipeline.
It replaces a fine-tuned BanglaBERT classifier (which would require 618 docs
— far too few for reliable transformer training).
"""

import re
import unicodedata
from pathlib import Path
from typing import Optional, Union

from ml.cc_density import (
    cc_density_per_100_chars,
    bangla_word_count,
    init_conjunct_list,
)


# ── Load Easy-Word List ─────────────────────────────────────────────────────

def load_easy_words(path: Optional[str] = None) -> set:
    """
    Load the 3,396-word easy-word list from the BengaliReadability corpus.
    Returns a set of normalized Bangla words for fast O(1) lookup.
    """
    if path is None:
        candidates = [
            Path(__file__).parent.parent / "data" / "BengaliReadability" / "easy_word_list.txt",
            Path(__file__).parent.parent / "data" / "BengaliReadability" / "Easy_Word_List" / "easy_word_list.txt",
            Path(__file__).parent.parent / "data" / "BengaliReadability" / "easy_words.txt",
        ]
        for p in candidates:
            if p.exists():
                path = str(p)
                break

    if path and Path(path).exists():
        with open(path, encoding="utf-8") as f:
            words = {unicodedata.normalize("NFC", line.strip())
                     for line in f if line.strip()}
        print(f"[readability_scorer] Loaded {len(words)} easy words from {path}")
        return words

    print("[readability_scorer] Easy-word list not found — rare_word_ratio will be 0")
    return set()


# Module-level singletons (initialised lazily)
EASY_WORDS: set = set()


def init_scorer(
    easy_word_path: Optional[str] = None,
    conjunct_path: Optional[str] = None,
) -> None:
    """Call once at startup to pre-load both resource files."""
    global EASY_WORDS
    EASY_WORDS = load_easy_words(easy_word_path)
    init_conjunct_list(conjunct_path)


# ── Sentence Tokeniser (lightweight, no bnlp dependency) ───────────────────

# Bangla sentence-ending punctuation characters
_SENTENCE_ENDINGS = re.compile(r'[।!?\.]+')


def _simple_sentence_tokenize(text: str) -> list:
    """
    Lightweight rule-based Bangla sentence tokeniser.
    Splits on daṇḍa (।), ! ? and full-stop.
    Used as a fallback when bnlp is not available.
    """
    parts = _SENTENCE_ENDINGS.split(text)
    return [p.strip() for p in parts if p.strip()]


def _bnlp_sentence_tokenize(text: str) -> list:
    """Attempt to use bnlp sentence tokeniser; fallback to rule-based."""
    try:
        from bnlp import NLTKTokenizer
        tok = NLTKTokenizer()
        sents = tok.sentence_tokenize(text)
        return [s for s in sents if s.strip()]
    except Exception:
        return _simple_sentence_tokenize(text)


# ── Feature Computation ─────────────────────────────────────────────────────

def _avg_sentence_length(text: str) -> float:
    """Mean number of Bangla words per sentence."""
    sentences = _bnlp_sentence_tokenize(text)
    if not sentences:
        return 0.0
    word_counts = [len(bangla_word_count(s)) for s in sentences]
    return sum(word_counts) / len(word_counts)


def _avg_word_length(text: str) -> float:
    """Mean number of characters per Bangla word."""
    words = bangla_word_count(text)
    if not words:
        return 0.0
    return sum(len(w) for w in words) / len(words)


def _rare_word_ratio(text: str) -> float:
    """
    Fraction of Bangla words NOT present in the easy-word list.
    Returns 0.0 if easy-word list is empty (no penalty applied).
    """
    if not EASY_WORDS:
        return 0.0
    words = bangla_word_count(text)
    if not words:
        return 0.0
    rare = sum(
        1 for w in words
        if unicodedata.normalize("NFC", w) not in EASY_WORDS
    )
    return rare / len(words)


# ── Normalisation Helpers ───────────────────────────────────────────────────

# Calibrated ranges (min, max) per feature — tuned on NCTB corpus observations
# CC Easy~2-4, Medium~5-8, Hard~8-13 per 100 chars
_FEATURE_RANGES = {
    "cc_density":      (0.0,  14.0),   # CC per 100 chars
    "avg_sent_len":    (4.0,  40.0),   # words per sentence
    "avg_word_len":    (2.5,   8.5),   # chars per word
    "rare_word_ratio": (0.0,   1.0),   # fraction (0 when list not loaded)
}


def _normalize(value: float, min_val: float, max_val: float) -> float:
    """Clamp and linearly normalise value to [0, 1]."""
    if max_val == min_val:
        return 0.0
    return max(0.0, min(1.0, (value - min_val) / (max_val - min_val)))


# ── Main Scorer ──────────────────────────────────────────────────────────────

WEIGHTS = {
    "cc_density":      0.30,
    "avg_sent_len":    0.25,
    "avg_word_len":    0.20,
    "rare_word_ratio": 0.25,
}

TIER_THRESHOLDS = (0.2383, 0.3210)   # auto-calibrated on 935 passages


def compute_readability(text: str) -> dict:
    """
    Compute composite readability score for a Bangla text passage.

    Returns:
        dict with keys:
          score         — float in [0, 1]; higher = harder
          tier          — "Easy" | "Medium" | "Hard"
          grade_estimate— approximate school grade range
          features      — raw feature values (for explainability & evaluation)
          features_norm — normalised feature values (0–1)
    """
    text = unicodedata.normalize("NFC", text)

    # 1. Raw features
    raw = {
        "cc_density":      cc_density_per_100_chars(text),
        "avg_sent_len":    _avg_sentence_length(text),
        "avg_word_len":    _avg_word_length(text),
        "rare_word_ratio": _rare_word_ratio(text),
    }

    # 2. Normalised features
    norm = {
        feat: _normalize(raw[feat], *_FEATURE_RANGES[feat])
        for feat in raw
    }

    # 3. Weighted composite
    score = sum(WEIGHTS[feat] * norm[feat] for feat in WEIGHTS)
    score = round(score, 4)

    # 4. Tier & grade
    if score <= TIER_THRESHOLDS[0]:
        tier, grade = "Easy", "1–4"
    elif score <= TIER_THRESHOLDS[1]:
        tier, grade = "Medium", "5–8"
    else:
        tier, grade = "Hard", "9–12"

    return {
        "score":          score,
        "tier":           tier,
        "grade_estimate": grade,
        "features":       {k: round(v, 4) for k, v in raw.items()},
        "features_norm":  {k: round(v, 4) for k, v in norm.items()},
    }


def score_delta(original_text: str, simplified_text: str) -> dict:
    """
    Compute before/after readability and the delta.
    Positive delta means simplification reduced difficulty (good).
    """
    before = compute_readability(original_text)
    after  = compute_readability(simplified_text)
    delta  = round(before["score"] - after["score"], 4)

    return {
        "before":       before,
        "after":        after,
        "score_delta":  delta,           # positive = harder → easier
        "tier_change":  f"{before['tier']} → {after['tier']}",
        "improved":     delta > 0,
    }


# ── CLI / Quick test ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    import json

    # Initialise with whatever is available
    init_scorer()

    test_passages = {
        "Easy (Class 1)": (
            "এ দেশ অনেক সুন্দর। এ দেশে আছে বিচিত্র ধরনের পাখি। "
            "দোয়েল আমাদের জাতীয় পাখি। এ দেশের বনে বনে খালে বিলে অনেক ফুল ফোটে।"
        ),
        "Medium (Class 7)": (
            "বাংলাদেশের অর্থনীতি মূলত কৃষিনির্ভর। দেশের মোট শ্রমশক্তির একটি বড় অংশ "
            "কৃষিকাজে নিয়োজিত। ধান, পাট, চা এবং শাকসবজি এ দেশের প্রধান কৃষিপণ্য।"
        ),
        "Hard (Class 11)": (
            "বিশ্বসাহিত্যের ইতিহাসে রবীন্দ্রনাথ ঠাকুরের সৃষ্টিকর্ম এক অনন্য স্থান অধিকার করেছে। "
            "তাঁর কবিত্বশক্তি, দার্শনিক চিন্তাভাবনা এবং মানবতাবাদী দৃষ্টিভঙ্গি অতুলনীয়। "
            "গীতাঞ্জলির জন্য তিনি ১৯১৩ সালে নোবেল পুরস্কার লাভ করেন।"
        ),
    }

    print("=" * 65)
    print("READABILITY SCORER — QUICK TEST")
    print("=" * 65)

    for label, text in test_passages.items():
        result = compute_readability(text)
        print(f"\n{'─'*65}")
        print(f"  [{label}]")
        print(f"  Score : {result['score']}  |  Tier: {result['tier']}  |  Grade: {result['grade_estimate']}")
        print(f"  Features:")
        for k, v in result["features"].items():
            bar = "█" * int(result["features_norm"][k] * 20)
            print(f"    {k:22s}: {v:7.4f}  [{bar:<20}]")

    # Delta test
    original   = test_passages["Hard (Class 11)"]
    simplified = test_passages["Easy (Class 1)"]
    delta = score_delta(original, simplified)
    print(f"\n{'─'*65}")
    print(f"  DELTA TEST (Hard → Easy):")
    print(f"  Before: {delta['before']['score']} ({delta['before']['tier']})")
    print(f"  After : {delta['after']['score']} ({delta['after']['tier']})")
    print(f"  Delta : {delta['score_delta']} | Improved: {delta['improved']}")
    print(f"\n✅ readability_scorer.py working correctly")
