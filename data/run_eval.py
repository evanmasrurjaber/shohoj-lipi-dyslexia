import pandas as pd
import requests
import os
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
input_path = os.path.join(BASE_DIR, "eval_passages.csv")
output_path = os.path.join(BASE_DIR, "eval_results.csv")

df = pd.read_csv(input_path, encoding="utf-8-sig")
print(f"Found {len(df)} total passages to evaluate.")

# --- RESUME LOGIC: if eval_results.csv already exists, skip IDs already done ---
done_ids = set()
if os.path.exists(output_path):
    existing = pd.read_csv(output_path, encoding="utf-8-sig")
    done_ids = set(existing["id"].tolist())
    print(f"Resuming — {len(done_ids)} passages already processed, skipping those.")

remaining_df = df[~df["id"].isin(done_ids)].copy()
print(f"{len(remaining_df)} passages left to process.")

MAX_RETRIES = 4
BASE_DELAY = 2  # seconds between calls under normal conditions

def process_passage(text, timeout=60):
    """Call /process with retry + exponential backoff on failure."""
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.post(
                "http://127.0.0.1:8001/process",
                json={"text": text},
                timeout=timeout
            )
            if response.status_code == 200:
                return response.json(), None
            elif response.status_code == 429:
                wait = BASE_DELAY * (2 ** attempt)
                print(f"    Rate limited (429) — waiting {wait}s before retry {attempt+1}/{MAX_RETRIES}")
                time.sleep(wait)
                continue
            else:
                return None, f"HTTP {response.status_code}: {response.text[:100]}"
        except requests.exceptions.Timeout:
            wait = BASE_DELAY * (2 ** attempt)
            print(f"    Timeout — waiting {wait}s before retry {attempt+1}/{MAX_RETRIES}")
            time.sleep(wait)
    return None, "FAILED_AFTER_RETRIES"

# Write header if file doesn't exist yet
if not os.path.exists(output_path):
    pd.DataFrame(columns=[
        "id", "source", "intended_difficulty", "original_text",
        "simplified_text", "before_score", "before_tier",
        "after_score", "after_tier"
    ]).to_csv(output_path, index=False, encoding="utf-8-sig")

for i, row in remaining_df.iterrows():
    print(f"Processing passage {row['id']} ({i+1}/{len(df)})...")
    data, error = process_passage(row["text"])

    if data is not None:
        result_row = {
            "id": row["id"],
            "source": row["source"],
            "intended_difficulty": row["intended_difficulty"],
            "original_text": row["text"],
            "simplified_text": data.get("simplified_text", ""),
            "before_score": data.get("before_score", ""),
            "before_tier": data.get("before_tier", ""),
            "after_score": data.get("after_score", ""),
            "after_tier": data.get("after_tier", ""),
        }
        print(f"  ✓ Before: {data.get('before_tier')} ({data.get('before_score')}) → After: {data.get('after_tier')} ({data.get('after_score')})")
    else:
        result_row = {
            "id": row["id"],
            "source": row["source"],
            "intended_difficulty": row["intended_difficulty"],
            "original_text": row["text"],
            "simplified_text": error,
            "before_score": "", "before_tier": "",
            "after_score": "", "after_tier": "",
        }
        print(f"  ✗ {error}")

    # Append this single row immediately — never lose progress on crash
    pd.DataFrame([result_row]).to_csv(output_path, mode="a", header=False, index=False, encoding="utf-8-sig")

    time.sleep(BASE_DELAY)  # pace calls to respect free-tier RPM limits

print("\nDone processing all remaining passages.")

# Quick summary
final_df = pd.read_csv(output_path, encoding="utf-8-sig")
successful = final_df[pd.to_numeric(final_df["before_score"], errors="coerce").notna()]
if len(successful) > 0:
    avg_before = pd.to_numeric(successful["before_score"]).mean()
    avg_after = pd.to_numeric(successful["after_score"]).mean()
    print(f"\n--- Quick Summary ---")
    print(f"Successful: {len(successful)} / {len(final_df)}")
    print(f"Average before score: {avg_before:.2f}")
    print(f"Average after score:  {avg_after:.2f}")
    print(f"Average score drop:   {avg_before - avg_after:.2f}")