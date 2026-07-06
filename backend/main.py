import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from functools import lru_cache
from simplify import simplify_text
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from bnlp import NLTKTokenizer
import unicodedata
import re

from ml.syllabifier import syllabify_text, init_syllabifier  # pylint: disable=import-error,wrong-import-position
from ml.readability_scorer import compute_readability, init_scorer  # pylint: disable=import-error,wrong-import-position
from ml.sentence_router import SentenceRouter  # pylint: disable=import-error,wrong-import-position

from fastapi.responses import JSONResponse
from fastapi.requests import Request

# ✅ app is created FIRST before anything uses it
app = FastAPI()
tokenizer = NLTKTokenizer()
router = None


class TextInput(BaseModel):
    text: str


def normalize_bangla(text: str) -> str:
    return unicodedata.normalize("NFC", text)


def is_bangla_text(text: str) -> bool:
    if not text or not text.strip():
        return False
    return bool(re.search(r'[\u0980-\u09FF]', text))


# ✅ exception handler AFTER app is defined
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    print(f"[UNHANDLED ERROR] {request.url.path}: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Something went wrong processing your request. Please try again."},
    )


# ✅ middleware AFTER app is defined
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def load_models():
    global router
    print("Loading readability scorer resources...")
    init_scorer()
    print("Loading sentence router model...")
    router = SentenceRouter()
    print("Loading pronunciation dictionary...")
    init_syllabifier()
    print("Startup complete.")


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


@lru_cache(maxsize=256)
def _process_cached(normalized_text: str) -> dict:
    before = compute_readability(normalized_text)
    simplify_result = simplify_text(normalized_text, tokenizer, router)
    simplified_text = simplify_result["simplified_text"]
    after = compute_readability(simplified_text)
    return {
        "before_score": before["score"],
        "before_tier": before["tier"],
        "simplified_text": simplified_text,
        "after_score": after["score"],
        "after_tier": after["tier"],
    }


@app.post("/process")
def process(input: TextInput):
    if not is_bangla_text(input.text):
        raise HTTPException(status_code=400, detail="Input must be non-empty Bangla text")
    text = normalize_bangla(input.text)
    return _process_cached(text)


@app.post("/syllabify")
def syllabify(input: TextInput):
    if not is_bangla_text(input.text):
        raise HTTPException(status_code=400, detail="Input must be non-empty Bangla text")
    text = normalize_bangla(input.text)
    return {"syllabified_text": syllabify_text(text)}