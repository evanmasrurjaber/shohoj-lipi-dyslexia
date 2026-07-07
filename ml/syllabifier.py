"""
syllabifier.py — Bangla word syllabification using the BengaliReadability
pronunciation dictionary's syllable-COUNT data (not boundary data -- see note
below), combined with a vowel-based heuristic for actual boundary placement.

IMPORTANT DATA NOTE:
The available "pronunciation dictionary" files only give the number of
syllables per word (pronunciation_dict_words.txt + pronunciation_dict_words_length.txt,
aligned by line position, plus vocab_not_in_dict.txt/csv for out-of-vocabulary
words). There is no phonetic transcription or marked syllable-boundary data
in these files. So this module:
  1. Uses a vowel-based heuristic to guess WHERE syllable boundaries fall.
  2. Where the dictionary has a known correct COUNT for that word, uses it
     to validate the heuristic's guess and lightly correct over-segmentation
     (merging the shortest adjacent piece) when the counts don't match.
  3. For words with no dictionary entry, falls back to the heuristic alone.

This is disclosed as a limitation in the report: syllable placement is a
heuristic approximation validated against (not derived from) real dictionary
counts, not a true phonetic dictionary lookup.
"""

import csv
from pathlib import Path
from typing import Optional

SYLLABLE_MARK = "\u00B7"  # middot ( · ), used to mark syllable boundaries

# Bangla vowel signs (matras) + independent vowels -- used by the heuristic
_VOWEL_MATRAS = "\u09BE\u09BF\u09C0\u09C1\u09C2\u09C3\u09C7\u09C8\u09CB\u09CC"
_INDEPENDENT_VOWELS = "\u0985\u0986\u0987\u0988\u0989\u098A\u098B\u098F\u0990\u0993\u0994"

# word -> known-correct syllable count, loaded once at startup
SYLLABLE_COUNTS: dict = {}


def _load_word_count_pairs(words_path: Path, lengths_path: Path) -> dict:
    """Loads two line-aligned files (word list + parallel syllable-count list) into a dict."""
    if not words_path.exists() or not lengths_path.exists():
        return {}
    with open(words_path, encoding="utf-8") as wf, open(lengths_path, encoding="utf-8") as lf:
        words = [line.strip() for line in wf]
        lengths = [line.strip() for line in lf]
    pairs = {}
    for word, length_str in zip(words, lengths):
        if word and length_str.isdigit():
            pairs[word] = int(length_str)
    return pairs


def _load_oov_counts(path: Path) -> dict:
    """Loads the 'word,count' format vocab_not_in_dict file into a dict."""
    if not path.exists():
        return {}
    pairs = {}
    with open(path, encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) >= 2 and row[0].strip() and row[1].strip().isdigit():
                pairs[row[0].strip()] = int(row[1].strip())
    return pairs


def load_syllable_counts(base_dir: Optional[str] = None) -> dict:
    """
    Loads the syllable-count dictionary from the BengaliReadability
    pronunciation dictionary files. Adjust the folder path below if your
    files live somewhere else.
    """
    if base_dir is None:
        base_dir = Path(__file__).parent.parent / "data" / "BengaliReadability" / "pronunciation_dict"
    else:
        base_dir = Path(base_dir)

    counts = _load_word_count_pairs(
        base_dir / "pronunciation_dict_words.txt",
        base_dir / "pronunciation_dict_words_length.txt",
    )
    oov_counts = _load_oov_counts(base_dir / "vocab_not_in_dict.txt")
    if not oov_counts:
        oov_counts = _load_oov_counts(base_dir / "vocab_not_in_dict.csv")

    counts.update(oov_counts)  # OOV entries don't overlap with the main list, safe to merge

    if counts:
        print(f"[syllabifier] Loaded syllable counts for {len(counts)} words "
              f"({len(oov_counts)} from the out-of-vocabulary list)")
    else:
        print(f"[syllabifier] No syllable-count dictionary found at {base_dir} "
              f"-- using heuristic only, with no validation")
    return counts


