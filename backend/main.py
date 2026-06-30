from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from bnlp import NLTKTokenizer
from cc_density import compute_cc_density
from gtts import gTTS
import unicodedata
import io

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

tokenizer = NLTKTokenizer()

class TextInput(BaseModel):
    text: str

def normalize_bangla(text: str) -> str:
    return unicodedata.normalize("NFC", text)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/classify")
def classify(input: TextInput):
    if not input.text.strip():
        raise HTTPException(status_code=400, detail="Empty input")
    text = normalize_bangla(input.text)
    sentences = tokenizer.sentence_tokenize(text)
    if len(sentences) == 0:
        raise HTTPException(status_code=400, detail="Could not tokenize input")
    cc_density = compute_cc_density(text)
    avg_sent_len = sum(len(s) for s in sentences) / len(sentences)
    score = round((cc_density * 1.5) + (avg_sent_len * 0.3), 2)
    if score < 20:
        tier = "Easy"
    elif score < 40:
        tier = "Medium"
    else:
        tier = "Hard"
    return {
        "score": score,
        "tier": tier,
        "cc_density": cc_density,
        "avg_sentence_length": round(avg_sent_len, 2),
    }

@app.post("/tts")
def tts_endpoint(input: TextInput):
    if not input.text.strip():
        raise HTTPException(status_code=400, detail="Empty input")
    tts = gTTS(text=input.text, lang="bn")
    buf = io.BytesIO()
    tts.write_to_fp(buf)
    buf.seek(0)
    return StreamingResponse(buf, media_type="audio/mpeg")