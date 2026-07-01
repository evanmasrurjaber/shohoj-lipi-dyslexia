import os
import sys
from dotenv import load_dotenv
load_dotenv()
from google import genai
from google.genai import types

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

system_prompt = """You are a Bangla text simplification engine for dyslexic children.
Your ONLY job is to take a complex Bangla sentence and output a simpler Bangla sentence.
DO NOT output any English. DO NOT output translations. DO NOT output any explanations or markdown.
Just output the raw simplified Bangla text.
Keep it under 12 words if possible, or split into two very short sentences."""

sentences = [
    "বাংলাদেশের অর্থনীতি মূলত কৃষিনির্ভর এবং বিশ্ববাজারে পোশাক রপ্তানিতে উল্লেখযোগ্য ভূমিকা রাখে",
    "বিশ্বসাহিত্যের ইতিহাসে রবীন্দ্রনাথ ঠাকুরের সৃষ্টিকর্ম এক অনন্য স্থান অধিকার করেছে"
]

print("Testing raw LLM prompt...")
for s in sentences:
    print(f"In:  {s}")
    prompt = f"Simplify:\n{s}"
    res = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=0.1,
            max_output_tokens=256
        )
    )
    print(f"Out: {res.text.strip()}\n")
