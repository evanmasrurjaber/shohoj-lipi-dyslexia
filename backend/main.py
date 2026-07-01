import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))  # lets us import from ../ml

from dotenv import load_dotenv
load_dotenv()

from simplify import simplify_text
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from bnlp import NLTKTokenizer
import unicodedata
import re

from ml.readability_scorer import compute_readability, init_scorer
from ml.sentence_router import SentenceRouter
  # reads backend/.env, makes OPENAI_API_KEY available

app = FastAPI()
tokenizer = NLTKTokenizer()
router = None  # loaded once at startup, see below


class TextInput(BaseModel):
    text: str


def normalize_bangla(text: str) -> str:
    return unicodedata.normalize("NFC", text)


def is_bangla_text(text: str) -> bool:
    """Reject empty input or input with no Bangla characters at all."""
    if not text or not text.strip():
        return False
    return bool(re.search(r'[\u0980-\u09FF]', text))


@app.on_event("startup")
def load_models():
    """Runs once when the server starts — loads the readability scorer's
    word lists and the sentence router model, so requests don't pay that
    cost on every call."""
    global router
    print("Loading readability scorer resources...")
    init_scorer()
    print("Loading sentence router model...")
    router = SentenceRouter()
    print("Startup complete.")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten this to the real Vercel URL on Day 6
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/classify")
def classify(input: TextInput):
    if not is_bangla_text(input.text):
        raise HTTPException(status_code=400, detail="Input must be non-empty Bangla text")

    text = normalize_bangla(input.text)
    result = compute_readability(text)
    return result


@app.post("/simplify")
def simplify(input: TextInput):
    if not is_bangla_text(input.text):
        raise HTTPException(status_code=400, detail="Input must be non-empty Bangla text")

    text = normalize_bangla(input.text)
    result = simplify_text(text, tokenizer, router)
    return result