from bnlp import NLTKTokenizer
import unicodedata
from gtts import gTTS

tokenizer = NLTKTokenizer()

def normalize_bangla(text: str) -> str:
    return unicodedata.normalize("NFC", text)

# Part 9 — tokenizer test
sample_text = "আমি ভালো আছি। তুমি কেমন আছ? আজকে আবহাওয়া খুব সুন্দর।"
sentences = tokenizer.sentence_tokenize(sample_text)

with open("tokenizer_output.txt", "w", encoding="utf-8") as f:
    f.write("--- Tokenizer test ---\n")
    for s in sentences:
        f.write(s + "\n")

# Part 10 — normalizer test
with open("tokenizer_output.txt", "a", encoding="utf-8") as f:
    f.write("\n--- Normalizer test ---\n")
    f.write(normalize_bangla("পরীক্ষা") + "\n")

# Part 11 — gTTS test
tts = gTTS(text="আমি ভালো আছি", lang="bn")
tts.save("test.mp3")

with open("tokenizer_output.txt", "a", encoding="utf-8") as f:
    f.write("\n--- gTTS test ---\n")
    f.write("test.mp3 created successfully\n")

print("All tests done — check tokenizer_output.txt and test.mp3")