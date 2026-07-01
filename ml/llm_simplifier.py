"""
ml/llm_simplifier.py — LLM Simplification Pipeline
====================================================
Uses Gemini API (primary) to simplify complex Bangla sentences
for dyslexic readers.
"""

import os
import time
from typing import Optional
from google import genai
from google.genai import types

# ── Easy-word substitution table ──────────────────────────────────────────
# Common formal → simple Bangla word substitutions
EASY_SUBSTITUTIONS = {
    "বিদ্যালয়": "স্কুল",
    "পুস্তক": "বই",
    "অধ্যয়ন": "পড়া",
    "গৃহ": "বাড়ি",
    "জনক": "বাবা",
    "জননী": "মা",
    "বায়ু": "বাতাস",
    "জল": "পানি",
    "অগ্নি": "আগুন",
    "অন্ধকার": "আঁধার",
    "আলোক": "আলো",
    "শিশু": "বাচ্চা",
    "মানব": "মানুষ",
    "রাত্রি": "রাত",
    "প্রাতঃ": "সকাল",
    "অত্যন্ত": "খুব",
    "অধিক": "বেশি",
    "নিকট": "কাছে",
    "দূরত্ব": "দূরত্ব",
    "পরিবার": "পরিবার",
    "কৃষিনির্ভর": "কৃষি কাজের উপর নির্ভরশীল",
}

SYSTEM_PROMPT = """You are a Bangla reading accessibility expert. You simplify Bangla text for children with dyslexia (ages 6–14).

RULES:
1. Break long sentences into 2-3 shorter, complete sentences to make reading easier.
2. DO NOT change the vocabulary of the sentence unnecessarily. Keep the original words.
3. Your main goal is to help with conjunct consonants (যুক্তবর্ণ). When you encounter a hard word with a conjunct (e.g. "অর্থনীতি" or "বিশ্ববাজারে"):
   - Keep the original word, but immediately follow it with its phonetic syllable breakdown in brackets.
   - Example: "অর্থনীতি (অর-থো-নীতি)"
   - Example: "বিশ্ববাজারে (বিস-শ-বা-জা-রে)"
4. Preserve ALL factual meaning — never add or remove information.
5. Keep the same paragraph structure.

OUTPUT FORMAT:
Return ONLY the simplified Bangla text. No explanations, no English."""

USER_PROMPT_TEMPLATE = """Simplify this Bangla text:
---
{sentence}
---"""


class LLMSimplifier:
    def __init__(self, api_key: Optional[str] = None):
        key = api_key or os.getenv("GEMINI_API_KEY")
        if not key:
            raise ValueError(
                "No Gemini API key found. Set GEMINI_API_KEY environment variable "
                "or pass api_key parameter."
            )
        self.client = genai.Client(api_key=key)
        self.model_name = "gemini-2.5-flash"
        print("Gemini LLM simplifier initialized (gemini-2.5-flash).")

    def simplify_sentence(self, sentence: str, retries: int = 2) -> str:
        """
        Simplify a single complex Bangla sentence.
        Returns the simplified text, or original on failure.
        """
        # First apply quick local substitutions
        text = sentence
        for formal, simple in EASY_SUBSTITUTIONS.items():
            text = text.replace(formal, simple)

        prompt = USER_PROMPT_TEMPLATE.format(sentence=text)

        for attempt in range(retries + 1):
            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_PROMPT,
                        temperature=0.3,
                        max_output_tokens=2048,
                    )
                )
                result = response.text.strip()
                # Guard: if LLM returned empty or English, fall back
                if result and any('\u0980' <= c <= '\u09FF' for c in result):
                    return result
                else:
                    return sentence  # fallback to original
            except Exception as e:
                if attempt < retries:
                    time.sleep(1.5 * (attempt + 1))
                else:
                    print(f"LLM call failed after {retries+1} attempts: {e}")
                    return sentence  # always return something

    def simplify_batch(self, sentences: list[str], delay_s: float = 0.5) -> list[str]:
        """
        Simplify a list of sentences with a small delay between calls
        to avoid rate limiting.
        """
        results = []
        for i, sent in enumerate(sentences):
            simplified = self.simplify_sentence(sent)
            results.append(simplified)
            if i < len(sentences) - 1:
                time.sleep(delay_s)
        return results


if __name__ == "__main__":
    import sys
    key = input("Enter your Gemini API key: ").strip()
    simplifier = LLMSimplifier(api_key=key)

    test_sentences = [
        "বাংলাদেশের অর্থনীতি মূলত কৃষিনির্ভর এবং বিশ্ববাজারে পোশাক রপ্তানিতে উল্লেখযোগ্য ভূমিকা রাখে।",
        "বিশ্বসাহিত্যের ইতিহাসে রবীন্দ্রনাথ ঠাকুরের সৃষ্টিকর্ম এক অনন্য স্থান অধিকার করেছে।",
    ]

    print("\n--- LLM Simplification Test ---\n")
    for sent in test_sentences:
        result = simplifier.simplify_sentence(sent)
        print(f"Original:   {sent}")
        print(f"Simplified: {result}")
        print()
