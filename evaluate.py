import pandas as pd
import json
import os
import time
import sys
from tqdm import tqdm
from bert_score import score as bert_score_func

sys.path.insert(0, '.')
from ml.readability_scorer import compute_readability, init_scorer
from backend.main import route_and_simplify

print("Initializing scorers and models...")
init_scorer()
# models already loaded in backend.main

df = pd.read_csv("data/eval_passages.csv")
# Sample 100 passages, prioritize medium and hard to see simplification
df_hard = df[df["intended_difficulty"].isin(["hard", "medium"])].sample(n=80, random_state=42)
df_easy = df[df["intended_difficulty"] == "easy"].sample(n=20, random_state=42)
df_eval = pd.concat([df_hard, df_easy]).reset_index(drop=True)

results = []

print(f"Starting evaluation on {len(df_eval)} passages...")
for idx, row in tqdm(df_eval.iterrows(), total=len(df_eval)):
    original_text = row["text"]
    
    # Pre-score
    before = compute_readability(original_text)
    
    # Process
    try:
        res = route_and_simplify(original_text)
        simplified_text = res["final_text"]
        
        # Post-score
        after = compute_readability(simplified_text)
        
        results.append({
            "id": row["id"],
            "intended": row["intended_difficulty"],
            "original": original_text,
            "simplified": simplified_text,
            "score_before": before["score"],
            "score_after": after["score"],
            "cc_before": before["features"]["cc_density"],
            "cc_after": after["features"]["cc_density"],
            "num_complex_sentences": sum(1 for p in res["processed"] if p["was_complex"])
        })
    except Exception as e:
        print(f"Failed on index {idx}: {e}")
        continue
    
    # Short delay to avoid rate limits
    time.sleep(1)

res_df = pd.DataFrame(results)

# Calculate metrics
print("\nCalculating BERTScore...")
# We only calculate BERTScore for texts that were actually simplified (where original != simplified)
changed_df = res_df[res_df["original"] != res_df["simplified"]]

if len(changed_df) > 0:
    P, R, F1 = bert_score_func(
        changed_df["simplified"].tolist(), 
        changed_df["original"].tolist(), 
        lang="bn", 
        verbose=True
    )
    bert_f1_mean = F1.mean().item()
else:
    bert_f1_mean = 1.0

res_df["score_delta"] = res_df["score_before"] - res_df["score_after"]
res_df["cc_delta"] = res_df["cc_before"] - res_df["cc_after"]

res_df.to_csv("data/evaluation_results.csv", index=False)

print("=========================================")
print("           EVALUATION RESULTS            ")
print("=========================================")
print(f"Total Passages Evaluated: {len(res_df)}")
print(f"Passages Simplified (complex detected): {len(changed_df)}")
print(f"Mean Readability Score Drop (on simplified): {res_df[res_df['num_complex_sentences'] > 0]['score_delta'].mean():.4f}")
print(f"Mean CC-Density Drop (on simplified): {res_df[res_df['num_complex_sentences'] > 0]['cc_delta'].mean():.2f}")
print(f"BERTScore F1 (Semantic Fidelity): {bert_f1_mean:.4f} (Target: >0.82)")
print("=========================================")
print("Results saved to data/evaluation_results.csv")
