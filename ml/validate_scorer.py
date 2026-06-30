"""
validate_scorer.py — Validate Rule-Based Readability Scorer
============================================================
Validates the readability_scorer against:
  1. Our own eval_passages.csv (NCTB-sourced, labelled easy/medium/hard)
  2. BengaliReadability 618-doc corpus (if downloaded)

Outputs:
  - Tier agreement accuracy (overall + per-class)
  - Confusion matrix
  - Per-feature statistics per tier
  - Calibration recommendations if agreement < 75%

Usage:
    python -m ml.validate_scorer
"""

import csv
import json
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ml.readability_scorer import compute_readability, init_scorer


# ── Helpers ──────────────────────────────────────────────────────────────────

def load_eval_passages(path: str) -> list:
    """Load eval_passages.csv → list of dicts with text + intended_difficulty."""
    rows = []
    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("text") and row.get("intended_difficulty"):
                rows.append({
                    "id":         row.get("id", ""),
                    "text":       unicodedata.normalize("NFC", row["text"]),
                    "true_tier":  row["intended_difficulty"].strip().capitalize(),
                    "source":     row.get("source", ""),
                })
    return rows


def confusion_matrix_str(matrix: dict, labels: list) -> str:
    """Format a confusion matrix as a readable string."""
    header = f"{'':12s}" + "".join(f"{l:10s}" for l in labels)
    lines = [header, "─" * (12 + 10 * len(labels))]
    for true in labels:
        row = f"True {true:7s}" + "".join(
            f"{matrix[true].get(pred, 0):10d}" for pred in labels
        )
        lines.append(row)
    return "\n".join(lines)


def per_class_metrics(matrix: dict, labels: list) -> dict:
    """Compute precision, recall, F1 per class from confusion matrix."""
    metrics = {}
    for cls in labels:
        tp = matrix[cls].get(cls, 0)
        fp = sum(matrix[other].get(cls, 0) for other in labels if other != cls)
        fn = sum(matrix[cls].get(other, 0) for other in labels if other != cls)
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall    = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1        = (2 * precision * recall / (precision + recall)
                     if (precision + recall) > 0 else 0.0)
        metrics[cls] = {
            "precision": round(precision, 3),
            "recall":    round(recall, 3),
            "f1":        round(f1, 3),
            "support":   tp + fn,
        }
    return metrics


# ── Main Validation ──────────────────────────────────────────────────────────

def validate(csv_path: str, output_path: str = None) -> dict:
    project_root = Path(__file__).parent.parent

    print("\n" + "=" * 65)
    print("  READABILITY SCORER VALIDATION")
    print("=" * 65)

    # Init scorer (loads easy-word list + conjunct list if available)
    init_scorer()

    # Load data
    passages = load_eval_passages(csv_path)
    print(f"\n  Loaded {len(passages)} passages from: {csv_path}")

    label_dist = Counter(p["true_tier"] for p in passages)
    print(f"  Label distribution: {dict(label_dist)}")

    # Score all passages
    results = []
    feature_stats = defaultdict(lambda: defaultdict(list))
    LABELS = ["Easy", "Medium", "Hard"]

    print(f"\n  Scoring {len(passages)} passages...", end="", flush=True)
    for i, p in enumerate(passages):
        scored = compute_readability(p["text"])
        pred_tier = scored["tier"]
        correct = (pred_tier == p["true_tier"])
        results.append({**p, **scored, "pred_tier": pred_tier, "correct": correct})
        for feat, val in scored["features"].items():
            feature_stats[p["true_tier"]][feat].append(val)
        if (i + 1) % 100 == 0:
            print(f" {i+1}", end="", flush=True)
    print(" ✓")

    # ── Overall accuracy ─────────────────────────────────────────────────────
    n_correct = sum(1 for r in results if r["correct"])
    accuracy  = n_correct / len(results) if results else 0
    print(f"\n  Overall Tier Agreement: {n_correct}/{len(results)} = {accuracy:.1%}")

    if accuracy >= 0.85:
        verdict = "✅ EXCELLENT — Scorer well-calibrated"
    elif accuracy >= 0.75:
        verdict = "✅ GOOD — Meets target threshold"
    elif accuracy >= 0.60:
        verdict = "⚠️  ACCEPTABLE — Consider re-calibrating weights"
    else:
        verdict = "❌ POOR — Recalibrate or use BanglaBERT doc classifier"
    print(f"  Verdict: {verdict}")

    # ── Confusion matrix ─────────────────────────────────────────────────────
    confusion = {l: Counter() for l in LABELS}
    for r in results:
        confusion[r["true_tier"]][r["pred_tier"]] += 1

    print(f"\n  Confusion Matrix (rows=True, cols=Predicted):")
    print("  " + confusion_matrix_str(confusion, LABELS).replace("\n", "\n  "))

    # ── Per-class metrics ─────────────────────────────────────────────────────
    cls_metrics = per_class_metrics(confusion, LABELS)
    print(f"\n  Per-Class Metrics:")
    print(f"  {'Class':10s} {'Precision':>10s} {'Recall':>10s} {'F1':>10s} {'Support':>10s}")
    print("  " + "─" * 52)
    for cls in LABELS:
        m = cls_metrics[cls]
        print(f"  {cls:10s} {m['precision']:>10.3f} {m['recall']:>10.3f} {m['f1']:>10.3f} {m['support']:>10d}")

    # ── Feature statistics per tier ──────────────────────────────────────────
    print(f"\n  Feature Means per True Tier:")
    feat_names = ["cc_density", "avg_sent_len", "avg_word_len", "rare_word_ratio"]
    header = f"  {'Feature':25s}" + "".join(f"{l:>12s}" for l in LABELS)
    print(header)
    print("  " + "─" * (25 + 12 * len(LABELS)))
    for feat in feat_names:
        row = f"  {feat:25s}"
        for tier in LABELS:
            vals = feature_stats[tier][feat]
            mean = sum(vals) / len(vals) if vals else 0
            row += f"{mean:>12.4f}"
        print(row)

    # ── Mis-classified examples ───────────────────────────────────────────────
    wrong = [r for r in results if not r["correct"]]
    print(f"\n  Mis-classified: {len(wrong)} ({len(wrong)/len(results):.1%})")
    if wrong:
        print(f"  Top 5 mis-classified examples:")
        for r in wrong[:5]:
            print(f"    ID {r['id']:5s} | True: {r['true_tier']:6s} | Pred: {r['pred_tier']:6s} | "
                  f"Score: {r['score']:.3f} | Source: {r['source']}")

    # ── Save detailed results ─────────────────────────────────────────────────
    summary = {
        "total_passages":    len(results),
        "correct":           n_correct,
        "accuracy":          round(accuracy, 4),
        "verdict":           verdict,
        "per_class_metrics": cls_metrics,
        "confusion_matrix":  {k: dict(v) for k, v in confusion.items()},
    }

    if output_path is None:
        output_path = str(project_root / "docs" / "scorer_validation.json")
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    # Save full results CSV
    results_csv = str(Path(output_path).parent / "scorer_validation_full.csv")
    with open(results_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "id", "source", "true_tier", "pred_tier", "correct",
            "score", "tier", "grade_estimate",
        ])
        writer.writeheader()
        for r in results:
            writer.writerow({k: r[k] for k in writer.fieldnames})

    print(f"\n  Saved summary  → {output_path}")
    print(f"  Saved full CSV → {results_csv}")
    print("\n" + "=" * 65)

    return summary


if __name__ == "__main__":
    project_root = Path(__file__).parent.parent
    csv_path = str(project_root / "data" / "eval_passages.csv")
    validate(csv_path)
