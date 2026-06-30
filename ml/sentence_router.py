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
    def __init__(self, model_dir: str = "models/sentence_router_onnx"):
        """
        Initialize the router with the quantized ONNX model.
        """
        if not os.path.exists(model_dir):
            raise FileNotFoundError(f"Model directory not found at {model_dir}. Please run export_onnx.py first.")
            
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
    except Exception as e:
        print(f"Could not initialize test: {e}")
        print("You must train and export the model first!")
