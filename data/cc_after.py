import pandas as pd
import re
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def compute_cc_density(text: str) -> float:
    conjunct_pattern = re.compile(r'[\u0995-\u09B9]\u09CD[\u0995-\u09B9]')
    matches = conjunct_pattern.findall(str(text))
    char_count = max(len(str(text)), 1)
    return round((len(matches) / char_count) * 100, 2)

df = pd.read_csv(os.path.join(BASE_DIR, "eval_results.csv"), encoding="utf-8-sig")

df_valid = df[df["simplified_text"].notna() & ~df["simplified_text"].str.contains(
    "FAILED|TIMEOUT|ERROR|HTTP", na=False)].copy()

df_valid["cc_density_before"] = df_valid["original_text"].apply(compute_cc_density)
df_valid["cc_density_after"] = df_valid["simplified_text"].apply(compute_cc_density)
df_valid["cc_density_reduction"] = df_valid["cc_density_before"] - df_valid["cc_density_after"]

print("--- CC-Density Before vs After Simplification (full corpus) ---")
print(f"N = {len(df_valid)}")
print(f"Average CC-density BEFORE: {df_valid['cc_density_before'].mean():.2f}")
print(f"Average CC-density AFTER:  {df_valid['cc_density_after'].mean():.2f}")
print(f"Average reduction:         {df_valid['cc_density_reduction'].mean():.2f}")

df_valid.to_csv(os.path.join(BASE_DIR, "eval_results_with_cc.csv"), index=False, encoding="utf-8-sig")
print("\nSaved to eval_results_with_cc.csv")