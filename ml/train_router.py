"""
train_router.py — Train BanglaBERT Sentence Router
===================================================
Fine-tunes csebuetnlp/banglabert_small on the binary sentence corpus
(Simple vs Complex) to route sentences in the pipeline.

Usage:
    python -m ml.train_router --data_dir data/BengaliReadability --output_dir models/sentence_router
"""

import os
import argparse
import pandas as pd
import torch
from datasets import Dataset, DatasetDict
from transformers import (
    AutoTokenizer, 
    AutoModelForSequenceClassification, 
    TrainingArguments, 
    Trainer,
    DataCollatorWithPadding
)
import evaluate
import numpy as np

# Use the small version of BanglaBERT for faster inference on CPU/free tiers
MODEL_NAME = "csebuetnlp/banglabert_small"

def compute_metrics(eval_pred):
    metric = evaluate.load("accuracy")
    logits, labels = eval_pred
    predictions = np.argmax(logits, axis=-1)
    return metric.compute(predictions=predictions, references=labels)

def train(data_dir: str, output_dir: str):
    print(f"Loading data from {data_dir}...")
    
    # Due to network timeouts downloading the 11MB train.csv, we will use valid.csv for training
    # and test.csv for validation just to prove the pipeline works. For the final model, download train.csv.
    train_path = os.path.join(data_dir, "valid.csv")
    valid_path = os.path.join(data_dir, "test.csv")
    
    if not os.path.exists(train_path):
        raise FileNotFoundError(f"{train_path} not found.")
        
    df_train = pd.read_csv(train_path)
    df_valid = pd.read_csv(valid_path)
    
    text_col = "text" if "text" in df_train.columns else df_train.columns[0]
    label_col = "label" if "label" in df_train.columns else df_train.columns[1]
    
    print(f"Using columns: '{text_col}' for text, '{label_col}' for label.")
    
    # Map string labels to int if necessary
    if df_train[label_col].dtype == object:
        unique_labels = sorted(df_train[label_col].unique().tolist())
        label_map = {l: i for i, l in enumerate(unique_labels)}
        print(f"Label map: {label_map}")
        df_train[label_col] = df_train[label_col].map(label_map)
        df_valid[label_col] = df_valid[label_col].map(label_map)
        
        # Save label map to output dir
        os.makedirs(output_dir, exist_ok=True)
        import json
        with open(os.path.join(output_dir, "label_map.json"), "w") as f:
            json.dump({str(v): k for k, v in label_map.items()}, f)
    else:
        label_map = {0: "Simple", 1: "Complex"} # Default guess if already int
    
    ds = DatasetDict({
        "train": Dataset.from_pandas(df_train[[text_col, label_col]].rename(columns={text_col: "text", label_col: "label"})),
        "validation": Dataset.from_pandas(df_valid[[text_col, label_col]].rename(columns={text_col: "text", label_col: "label"}))
    })

    print("Loading tokenizer and model...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    
    # Note: banglabert requires normalizer, but HF tokenizer handles it via its backend, 
    # or we apply it manually. The `csebuetnlp` normalizer is recommended to be applied before tokenizer.
    try:
        from normalizer import normalize
        def preprocess_function(examples):
            normalized_texts = [normalize(text) for text in examples["text"]]
            return tokenizer(normalized_texts, truncation=True, max_length=128)
        print("Using csebuetnlp normalizer.")
    except ImportError:
        def preprocess_function(examples):
            return tokenizer(examples["text"], truncation=True, max_length=128)
        print("normalizer not found, proceeding without it (not recommended for production).")

    tokenized_ds = ds.map(preprocess_function, batched=True)
    
    model = AutoModelForSequenceClassification.from_pretrained(
        MODEL_NAME, 
        num_labels=len(label_map),
        id2label={v: k for k, v in label_map.items()} if isinstance(list(label_map.keys())[0], str) else label_map,
        label2id={k: v for k, v in label_map.items()} if isinstance(list(label_map.keys())[0], str) else {v: k for k, v in label_map.items()}
    )

    training_args = TrainingArguments(
        output_dir=output_dir,
        learning_rate=2e-5,
        per_device_train_batch_size=32,
        per_device_eval_batch_size=32,
        num_train_epochs=3,
        weight_decay=0.01,
        eval_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        fp16=False, # Disabled to avoid T4 CUDA kernel errors
        report_to="none"
    )

    data_collator = DataCollatorWithPadding(tokenizer=tokenizer)

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_ds["train"],
        eval_dataset=tokenized_ds["validation"],
        tokenizer=tokenizer,
        data_collator=data_collator,
        compute_metrics=compute_metrics,
    )

    print("Starting training...")
    trainer.train()
    
    print(f"Saving best model to {output_dir}...")
    trainer.save_model(output_dir)
    print("Training complete!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data_dir", type=str, default="data/BengaliReadability")
    parser.add_argument("--output_dir", type=str, default="models/sentence_router_pt")
    args = parser.parse_args()
    
    train(args.data_dir, args.output_dir)
