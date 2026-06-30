import pandas as pd
import requests
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
csv_path = os.path.join(BASE_DIR, "..", "data", "eval_passages.csv")

df = pd.read_csv(csv_path, encoding="utf-8-sig")
sample = df.sample(10, random_state=1)

for _, row in sample.iterrows():
    response = requests.post(
        "http://127.0.0.1:8000/classify",
        json={"text": row["text"]}
    )
    result = response.json()
    print(f"ID {row['id']} | intended: {row['intended_difficulty']} | predicted: {result.get('tier')} | score: {result.get('score')}")