def init_syllabifier(base_dir: Optional[str] = None) -> None:
    """Call once at startup."""
    global SYLLABLE_COUNTS
    SYLLABLE_COUNTS = load_syllable_counts(base_dir)


def _heuristic_split(word: str) -> list:
    """
    Rough heuristic: splits after each vowel (matra or independent vowel).
    Returns a list of syllable-piece strings (not yet joined with the marker).
    """
    pieces = []
    current = ""
    for ch in word:
        current += ch
        if ch in _VOWEL_MATRAS or ch in _INDEPENDENT_VOWELS:
            pieces.append(current)
            current = ""
    if current:
        pieces.append(current)
    return pieces if pieces else [word]


def _merge_down_to_count(pieces: list, target_count: int) -> list:
    """
    If the heuristic over-segmented (more pieces than the dictionary's known
    correct count), repeatedly merge the shortest adjacent pair until the
    piece count matches. If the heuristic under-segmented, we have no
    positional information to add a correct split, so pieces are returned
    unchanged (this word's split is a best-effort guess, not corrected).
    """
    while len(pieces) > target_count and len(pieces) > 1:
        # find the shortest adjacent pair to merge (least disruptive merge)
        merge_idx = min(
            range(len(pieces) - 1),
            key=lambda i: len(pieces[i]) + len(pieces[i + 1]),
        )
        pieces[merge_idx] = pieces[merge_idx] + pieces[merge_idx + 1]
        del pieces[merge_idx + 1]
    return pieces


def syllabify_word(word: str) -> str:
    """
    Splits a single word into syllable-marked pieces. Uses the dictionary's
    known syllable count to validate/correct the heuristic split when the
    word is found; otherwise returns the heuristic's best guess unchanged.
    """
    pieces = _heuristic_split(word)

    target_count = SYLLABLE_COUNTS.get(word)
    if target_count is not None and target_count >= 1:
        pieces = _merge_down_to_count(pieces, target_count)

    return SYLLABLE_MARK.join(pieces)


def syllabify_text(text: str) -> str:
    """
    Syllabifies every Bangla word in a passage, leaving punctuation and
    whitespace untouched, and returns the reassembled text.
    """
    tokens = text.split(" ")
    output = []
    for token in tokens:
        stripped = token.strip("।,.!?;:\"'")
        trailing = token[len(stripped):] if stripped else token
        if stripped:
            output.append(syllabify_word(stripped) + trailing)
        else:
            output.append(token)
    return " ".join(output)


def evaluate_heuristic_accuracy(sample_size: Optional[int] = None) -> dict:
    """
    Measures how often the vowel-based heuristic's raw (uncorrected) syllable
    count matches the dictionary's known-correct count -- a legitimate,
    disclosed accuracy number for the report, since we can't claim the
    heuristic is "validated" without actually checking it against something.
    """
    if not SYLLABLE_COUNTS:
        return {"error": "No syllable-count dictionary loaded -- call init_syllabifier() first"}

    items = list(SYLLABLE_COUNTS.items())
    if sample_size:
        items = items[:sample_size]

    correct = 0
    for word, true_count in items:
        guessed_count = len(_heuristic_split(word))
        if guessed_count == true_count:
            correct += 1

    accuracy = correct / len(items) if items else 0.0
    return {
        "n_words": len(items),
        "correct": correct,
        "accuracy": round(accuracy, 4),
    }


if __name__ == "__main__":
    init_syllabifier()
    result = evaluate_heuristic_accuracy()
    print(f"\nHeuristic syllable-count accuracy: {result}")

    test_words = ["বিদ্যালয়ে", "সুন্দর", "পাঁচালি", "রবীন্দ্রনাথ"]
    for w in test_words:
        print(f"{w} -> {syllabify_word(w)}")