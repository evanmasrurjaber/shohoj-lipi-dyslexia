import csv
import os

# This makes the script always look for files relative to its own location,
# no matter what folder you're sitting in when you run it.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# === CONFIGURE THIS for each file you run ===
input_file = os.path.join(BASE_DIR, "raw", "nctb_by_class", "class 11+12", "Bengali_literature.txt")
source_label = "NCTB-Class11-12"
intended_difficulty = "hard"
min_length = 100
output_file = os.path.join(BASE_DIR, "passages_review.csv")
# ==============================================

with open(input_file, "r", encoding="utf-8") as f:
    lines = [line.strip() for line in f if line.strip()]  # remove blank lines

kept = [line for line in lines if len(line) >= min_length]
discarded = [line for line in lines if len(line) < min_length]

file_exists = os.path.isfile(output_file)
with open(output_file, "a", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    if not file_exists:
        writer.writerow(["id", "text", "source", "intended_difficulty"])
    start_id = sum(1 for _ in open(output_file, encoding="utf-8")) if file_exists else 1
    for i, text in enumerate(kept, start=start_id):
        writer.writerow([i, text, source_label, intended_difficulty])

print(f"Kept {len(kept)} passages, discarded {len(discarded)} short lines (likely rhymes).")
print(f"Appended to {output_file} — go review it before treating it as final.")