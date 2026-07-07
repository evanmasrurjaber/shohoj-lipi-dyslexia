"""
syllabifier.py — Bangla word syllabification using the BengaliReadability
pronunciation dictionary, with a fallback heuristic for unknown words.
"""

from pathlib import Path
from typing import Optional

SYLLABLE_MARK = "\u00B7"  # middot ( · ), used to mark syllable boundaries

# Bangla vowel signs (matras) + independent vowels -- used only by the fallback
_VOWEL_MATRAS = "\u09BE\u09BF\u09C0\u09C1\u09C2\u09C3\u09C7\u09C8\u09CB\u09CC"
_INDEPENDENT_VOWELS = "\u0985\u0986\u0987\u0988\u0989\u098A\u098B\u098F\u0990\u0993\u0994"

PRONUNCIATION_DICT: dict = {}


def load_pronunciation_dict(path: Optional[str] = None) -> dict:
    """
    Loads word -> syllable-marked pronunciation from the BengaliReadability
    pronunciation dictionary file. Adjust the split character below to match
    the actual file format once confirmed.
    """
    if path is None:
        candidates = [
            Path(__file__).parent.parent / "data" / "BengaliReadability" / "Other resources" / "Pronounciation Dictionary" / "pronunciation_dict_words.txt",
            Path(__file__).parent.parent / "data" / "BengaliReadability" / "Other resources" / "Pronounciation Dictionary" / "pronunciation_dict_words.txt",
        ]
        for p in candidates:
            if p.exists():
                path = str(p)
                break

    result = {}
    if path and Path(path).exists():
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or "\t" not in line:
                    continue
                word, pronunciation = line.split("\t", 1)
                # Assumes syllables in the source file are hyphen-separated --
                # change "-" below if the real file uses a different character.
                syllabified = pronunciation.replace("-", SYLLABLE_MARK)
                result[word.strip()] = syllabified
        print(f"[syllabifier] Loaded {len(result)} words from {path}")
    else:
        print("[syllabifier] Pronunciation dictionary not found — using fallback heuristic only")
    return result


def init_syllabifier(path: Optional[str] = None) -> None:
    """Call once at startup."""
    global PRONUNCIATION_DICT
    PRONUNCIATION_DICT = load_pronunciation_dict(path)


def _fallback_syllabify(word: str) -> str:
    """
    Rough heuristic for words not in the dictionary: insert a syllable
    marker after each vowel (matra or independent vowel). Not linguistically
    perfect, but gives dyslexia-friendly visual chunking rather than nothing.
    """
    out = []
    for ch in word:
        out.append(ch)
        if ch in _VOWEL_MATRAS or ch in _INDEPENDENT_VOWELS:
            out.append(SYLLABLE_MARK)
    result = "".join(out).strip(SYLLABLE_MARK)
    return result


def syllabify_word(word: str) -> str:
    """Look up a single word; fall back to the heuristic if not found."""
    if word in PRONUNCIATION_DICT:
        return PRONUNCIATION_DICT[word]
    return _fallback_syllabify(word)


def syllabify_text(text: str) -> str:
    """
    Syllabifies every Bangla word in a passage, leaving punctuation and
    whitespace untouched, and returns the reassembled text.
    """
    tokens = text.split(" ")
    output = []
    for token in tokens:
        # Strip trailing punctuation so lookup works, then reattach it
        stripped = token.strip("।,.!?;:\"'")
        trailing = token[len(stripped):] if stripped else token
        if stripped:
            output.append(syllabify_word(stripped) + trailing)
        else:
            output.append(token)
    return " ".join(output)