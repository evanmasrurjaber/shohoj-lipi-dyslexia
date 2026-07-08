import pandas as pd
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Load easy-word list — one word per line
with open(os.path.join(BASE_DIR, "BengaliReadability/easy_word_list.txt"), encoding="utf-8") as f:
    easy_words = set(line.strip() for line in f if line.strip())

def vocab_simplicity_pct(text: str) -> float:
    words = str(text).split()
    if not words:
        return 0.0
    easy_count = sum(1 for w in words if w in easy_words)
    return round((easy_count / len(words)) * 100, 2)

df = pd.read_csv(os.path.join(BASE_DIR, "eval_results_with_cc.csv"), encoding="utf-8-sig")

df["vocab_simplicity_before"] = df["original_text"].apply(vocab_simplicity_pct)
df["vocab_simplicity_after"] = df["simplified_text"].apply(vocab_simplicity_pct)
df["vocab_simplicity_gain"] = df["vocab_simplicity_after"] - df["vocab_simplicity_before"]

print("--- Vocabulary Simplicity % (words in easy-word list) ---")
print(f"N = {len(df)}")
print(f"Average BEFORE: {df['vocab_simplicity_before'].mean():.2f}%")
print(f"Average AFTER:  {df['vocab_simplicity_after'].mean():.2f}%")
print(f"Average gain:   {df['vocab_simplicity_gain'].mean():.2f} percentage points")

df.to_csv(os.path.join(BASE_DIR, "eval_results_full.csv"), index=False, encoding="utf-8-sig")
print("\nSaved to eval_results_full.csv")