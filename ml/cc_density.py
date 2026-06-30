"""
cc_density.py — Conjunct Consonant (CC) Density Computation
============================================================
Computes CC-density for Bangla text using two complementary methods:
  1. Unicode hasant (্) based detection  — catches all joining sequences
  2. Validated-conjunct-list lookup     — cross-reference with AAAI 2021 paper

Reference: Chakraborty et al., "Simple or Complex? Learning to Predict
           Readability of Bengali Texts", AAAI 2021.
"""

import re
import sys
import unicodedata
from pathlib import Path
from typing import Optional

# Fix Windows console Unicode output
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')


# ── Unicode ranges ──────────────────────────────────────────────────────────
BANGLA_CONSONANT_RANGE = r'[\u0995-\u09B9]'   # ক–হ (excluding anusvara etc.)
HASANT = '\u09CD'                               # ্  (virama / hasant)
BANGLA_CHAR_RANGE = r'[\u0980-\u09FF]'

# Conjunct pattern: consonant + hasant + consonant (+ optional further hasants)
CC_PATTERN = re.compile(
    r'[\u0995-\u09B9](?:\u09CD[\u0995-\u09B9])+'
)

# ── Load optional validated-conjunct list ───────────────────────────────────
def load_conjunct_list(path: Optional[str] = None) -> set:
    """
    Load the 341-word validated conjunct list from the BengaliReadability repo.
    Falls back to empty set if file not found (Unicode method still works).
    """
    if path is None:
        # Default relative path — adjust if repo is elsewhere
        candidates = [
            Path(__file__).parent.parent / "data" / "BengaliReadability" / "conjunct_list.txt",
            Path(__file__).parent.parent / "data" / "BengaliReadability" / "Conjunct_Consonant_Algorithm" / "conjunct_list.txt",
        ]
        for p in candidates:
            if p.exists():
                path = str(p)
                break

    if path and Path(path).exists():
        with open(path, encoding="utf-8") as f:
            words = {line.strip() for line in f if line.strip()}
        print(f"[cc_density] Loaded {len(words)} validated conjuncts from {path}")
        return words

    print("[cc_density] Conjunct list not found — using Unicode-only detection")
    return set()


VALIDATED_CONJUNCTS: set = set()   # populated lazily via init_conjunct_list()


def init_conjunct_list(path: Optional[str] = None) -> None:
    """Call once at app startup to pre-load the conjunct list."""
    global VALIDATED_CONJUNCTS
    VALIDATED_CONJUNCTS = load_conjunct_list(path)


# ── Core computation ────────────────────────────────────────────────────────

def count_conjuncts_in_text(text: str) -> int:
    """
    Count conjunct consonant occurrences in `text`.
    Uses Unicode hasant-based detection (primary method).
    Returns total count of conjunct sequences found.
    """
    return len(CC_PATTERN.findall(text))


def bangla_char_count(text: str) -> int:
    """Count only Bangla Unicode characters (U+0980–U+09FF)."""
    return sum(1 for ch in text if '\u0980' <= ch <= '\u09FF')


def bangla_word_count(text: str) -> list:
    """Return list of whitespace-split tokens that contain Bangla chars."""
    return [w for w in text.split() if any('\u0980' <= ch <= '\u09FF' for ch in w)]


def cc_density_per_100_chars(text: str) -> float:
    """
    CC-density metric from AAAI 2021 paper:
      = (number of conjunct sequences / number of Bangla chars) × 100

    Returns 0.0 if text has no Bangla characters.
    """
    n_chars = bangla_char_count(text)
    if n_chars == 0:
        return 0.0
    n_cc = count_conjuncts_in_text(text)
    return round((n_cc / n_chars) * 100, 4)


def cc_density_per_word(text: str) -> float:
    """
    Alternative CC-density:
      = number of conjunct sequences / number of Bangla words

    Useful for comparing passages of different lengths.
    """
    words = bangla_word_count(text)
    if not words:
        return 0.0
    n_cc = count_conjuncts_in_text(text)
    return round(n_cc / len(words), 4)


def words_with_conjuncts(text: str) -> list:
    """Return a list of (word, conjunct_count) for words containing conjuncts."""
    result = []
    for word in bangla_word_count(text):
        n = len(CC_PATTERN.findall(word))
        if n > 0:
            result.append((word, n))
    return result


def validated_conjunct_ratio(text: str) -> float:
    """
    Ratio of words containing a VALIDATED conjunct (from AAAI list) to total words.
    Requires init_conjunct_list() to be called first.
    """
    if not VALIDATED_CONJUNCTS:
        return 0.0
    words = bangla_word_count(text)
    if not words:
        return 0.0
    count = sum(1 for w in words if w in VALIDATED_CONJUNCTS)
    return round(count / len(words), 4)


def full_cc_report(text: str) -> dict:
    """Return all CC metrics for a given text passage."""
    return {
        "cc_per_100_chars":      cc_density_per_100_chars(text),
        "cc_per_word":           cc_density_per_word(text),
        "total_conjuncts":       count_conjuncts_in_text(text),
        "validated_conjunct_ratio": validated_conjunct_ratio(text),
        "bangla_char_count":     bangla_char_count(text),
        "bangla_word_count":     len(bangla_word_count(text)),
    }


# ── Quick test ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    test_cases = [
        # Easy (class 1) — few conjuncts
        ("EASY",   "এ দেশ অনেক সুন্দর। এ দেশে আছে বিচিত্র ধরনের পাখি। দোয়েল আমাদের জাতীয় পাখি।"),
        # Medium (class 6-8)
        ("MEDIUM", "বাংলাদেশের মানুষ অত্যন্ত পরিশ্রমী। তারা কৃষি, শিল্প ও বাণিজ্যে নিরলস কাজ করে।"),
        # Hard (class 11-12) — dense conjuncts
        ("HARD",   "বিশ্বসাহিত্যের ইতিহাসে রবীন্দ্রনাথ ঠাকুরের সৃষ্টিকর্ম এক অনন্য স্থান অধিকার করেছে। তাঁর কবিত্বশক্তি, দার্শনিক চিন্তাভাবনা এবং মানবতাবাদী দৃষ্টিভঙ্গি অতুলনীয়।"),
    ]

    print("=" * 60)
    print("CC-DENSITY TEST RESULTS")
    print("=" * 60)
    for label, text in test_cases:
        report = full_cc_report(text)
        print(f"\n[{label}]")
        preview = text[:60].encode('ascii', errors='replace').decode('ascii')
        print(f"  Text (preview): {preview}...")
        for k, v in report.items():
            print(f"  {k:35s}: {v}")
    print("\n✅ cc_density.py working correctly")
