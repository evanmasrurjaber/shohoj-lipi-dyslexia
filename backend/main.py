import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))  # root → allows `from ml.xxx import yyy`
sys.path.insert(0, str(Path(__file__).parent))          # backend/ → allows `from simplify import ...`

from dotenv import load_dotenv
load_dotenv(dotenv_path=Path(__file__).parent / ".env")

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

from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.requests import Request
from gtts import gTTS
import io
import asyncio

print("[main] Starting global imports...")

# ✅ app is created FIRST before anything uses it
app = FastAPI()
tokenizer = None
router = None
models_loaded = False

print("[main] Global scope initialized. Waiting for Uvicorn startup hook...")


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
    
    # Provide specific error descriptions based on what failed
    path = request.url.path
    exc_msg = str(exc)
    
    if "Gemini API" in exc_msg or "google" in exc_msg.lower() or "genai" in exc_msg.lower():
        detail_msg = f"Gemini API Error: {exc_msg}"
    elif path == "/classify" or "readability" in exc_msg.lower() or "cc_density" in exc_msg.lower():
        detail_msg = f"Difficulty Scoring Model Error: {exc_msg}"
    elif path == "/process":
        # /process runs both simplification (Gemini) and difficulty scoring
        if "Gemini API" in exc_msg or "google" in exc_msg.lower() or "genai" in exc_msg.lower():
            detail_msg = f"Gemini API Error during simplification: {exc_msg}"
        else:
            detail_msg = f"Difficulty Scoring Error during evaluation: {exc_msg}"
    else:
        detail_msg = f"Internal Server Error ({path}): {exc_msg}"

    return JSONResponse(
        status_code=500,
        content={"detail": detail_msg},
    )


# ✅ middleware AFTER app is defined
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def load_models_sync():
    global router, tokenizer, models_loaded
    import nltk
    from bnlp import NLTKTokenizer
    print("Downloading NLTK data (punkt_tab)...")
    nltk.download("punkt_tab", quiet=True)
    nltk.download("punkt", quiet=True)
    print("Initializing NLTKTokenizer...")
    tokenizer = NLTKTokenizer()
    print("Loading readability scorer resources...")
    init_scorer()
    print("Loading sentence router model...")
    router = SentenceRouter()
    print("Loading pronunciation dictionary...")
    init_syllabifier()
    print("Startup complete.")
    models_loaded = True


@app.on_event("startup")
def startup_event():
    # Run heavy initialization in the background so Uvicorn startup doesn't block HF health checks
    loop = asyncio.get_event_loop()
    loop.run_in_executor(None, load_models_sync)


def check_models_ready():
    if not models_loaded:
        raise HTTPException(
            status_code=503,
            detail="Models are still loading in the background. Please try again in a few seconds."
        )


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/classify")
def classify(input: TextInput):
    check_models_ready()
    if not is_bangla_text(input.text):
        raise HTTPException(status_code=400, detail="Input must be non-empty Bangla text")
    text = normalize_bangla(input.text)
    result = compute_readability(text)
    return result


@app.post("/simplify")
def simplify(input: TextInput):
    check_models_ready()
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
    check_models_ready()
    if not is_bangla_text(input.text):
        raise HTTPException(status_code=400, detail="Input must be non-empty Bangla text")
    text = normalize_bangla(input.text)
    return _process_cached(text)


@app.post("/syllabify")
def syllabify(input: TextInput):
    check_models_ready()
    if not is_bangla_text(input.text):
        raise HTTPException(status_code=400, detail="Input must be non-empty Bangla text")
    text = normalize_bangla(input.text)
    return {"syllabified_text": syllabify_text(text)}


@app.post("/tts")
def tts(input: TextInput):
    """Convert simplified Bangla text to speech using gTTS.
    Returns an MP3 audio stream for the frontend TTS play button (F7).
    """
    check_models_ready()
    if not is_bangla_text(input.text):
        raise HTTPException(status_code=400, detail="Input must be non-empty Bangla text")
    text = normalize_bangla(input.text)
    try:
        tts_obj = gTTS(text=text, lang="bn", slow=False)
        audio_buffer = io.BytesIO()
        tts_obj.write_to_fp(audio_buffer)
        audio_buffer.seek(0)
        return StreamingResponse(
            audio_buffer,
            media_type="audio/mpeg",
            headers={"Content-Disposition": "inline; filename=tts.mp3"},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS generation failed: {e}") from e