---
language:
- bn
license: mit
tags:
- text-classification
- dyslexia
- accessibility
- onnx
- bangla
datasets:
- tafseer-nayeem/BengaliReadability
metrics:
- f1
- accuracy
---

# BanglaBERT Sentence Router (ONNX) - Shohoj Lipi 🧠

This is an ONNX-optimized, binary sentence classification model designed to detect complex Bengali sentences that are difficult for dyslexic readers (ages 6–14). It was created for **Shohoj Lipi (সহজ লিপি)**, a project for the **SciBlitz AI Challenge 2026 (Track C)**.

## Model Details
* **Base Model**: `csebuetnlp/banglabert` (Electra architecture)
* **Format**: ONNX (CPU optimized for ultra-fast, low-memory inference)
* **Task**: Binary Classification (`0` = Simple, `1` = Complex)
* **Training Data**: 96,000+ sentences from the `BengaliReadability` dataset

## Intended Use
This model acts as a "Router" in a text simplification pipeline. It rapidly scans Bengali sentences and flags the complex ones (`Label 1`) to be sent to a Large Language Model (like Gemini) for simplification and syllable-scaffolding, while allowing simple sentences (`Label 0`) to pass through untouched.

## Why ONNX?
Exporting BanglaBERT to ONNX reduces CPU inference time from ~2.0 seconds to ~300ms and cuts RAM usage by over 60%, allowing it to run smoothly on free-tier hosting services (like Render or Railway) without needing a GPU.

## Usage (Python)
You can load this model locally using `onnxruntime` and HuggingFace's tokenizers:

```python
import numpy as np
from transformers import AutoTokenizer
from optimum.onnxruntime import ORTModelForSequenceClassification

# Load tokenizer and ONNX model
tokenizer = AutoTokenizer.from_pretrained("YOUR_USERNAME/banglabert-sentence-router-onnx")
model = ORTModelForSequenceClassification.from_pretrained("YOUR_USERNAME/banglabert-sentence-router-onnx")

text = "বাংলাদেশের অর্থনীতি মূলত কৃষিনির্ভর।"
inputs = tokenizer(text, return_tensors="pt")

# Inference
outputs = model(**inputs)
logits = outputs.logits.detach().numpy()
predicted_class = np.argmax(logits, axis=1)[0]
confidence = np.max(np.exp(logits) / np.sum(np.exp(logits), axis=1, keepdims=True))

print("Class:", "Complex" if predicted_class == 1 else "Simple")
print("Confidence:", confidence)
```

## Performance
* **Validation Accuracy**: 85.0%
* **F1 Score**: > 0.80

## Limitations
* The model struggles with highly technical medical or legal jargon, as it was trained primarily on NCTB school textbooks and literature.
* It evaluates complexity at the *sentence level*, not the document level. It should be used in conjunction with a document-level readability heuristic.
