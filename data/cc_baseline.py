import pandas as pd
import re
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def compute_cc_density(text: str) -> float:
    conjunct_pattern = re.compile(r'[\u0995-\u09B9]\u09CD[\u0995-\u09B9]')
    matches = conjunct_pattern.findall(text)
    cc_count = len(matches)
    char_count = max(len(text), 1)
    return round((cc_count / char_count) * 100, 2)

input_path = os.path.join(BASE_DIR, "eval_passages.csv")
df = pd.read_csv(input_path, encoding="utf-8-sig")

df["cc_count"] = df["text"].apply(lambda t: len(re.findall(r'[\u0995-\u09B9]\u09CD[\u0995-\u09B9]', str(t))))
df["cc_density_per_100_chars"] = df["text"].apply(compute_cc_density)

output_path = os.path.join(BASE_DIR, "cc_baseline_results.csv")
df.to_csv(output_path, index=False, encoding="utf-8-sig")

print(df[["id", "intended_difficulty", "cc_count", "cc_density_per_100_chars"]].head(10))
print(f"\nSaved full results to {output_path}")

print("\n--- Average CC-density by intended difficulty ---")
print(df.groupby("intended_difficulty")["cc_density_per_100_chars"].mean())