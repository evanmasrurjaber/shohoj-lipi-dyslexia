"""
data_audit.py — Day-1 Dataset Audit Script
===========================================
Audits all available data, reports corpus statistics, and confirms
everything needed for the pipeline is present.

Run:  python -m ml.data_audit
"""

import csv
import json
import os
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from ml.cc_density import cc_density_per_100_chars, bangla_word_count


PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR     = PROJECT_ROOT / "data"


def audit_eval_passages() -> dict:
    """Audit our main eval_passages.csv."""
    path = DATA_DIR / "eval_passages.csv"
    if not path.exists():
        return {"status": "MISSING", "path": str(path)}

    rows = []
    with open(path, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    difficulty_dist = Counter(r.get("intended_difficulty", "") for r in rows)
    source_dist     = Counter(r.get("source", "") for r in rows)

    # Length stats
    lengths = [len(r.get("text", "")) for r in rows]
    word_counts = [len(bangla_word_count(r.get("text", ""))) for r in rows]

    # CC-density per difficulty group
    cc_by_diff = defaultdict(list)
    for r in rows:
        cc = cc_density_per_100_chars(unicodedata.normalize("NFC", r.get("text", "")))
        cc_by_diff[r.get("intended_difficulty", "unknown")].append(cc)

    cc_means = {k: round(sum(v)/len(v), 3) for k, v in cc_by_diff.items() if v}

    return {
        "status":              "OK",
        "path":                str(path),
        "total_passages":      len(rows),
        "difficulty_dist":     dict(difficulty_dist),
        "source_dist":         dict(source_dist),
        "avg_char_length":     round(sum(lengths) / len(lengths), 1) if lengths else 0,
        "avg_word_count":      round(sum(word_counts) / len(word_counts), 1) if word_counts else 0,
        "cc_density_by_diff":  cc_means,
    }


def audit_bengali_readability_corpus() -> dict:
    """Audit BengaliReadability dataset if cloned."""
    br_root = DATA_DIR / "BengaliReadability"
    if not br_root.exists():
        return {
            "status":  "MISSING",
            "message": "Clone via: git clone https://github.com/tafseer-nayeem/BengaliReadability.git data/BengaliReadability",
        }

    # Walk and find key files
    all_files = list(br_root.rglob("*.*"))
    file_summary = {}
    for f in all_files:
        ext = f.suffix.lower()
        file_summary.setdefault(ext, []).append(f.name)

    # Check specific expected files
    expected = {
        "easy_word_list": any("easy" in str(f).lower() for f in all_files),
        "conjunct_list":  any("conjunct" in str(f).lower() for f in all_files),
        "pronunciation":  any("pronunciation" in str(f).lower() or "dict" in str(f).lower() for f in all_files),
        "sentence_corpus": any("sentence" in str(f).lower() for f in all_files),
        "document_corpus": any("document" in str(f).lower() or "grade" in str(f).lower() for f in all_files),
    }

    return {
        "status":          "OK",
        "path":            str(br_root),
        "total_files":     len(all_files),
        "file_types":      {k: len(v) for k, v in file_summary.items()},
        "expected_assets": expected,
        "all_missing":     [k for k, v in expected.items() if not v],
    }


def audit_nctb_raw_data() -> dict:
    """Audit NCTB raw text files."""
    nctb_root = DATA_DIR / "raw" / "nctb_by_class"
    if not nctb_root.exists():
        return {"status": "MISSING"}

    class_dirs = [d for d in nctb_root.iterdir() if d.is_dir()]
    files_per_class = {}
    total_chars = 0

    for cls_dir in sorted(class_dirs):
        txt_files = list(cls_dir.rglob("*.txt"))
        total_cls_chars = 0
        for tf in txt_files:
            try:
                total_cls_chars += tf.stat().st_size
            except Exception:
                pass
        files_per_class[cls_dir.name] = {
            "txt_files": len(txt_files),
            "approx_kb": round(total_cls_chars / 1024, 1),
            "files":     [f.name for f in txt_files],
        }
        total_chars += total_cls_chars

    return {
        "status":          "OK",
        "path":            str(nctb_root),
        "class_dirs":      len(class_dirs),
        "total_approx_mb": round(total_chars / (1024 * 1024), 2),
        "classes":         files_per_class,
    }


def audit_python_env() -> dict:
    """Check that required Python packages are installed."""
    packages = {
        "bnlp-toolkit":   "bnlp",
        "transformers":   "transformers",
        "torch":          "torch",
        "datasets":       "datasets",
        "scikit-learn":   "sklearn",
        "bert-score":     "bert_score",
        "onnxruntime":    "onnxruntime",
        "openai":         "openai",
        "fastapi":        "fastapi",
        "gtts":           "gtts",
        "unicodedata":    "unicodedata",
    }
    status = {}
    for display_name, import_name in packages.items():
        try:
            __import__(import_name)
            status[display_name] = "✅ installed"
        except ImportError:
            status[display_name] = "❌ missing"
    return status


# ── Report ────────────────────────────────────────────────────────────────────

def print_section(title: str) -> None:
    print(f"\n{'═' * 65}")
    print(f"  {title}")
    print(f"{'═' * 65}")


def run_full_audit() -> None:
    print("\n" + "█" * 65)
    print("  SHOHOJ LIPI — DAY-1 DATA & ENVIRONMENT AUDIT")
    print("█" * 65)

    # 1. Eval passages
    print_section("1. EVAL PASSAGES (eval_passages.csv)")
    ep = audit_eval_passages()
    for k, v in ep.items():
        print(f"  {k:30s}: {v}")

    # 2. BengaliReadability corpus
    print_section("2. BENGALIREADABILITY CORPUS (GitHub)")
    br = audit_bengali_readability_corpus()
    for k, v in br.items():
        print(f"  {k:30s}: {v}")
    if br.get("all_missing"):
        print(f"\n  ⚠️  Missing assets: {br['all_missing']}")
        print("  → Run scorer validation without these (CC-density still works)")

    # 3. NCTB raw data
    print_section("3. NCTB RAW TEXT DATA")
    nctb = audit_nctb_raw_data()
    for k, v in nctb.items():
        if k != "classes":
            print(f"  {k:30s}: {v}")
    if "classes" in nctb:
        print(f"\n  Per-class breakdown:")
        for cls, info in nctb["classes"].items():
            print(f"    {cls:15s}: {info['txt_files']} files, ~{info['approx_kb']} KB")

    # 4. Python environment
    print_section("4. PYTHON PACKAGE STATUS")
    env = audit_python_env()
    for pkg, status in env.items():
        print(f"  {pkg:20s}: {status}")
    missing_pkgs = [k for k, v in env.items() if "missing" in v]
    if missing_pkgs:
        print(f"\n  📦 Install missing packages:")
        pip_names = {
            "transformers": "transformers", "torch": "torch",
            "datasets": "datasets", "scikit-learn": "scikit-learn",
            "bert-score": "bert-score", "onnxruntime": "onnxruntime",
            "openai": "openai",
        }
        install_list = " ".join(pip_names.get(p, p) for p in missing_pkgs if p in pip_names)
        if install_list:
            print(f"  pip install {install_list}")

    # 5. CC-density validation on sample passages
    print_section("5. CC-DENSITY SANITY CHECK")
    samples = [
        ("Easy (Class 1)",  "এ দেশ অনেক সুন্দর। দোয়েল আমাদের জাতীয় পাখি।"),
        ("Medium (Class 7)","বাংলাদেশের অর্থনীতি মূলত কৃষিনির্ভর এবং শিল্পায়ন প্রক্রিয়াধীন।"),
        ("Hard (Class 11)", "বিশ্বসাহিত্যের ইতিহাসে রবীন্দ্রনাথ ঠাকুরের সৃষ্টিকর্ম এক অনন্য স্থান অধিকার করেছে।"),
    ]
    print(f"\n  {'Label':20s} {'CC/100 chars':>15s}  Expected pattern")
    print("  " + "─" * 55)
    for label, text in samples:
        cc = cc_density_per_100_chars(text)
        expected = "low" if "Easy" in label else ("medium" if "Medium" in label else "high")
        print(f"  {label:20s} {cc:>15.4f}  → should be {expected}")

    # 6. Day-1 checklist
    print_section("6. DAY-1 COMPLETION CHECKLIST")
    checks = {
        "eval_passages.csv present":         ep.get("status") == "OK",
        "NCTB raw data present":             nctb.get("status") == "OK",
        "BengaliReadability cloned":         br.get("status") == "OK",
        "cc_density.py exists":              (PROJECT_ROOT / "ml" / "cc_density.py").exists(),
        "readability_scorer.py exists":      (PROJECT_ROOT / "ml" / "readability_scorer.py").exists(),
        "validate_scorer.py exists":         (PROJECT_ROOT / "ml" / "validate_scorer.py").exists(),
        "bnlp installed":                    "✅" in env.get("bnlp-toolkit", ""),
        "fastapi installed":                 "✅" in env.get("fastapi", ""),
    }
    all_done = True
    for item, done in checks.items():
        icon = "✅" if done else "❌"
        print(f"  {icon}  {item}")
        if not done:
            all_done = False

    print(f"\n  {'🎉 ALL DAY-1 TASKS COMPLETE' if all_done else '⚠️  Some tasks pending — see above'}")
    print("\n" + "█" * 65)

    # Save audit results
    docs_dir = PROJECT_ROOT / "docs"
    docs_dir.mkdir(exist_ok=True)
    audit_data = {
        "eval_passages": ep,
        "bengali_readability": br,
        "nctb_raw": nctb,
        "python_env": env,
    }
    with open(docs_dir / "day1_audit.json", "w", encoding="utf-8") as f:
        json.dump(audit_data, f, ensure_ascii=False, indent=2)
    print(f"\n  Audit saved to: docs/day1_audit.json")


if __name__ == "__main__":
    run_full_audit()
