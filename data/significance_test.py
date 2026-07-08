import pandas as pd
from scipy import stats
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
df = pd.read_csv(os.path.join(BASE_DIR, "eval_results_full.csv"), encoding="utf-8-sig")

before = pd.to_numeric(df["before_score"], errors="coerce")
after = pd.to_numeric(df["after_score"], errors="coerce")
valid = before.notna() & after.notna()

before_v = before[valid]
after_v = after[valid]

# Paired Wilcoxon signed-rank test — is the before/after difference statistically significant?
stat, p_value = stats.wilcoxon(before_v, after_v)
print("--- Wilcoxon Signed-Rank Test (Readability Score, Before vs After) ---")
print(f"N = {len(before_v)}")
print(f"Statistic = {stat:.2f}, p-value = {p_value:.6f}")
print("Significant at p < 0.05" if p_value < 0.05 else "NOT significant at p < 0.05")

# Correlation: does CC-density reduction track with BanglaBERT score drop?
score_drop = before_v - after_v
cc_reduction = df.loc[valid, "cc_density_reduction"]

pearson_r, pearson_p = stats.pearsonr(score_drop, cc_reduction)
spearman_r, spearman_p = stats.spearmanr(score_drop, cc_reduction)

print("\n--- Cross-Metric Correlation (Score Drop vs CC-Density Reduction) ---")
print(f"Pearson r  = {pearson_r:.3f} (p = {pearson_p:.4f})")
print(f"Spearman r = {spearman_r:.3f} (p = {spearman_p:.4f})")
