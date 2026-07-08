import pandas as pd
import re
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

VOWEL_MATRAS = "অআইঈউঊঋএঐওঔািীুূৃেৈোৌ"

def count_syllables(word: str) -> int:
    # Approximate: count vowel signs + independent vowels; minimum 1 per word
    count = sum(1 for ch in word if ch in VOWEL_MATRAS)
    return max(count, 1)

def sentence_split(text: str):
    # Simple Bangla sentence splitter on দাঁড়ি (।) and standard punctuation
    sentences = re.split(r'[।!?]', str(text))
    return [s.strip() for s in sentences if s.strip()]

def readability_stats(text: str):
    sentences = sentence_split(text)
    words = str(text).split()
    n_sentences = max(len(sentences), 1)
    n_words = max(len(words), 1)
    total_syllables = sum(count_syllables(w) for w in words)

    avg_sentence_len = n_words / n_sentences
    avg_syllables_per_word = total_syllables / n_words

    # Flesch-Kincaid-style formula (lower = easier). Same functional form as
    # the English FK Grade Level, adapted for Bangla syllable counting.
    fk_grade = 0.39 * avg_sentence_len + 11.8 * avg_syllables_per_word - 15.59
    return avg_sentence_len, avg_syllables_per_word, fk_grade

df = pd.read_csv(os.path.join(BASE_DIR, "eval_results_full.csv"), encoding="utf-8-sig")

before_stats = df["original_text"].apply(readability_stats)
after_stats = df["simplified_text"].apply(readability_stats)

df["avg_sent_len_before"], df["avg_syll_word_before"], df["fk_grade_before"] = zip(*before_stats)
df["avg_sent_len_after"], df["avg_syll_word_after"], df["fk_grade_after"] = zip(*after_stats)
df["fk_grade_drop"] = df["fk_grade_before"] - df["fk_grade_after"]

print("--- Bangla Flesch-Kincaid-style Formula ---")
print(f"N = {len(df)}")
print(f"Avg sentence length  BEFORE: {df['avg_sent_len_before'].mean():.2f} words  AFTER: {df['avg_sent_len_after'].mean():.2f} words")
print(f"Avg syllables/word   BEFORE: {df['avg_syll_word_before'].mean():.2f}       AFTER: {df['avg_syll_word_after'].mean():.2f}")
print(f"FK-style grade level BEFORE: {df['fk_grade_before'].mean():.2f}           AFTER: {df['fk_grade_after'].mean():.2f}")
print(f"Average FK grade drop:      {df['fk_grade_drop'].mean():.2f}")

df.to_csv(os.path.join(BASE_DIR, "eval_results_full.csv"), index=False, encoding="utf-8-sig")