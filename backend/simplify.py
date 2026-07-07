"""
simplify.py — LLM-based sentence simplification, wired to the sentence router.

Flow per input text:
  1. Split into sentences
  2. Classify each sentence: Simple → leave unchanged, Complex → send to LLM
  3. Reassemble and return

NOTE: This uses OpenRouter (https://openrouter.ai) instead of OpenAI directly,
so we can use a free-tier model. It's still the OpenAI SDK under the hood —
OpenRouter just exposes an OpenAI-compatible endpoint, so only the client
setup and model name differ from a stock OpenAI integration.
"""

import os
import time
from openai import OpenAI, RateLimitError
from ml import readability_scorer  # pylint: disable=import-error,wrong-import-position

client = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1",
)

# Free-tier model on OpenRouter. Check https://openrouter.ai/models?max_price=0
# for the current list — free models get added/removed/renamed over time.
MODEL_NAME = "openrouter/free"

SYSTEM_PROMPT_TEMPLATE = """You are a Bangla reading accessibility expert. You simplify Bangla text for children with dyslexia (ages 6-14).

RULES:
1. Break long sentences into 2-3 shorter ones (max 12 words per sentence)
2. Replace conjunct consonants (যুক্তবর্ণ) with simpler alternatives when possible
   e.g., "বিদ্যালয়" -> "স্কুল", "পুস্তক" -> "বই"
3. Prefer words from the easy-word list provided below
4. Preserve ALL factual meaning -- never add or remove information
5. Keep the same paragraph structure
6. If a word has no simpler alternative, keep it unchanged

EASY-WORD LIST (use these when possible):
{easy_words}

OUTPUT FORMAT:
Return ONLY the simplified Bangla text. No explanations, no English.
"""


def build_system_prompt() -> str:
    print(f"Easy words loaded: {len(readability_scorer.EASY_WORDS)}")
    # EASY_WORDS is populated by init_scorer() at startup, in main.py
    sample = list(readability_scorer.EASY_WORDS)[:500] if readability_scorer.EASY_WORDS else []
    words_str = "、".join(sample) if sample else "(word list not loaded)"
    return SYSTEM_PROMPT_TEMPLATE.format(easy_words=words_str)


def simplify_sentence_with_llm(sentence: str, max_retries: int = 3) -> str:
    system_prompt = build_system_prompt()
    user_prompt = f"Simplify this Bangla text:\n---\n{sentence}\n---"

    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.3,
            )
            return response.choices[0].message.content.strip()
        except RateLimitError:
            wait_time = 2 ** attempt  # 1s, then 2s, then 4s
            print(f"Rate limited, retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})...")
            time.sleep(wait_time)

    print(f"Still rate-limited after {max_retries} retries -- returning original sentence unchanged.")
    return sentence


def simplify_text(text: str, tokenizer, router) -> dict:
    """
    Splits text into sentences, routes each one through the BanglaBERT
    Simple/Complex classifier, sends only Complex sentences to the LLM,
    and reassembles the result.

    Returns a dict with the simplified text plus a per-sentence breakdown
    (useful for debugging and for Member B's diff-highlight stretch feature later).
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
            "original": sent,
            "label": label,
            "confidence": route_result["score"],
            "simplified": simplified,
        })

    simplified_text = " ".join(output_sentences)
    return {
        "simplified_text": simplified_text,
        "sentence_breakdown": breakdown,
    }