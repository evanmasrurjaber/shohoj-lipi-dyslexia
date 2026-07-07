"""
simplify.py — LLM-based sentence simplification via Gemini API.

Flow per input text:
  1. Split into sentences
  2. Classify each sentence: Simple → leave unchanged, Complex → send to LLM
  3. Reassemble and return

Uses google-genai SDK with gemini-2.0-flash (free tier, fast, great Bangla support).
"""

import os
from google import genai
from google.genai import types
from ml import readability_scorer  # pylint: disable=import-error,wrong-import-position

# ── Lazy Gemini client ────────────────────────────────────────────────────
# Created on first use so GEMINI_API_KEY is read AFTER load_dotenv() runs.
_client = None

def get_client() -> genai.Client:
    global _client
    if _client is None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key or api_key == "your_gemini_api_key_here":
            raise RuntimeError(
                "GEMINI_API_KEY is not set. "
                "Get a free key at https://aistudio.google.com/apikey "
                "and add it to backend/.env"
            )
        _client = genai.Client(api_key=api_key)
        print("[LLM] Gemini client initialized.")
    return _client


# gemini-2.0-flash: free tier, ~1s latency, excellent multilingual/Bangla support.
# Switch to "gemini-2.5-flash" for higher quality (slightly slower).
MODEL_NAME = "gemini-3.5-flash"

SYSTEM_PROMPT = """You are a Bangla reading accessibility expert. You simplify Bangla text for children with dyslexia (ages 6-14).

RULES:
1. Break long sentences into 2-3 shorter ones (max 12 words per sentence)
2. Replace conjunct consonants (যুক্তবর্ণ) with simpler alternatives when possible
   e.g., "বিদ্যালয়" -> "স্কুল", "পুস্তক" -> "বই", "অধ্যয়ন" -> "পড়া"
3. Prefer shorter, everyday Bangla words over formal literary ones
4. Preserve ALL factual meaning — never add or remove information
5. Keep the same paragraph structure
6. If a word has no simpler alternative, keep it unchanged

EASY-WORD SUBSTITUTIONS (use these when applicable):
{easy_words}

OUTPUT FORMAT:
Return ONLY the simplified Bangla text. No explanations, no English, no markdown."""


def build_system_prompt() -> str:
    """Build prompt with the easy-word list loaded at startup."""
    sample = list(readability_scorer.EASY_WORDS)[:500] if readability_scorer.EASY_WORDS else []
    words_str = "、".join(sample) if sample else "(word list not loaded)"
    return SYSTEM_PROMPT.format(easy_words=words_str)


def simplify_sentence_with_llm(sentence: str, max_retries: int = 2) -> str:
    """
    Send a single complex Bangla sentence to Gemini for simplification.
    Falls back to the original sentence on any error.
    """
    import time
    system_prompt = build_system_prompt()
    user_prompt = f"Simplify this Bangla text:\n---\n{sentence}\n---"

    for attempt in range(max_retries + 1):
        try:
            response = get_client().models.generate_content(
                model=MODEL_NAME,
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=0.3,
                    max_output_tokens=1024,
                ),
            )
            result = response.text.strip()

            # Guard: must contain Bangla characters, otherwise it's garbage
            if result and any('\u0980' <= c <= '\u09FF' for c in result):
                print(f"[LLM] OK (attempt {attempt+1}) — {len(result)} chars")
                return result

            print(f"[LLM] Non-Bangla response — returning original")
            return sentence

        except Exception as e:
            err = str(e)
            if attempt < max_retries:
                wait = 1.5 * (attempt + 1)
                print(f"[LLM] Error attempt {attempt+1}: {err[:80]}. Retrying in {wait:.1f}s...")
                time.sleep(wait)
            else:
                print(f"[LLM] Failed after {max_retries+1} attempts: {err[:120]}")
                return sentence  # always return something


def simplify_text(text: str, tokenizer, router) -> dict:
    """
    Splits text into sentences, routes each through the sentence router,
    sends only Complex sentences to Gemini, and reassembles the result.

    Returns:
        {
            "simplified_text": str,
            "sentence_breakdown": list[dict]  — per-sentence details
        }
    """
    sentences = tokenizer.sentence_tokenize(text)
    breakdown = []
    output_sentences = []

    for sent in sentences:
        sent = sent.strip()
        if not sent:
            continue

        route_result = router.classify(sent)
        label = route_result["label"]

        if label == "Complex":
            simplified = simplify_sentence_with_llm(sent)
        else:
            simplified = sent

        output_sentences.append(simplified)
        breakdown.append({
            "original":   sent,
            "label":      label,
            "confidence": route_result["score"],
            "simplified": simplified,
        })

    simplified_text = " ".join(output_sentences)
    return {
        "simplified_text":    simplified_text,
        "sentence_breakdown": breakdown,
    }