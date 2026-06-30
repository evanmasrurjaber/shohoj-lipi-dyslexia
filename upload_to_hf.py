import os
from huggingface_hub import HfApi, create_repo

HF_TOKEN = os.getenv("HF_TOKEN")
USERNAME = "zephrox"
REPO_NAME = "banglabert-sentence-router-onnx"
REPO_ID = f"{USERNAME}/{REPO_NAME}"

if not HF_TOKEN:
    print("❌ ERROR: Please set HF_TOKEN environment variable!")
    exit(1)

api = HfApi(token=HF_TOKEN)

print(f"Creating repository {REPO_ID} on HuggingFace Hub...")
try:
    create_repo(repo_id=REPO_ID, repo_type="model", exist_ok=True, token=HF_TOKEN)
    print("✅ Repository created (or already exists).")
except Exception as e:
    print(f"⚠️ Could not create repo: {e}")

print(f"Uploading ONNX model files to {REPO_ID}...")
api.upload_folder(
    folder_path="models/sentence_router_onnx",
    repo_id=REPO_ID,
    repo_type="model",
    commit_message="Initial commit: ONNX model and tokenizer for Shohoj Lipi"
)

print(f"Uploading Model Card...")
api.upload_file(
    path_or_fileobj="model_card.md",
    path_in_repo="README.md",
    repo_id=REPO_ID,
    repo_type="model",
    commit_message="Add Model Card"
)

print("\n🎉 SUCCESS! Your model is now live at:")
print(f"👉 https://huggingface.co/{REPO_ID}")
