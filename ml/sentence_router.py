"""
sentence_router.py — BanglaBERT Sentence Router Inference
=========================================================
Loads the quantized ONNX model for high-speed inference on CPU.
Classifies a given Bangla sentence as "Simple" or "Complex".
"""

import os
from optimum.onnxruntime import ORTModelForSequenceClassification
from transformers import AutoTokenizer

class SentenceRouter:
    def __init__(self, model_dir: str = "zephrox/banglabert-sentence-router-onnx"):
        """
        Initialize the router with the ONNX model — either a local folder
        or a Hugging Face Hub repo ID.
        """
        print(f"Loading ONNX model from {model_dir}...")
        self.tokenizer = AutoTokenizer.from_pretrained(model_dir)
        self.model = ORTModelForSequenceClassification.from_pretrained(model_dir)
        
        # Load csebuetnlp normalizer if available
        try:
            from normalizer import normalize
            self.normalize = normalize
        except ImportError:
            self.normalize = lambda x: x

    def classify(self, text: str) -> dict:
        """
        Classify a single sentence.
        Returns a dict: {'label': 'Simple'/'Complex', 'score': float}
        """
        normalized_text = self.normalize(text)
        inputs = self.tokenizer(normalized_text, return_tensors="pt", truncation=True, max_length=128)
        
        outputs = self.model(**inputs)
        logits = outputs.logits
        probabilities = logits.softmax(dim=-1).squeeze().tolist()
        
        predicted_class_id = logits.argmax(dim=-1).item()
        id2label = getattr(self.model.config, 'id2label', {0: 'Simple', 1: 'Complex'})
        predicted_label = id2label.get(predicted_class_id, 'Complex')
        
        return {
            "label": predicted_label,
            "score": probabilities[predicted_class_id],
            "probabilities": {
                id2label.get(i, str(i)): prob
                for i, prob in enumerate(probabilities)
            }
        }

if __name__ == "__main__":
    # Test the router if model exists
    import sys
    try:
        router = SentenceRouter()
        
        test_sentences = [
            "এ দেশ অনেক সুন্দর।", # Should be Simple
            "বিশ্বসাহিত্যের ইতিহাসে রবীন্দ্রনাথ ঠাকুরের সৃষ্টিকর্ম এক অনন্য স্থান অধিকার করেছে।" # Should be Complex
        ]
        
        print("\nRouter Test:")
        for sent in test_sentences:
            res = router.classify(sent)
            print(f"Text: {sent}")
            print(f"Prediction: {res['label']} (Confidence: {res['score']:.4f})\n")

        for sent in test_sentences:
            res = router.classify(sent)
            print(f"Text: {sent}")
            print(f"Probabilities: {res['probabilities']}")

        # Broader sanity check against known easy/hard passages
        import csv
        with open("data/eval_passages.csv", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        easy_rows = [r for r in rows if r["intended_difficulty"].strip().lower() == "easy"][:10]
        hard_rows = [r for r in rows if r["intended_difficulty"].strip().lower() == "hard"][:10]
        for label, group in [("EASY", easy_rows), ("HARD", hard_rows)]:
            print(f"\n--- {label} passages ---")
            for r in group:
                res = router.classify(r["text"][:60])
                print(f"  {res['label']:8s} ({res['score']:.3f})  {r['text'][:40]}")
    except Exception as e:
        print(f"Could not initialize test: {e}")
        print("You must train and export the model first!")
