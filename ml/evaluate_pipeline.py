"""
evaluate_pipeline.py — Evaluation Suite for DEV-A
=================================================
Calculates the required metrics for the final report:
1. BERTScore (Semantic preservation)
2. SARI (Simplification quality)
3. CC-density reduction
"""

import pandas as pd
import argparse
import os

try:
    from bert_score import score as bert_score
    import easse.sari as sari_scorer
except ImportError:
    print("⚠️ Please install evaluation dependencies:")
    print("pip install bert-score easse-nlp")

def evaluate_results(results_csv: str):
    """
    Assumes a CSV with columns: 'original_text', 'simplified_text', 'reference_text'
    (You can use easy-tier texts as a proxy for reference_text if no golden references exist).
    """
    if not os.path.exists(results_csv):
        print(f"Results file {results_csv} not found. Run the pipeline first to generate outputs.")
        return

    df = pd.read_csv(results_csv)
    original = df['original_text'].tolist()
    simplified = df['simplified_text'].tolist()
    
    # In SARI, references must be a list of lists (multiple references per sentence allowed)
    # If you only have one reference per text, wrap it: [[ref1], [ref2], ...]
    if 'reference_text' in df.columns:
        references = [[ref] for ref in df['reference_text'].tolist()]
    else:
        print("⚠️ No reference_text found. Using original_text as reference for SARI (not ideal).")
        references = [[ref] for ref in original]

    print("Calculating BERTScore... (this may take a moment to download the model)")
    # We use multilingual BERT for Bangla
    P, R, F1 = bert_score(simplified, original, lang="bn", model_type="bert-base-multilingual-cased")
    
    avg_bert_f1 = F1.mean().item()
    print(f"✅ Mean BERTScore F1: {avg_bert_f1:.4f} (Target: ≥ 0.82)")

    print("Calculating SARI...")
    # easse sari expects lists of strings
    sari_scores = []
    for orig, simp, refs in zip(original, simplified, references):
        # easse sari function takes (source, system_output, references)
        s_score = sari_scorer.corpus_sari([orig], [simp], [refs])
        sari_scores.append(s_score)
        
    avg_sari = sum(sari_scores) / len(sari_scores)
    print(f"✅ Mean SARI Score: {avg_sari:.2f} (Target: ≥ 35.0)")
    
    # Calculate CC-density reduction
    try:
        from ml.cc_density import compute_cc_density
        orig_cc = [compute_cc_density(t) for t in original]
        simp_cc = [compute_cc_density(t) for t in simplified]
        avg_drop = (sum(orig_cc) - sum(simp_cc)) / max(len(original), 1)
        print(f"✅ Mean CC-Density Reduction: {avg_drop:.2f} conjuncts per 100 chars")
    except ImportError:
        pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", type=str, default="data/pipeline_results.csv", help="CSV containing pipeline outputs")
    args = parser.parse_args()
    
    evaluate_results(args.results)
