"""
calibrate_scorer.py — Auto-Calibrate Readability Scorer Thresholds
===================================================================
Reads the validation CSV, computes optimal tier thresholds from the
actual score distribution, and updates readability_scorer.py.

Run ONCE after running validate_scorer.py for the first time.

Usage:
    python -m ml.calibrate_scorer
"""

import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from ml.readability_scorer import compute_readability, init_scorer

PROJECT_ROOT = Path(__file__).parent.parent


def calibrate():
    # Load eval passages
    passages_path = PROJECT_ROOT / "data" / "eval_passages.csv"
    with open(passages_path, encoding="utf-8") as f:
        passages = list(csv.DictReader(f))

    init_scorer()

    # Compute score for every passage, group by true tier
    from collections import defaultdict
    scores_by_tier = defaultdict(list)

    print(f"Computing scores for {len(passages)} passages...")
    for p in passages:
        result = compute_readability(p["text"])
        tier = p["intended_difficulty"].strip().capitalize()
        scores_by_tier[tier].append(result["score"])

    # Print distribution stats
    print("\nScore distribution per tier:")
    for tier in ["Easy", "Medium", "Hard"]:
        vals = scores_by_tier[tier]
        if not vals:
            continue
        vals.sort()
        p25 = vals[len(vals)//4]
        p50 = vals[len(vals)//2]
        p75 = vals[3*len(vals)//4]
        print(f"  {tier:8s}: min={min(vals):.3f}  p25={p25:.3f}  "
              f"median={p50:.3f}  p75={p75:.3f}  max={max(vals):.3f}  n={len(vals)}")

    # Find optimal thresholds using percentile-based approach:
    # Easy|Medium threshold = 75th percentile of Easy scores
    # Medium|Hard threshold = 25th percentile of Hard scores
    easy_scores  = sorted(scores_by_tier.get("Easy", [0.1]))
    medium_scores = sorted(scores_by_tier.get("Medium", [0.3]))
    hard_scores  = sorted(scores_by_tier.get("Hard", [0.5]))

    thresh_easy_medium = easy_scores[int(0.75 * len(easy_scores))]
    thresh_medium_hard = hard_scores[int(0.25 * len(hard_scores))]

    # Ensure thresholds are monotonically increasing
    if thresh_easy_medium >= thresh_medium_hard:
        # Fallback: use mean of medians
        thresh_easy_medium = easy_scores[len(easy_scores)//2]
        thresh_medium_hard = hard_scores[len(hard_scores)//2]

    print(f"\nCalibrated thresholds:")
    print(f"  Easy|Medium : {thresh_easy_medium:.4f}")
    print(f"  Medium|Hard : {thresh_medium_hard:.4f}")

    # Quick accuracy check with new thresholds
    correct = 0
    for p in passages:
        result  = compute_readability(p["text"])
        score   = result["score"]
        true_t  = p["intended_difficulty"].strip().capitalize()
        if score <= thresh_easy_medium:
            pred_t = "Easy"
        elif score <= thresh_medium_hard:
            pred_t = "Medium"
        else:
            pred_t = "Hard"
        if pred_t == true_t:
            correct += 1

    accuracy = correct / len(passages)
    print(f"\nAccuracy with calibrated thresholds: {correct}/{len(passages)} = {accuracy:.1%}")

    # Update readability_scorer.py with new thresholds
    scorer_path = PROJECT_ROOT / "ml" / "readability_scorer.py"
    content = scorer_path.read_text(encoding="utf-8")

    # Replace the TIER_THRESHOLDS line
    import re
    new_thresh_line = (
        f"TIER_THRESHOLDS = ({thresh_easy_medium:.4f}, {thresh_medium_hard:.4f})"
        f"   # auto-calibrated on {len(passages)} passages"
    )
    content = re.sub(
        r"TIER_THRESHOLDS = \([^)]+\).*",
        new_thresh_line,
        content,
    )
    scorer_path.write_text(content, encoding="utf-8")
    print(f"\n✅ Updated TIER_THRESHOLDS in ml/readability_scorer.py")
    print(f"   New: TIER_THRESHOLDS = ({thresh_easy_medium:.4f}, {thresh_medium_hard:.4f})")

    # Save calibration results
    docs_dir = PROJECT_ROOT / "docs"
    docs_dir.mkdir(exist_ok=True)
    calibration_data = {
        "easy_medium_threshold": thresh_easy_medium,
        "medium_hard_threshold": thresh_medium_hard,
        "calibration_accuracy":  round(accuracy, 4),
        "n_passages":            len(passages),
        "score_stats": {
            tier: {
                "min":    round(min(vals), 4),
                "median": round(vals[len(vals)//2], 4),
                "max":    round(max(vals), 4),
                "n":      len(vals),
            }
            for tier, vals in scores_by_tier.items()
        }
    }
    with open(docs_dir / "calibration.json", "w", encoding="utf-8") as f:
        json.dump(calibration_data, f, indent=2)
    print(f"   Saved calibration data → docs/calibration.json")

    return thresh_easy_medium, thresh_medium_hard, accuracy


if __name__ == "__main__":
    calibrate()
