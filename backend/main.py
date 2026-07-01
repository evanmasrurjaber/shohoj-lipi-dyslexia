"""
backend/main.py — FastAPI Backend for Shohoj Lipi
=================================================
Core API that handles text simplification requests.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load .env file so GEMINI_API_KEY is available when running via uvicorn
load_dotenv()

# Add project root to path so we can import ml modules
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from ml.readability_scorer import compute_readability, init_scorer, _bnlp_sentence_tokenize

# Try to load the Sentence Router (requires ONNX and trained model)
try:
    from ml.sentence_router import SentenceRouter
    router = SentenceRouter()
    has_ml_router = True
except Exception as e:
    print(f"ML Router not available: {e}. Using rule-based fallback.")
    has_ml_router = False

# Try to load the LLM Simplifier (requires GEMINI_API_KEY)
try:
    from ml.llm_simplifier import LLMSimplifier
    llm = LLMSimplifier()
    has_llm = True
except Exception as e:
    print(f"LLM Simplifier not available: {e}. Using mock fallback.")
    has_llm = False

app = FastAPI(title="Shohoj Lipi API")

# Initialize static resources on startup
@app.on_event("startup")
async def startup_event():
    init_scorer()

class SimplifyRequest(BaseModel):
    text: str
    target_tier: str = "Easy" # Easy, Medium

class SimplifyResponse(BaseModel):
    original_text: str
    simplified_text: str
    original_readability: dict
    new_readability: dict
    sentences_processed: list

def mock_llm_simplification(sentence: str) -> str:
    """Fallback mock simplification when no API key is set."""
    return sentence.replace("কৃষিনির্ভর", "কৃষি কাজ করে এমন").replace("অত্যন্ত", "খুবই")

def route_and_simplify(text: str) -> dict:
    sentences = _bnlp_sentence_tokenize(text)
    processed = []
    final_text_parts = []
    
    for sent in sentences:
        if not sent.strip():
            continue

        # --- Hybrid Routing Strategy ---
        # The ONNX router was trained on literary/newspaper text and tends to
        # over-predict "Complex" for informal/children's text (domain mismatch).
        # We use the rule-based readability scorer as the primary gate:
        #   - If sentence readability score > 0.45 (Hard tier) → treat as Complex
        #   - OR if ML router is very highly confident (>0.99) → treat as Complex
        # This prevents simple Grade 1 sentences from being sent to the LLM.

        sent_readability = compute_readability(sent)
        is_hard_by_rules = sent_readability["score"] > 0.45

        ml_says_complex = False
        confidence = 0.0
        if has_ml_router:
            route_res = router.classify(sent)
            ml_says_complex = (route_res["label"] == "Complex" and route_res["score"] > 0.99)
            confidence = route_res["score"]
        else:
            from ml.cc_density import bangla_word_count
            ml_says_complex = len(bangla_word_count(sent)) > 8
            confidence = 1.0

        is_complex = is_hard_by_rules or ml_says_complex
            
        # 2. Simplification
        if is_complex:
            if has_llm:
                simplified = llm.simplify_sentence(sent)
            else:
                simplified = mock_llm_simplification(sent)
            processed.append({
                "original": sent,
                "simplified": simplified,
                "was_complex": True,
                "confidence": confidence
            })
            final_text_parts.append(simplified)
        else:
            processed.append({
                "original": sent,
                "simplified": sent,
                "was_complex": False,
                "confidence": confidence
            })
            final_text_parts.append(sent)
            
    def ensure_period(text: str) -> str:
        text = text.strip()
        if text and text[-1] not in "।.?!":
            return text + "।"
        return text

    final_text = " ".join(ensure_period(part) for part in final_text_parts)

    return {
        "final_text": final_text,
        "processed": processed
    }

@app.post("/api/simplify", response_model=SimplifyResponse)
async def simplify_text(req: SimplifyRequest):
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty.")
        
    # 1. Document Readability Before
    doc_before = compute_readability(req.text)
    
    # 2. Sentence Routing & LLM
    pipeline_result = route_and_simplify(req.text)
    simplified_text = pipeline_result["final_text"]
    
    # 3. Document Readability After
    doc_after = compute_readability(simplified_text)
    
    return SimplifyResponse(
        original_text=req.text,
        simplified_text=simplified_text,
        original_readability=doc_before,
        new_readability=doc_after,
        sentences_processed=pipeline_result["processed"]
    )

@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "ml_router_loaded": has_ml_router,
        "llm_loaded": has_llm,
    }