# Shohoj Lipi (সহজ লিপি)

**Enhancing Bangla Text Accessibility for Dyslexic Readers through LLM-Driven Simplification and Adaptive Typography**

A submission for the SciBlitz AI Challenge 2026 (IEEE CUET), Track C: Education & Accessibility. Shohoj Lipi takes any Bangla text and transforms it into a dyslexia-friendly reading experience: it scores how difficult the text is, simplifies the complex parts with an LLM, and re-renders the result in an accessible layout, with a before/after readability score to show the improvement is real.

## Inspiration

Standard Bangla typography is hard on readers with dyslexia: dense conjunct consonants, tight character spacing, serif-heavy fonts, and long unbroken sentences create visual crowding. A 2015 Dhaka study found a 9.02% dyslexia prevalence rate among grade-4 students (n=133); a 2022 global meta-analysis found a pooled prevalence of 7.10% (95% CI 6.27-7.97%).[^1] No accessible, AI-powered Bangla reading tool currently exists.

The closest published work, the AAAI 2021 *BengaliReadability* paper (Chakraborty et al.), provides only a readability classifier — no simplification, no rendering. Shohoj Lipi combines readability scoring, LLM-based simplification, and accessible rendering into one pipeline.

## Key Features

- **Readability Scoring**: composite scorer (CC-density, sentence/word length, rare-word ratio) mapping input to an Easy / Medium / Hard tier
- **Sentence-Level Routing**: fine-tuned BanglaBERT classifies each sentence Simple/Complex before deciding whether it needs simplification
- **LLM Simplification**: complex sentences rewritten by Gemini into shorter, simpler Bangla, guided by a 3,396-word easy-word list, preserving factual meaning
- **Accessible Rendering**: adjustable font size, generous line height, alternating line shading, optional syllable-boundary dots
- **Text-to-Speech**: backend TTS with an in-browser fallback
- **Diff Highlighting**: words changed during simplification are visually marked
- **Copy & Download**: simplified text can be copied or saved as `.txt`
- **Evaluation Suite**: CC-density reduction, vocabulary-simplicity gain, a Bangla Flesch-Kincaid-style grade estimate, and statistical significance testing across the eval corpus

## Tech Stack

- **Frontend**: React 18, Vite, Tailwind CSS
- **Backend**: FastAPI, Uvicorn
- **NLP Preprocessing**: `bnlp-toolkit`
- **Readability Scoring**: rule-based composite scorer, calibrated against a labelled eval corpus
- **Sentence Routing**: fine-tuned `csebuetnlp/banglabert_small` (ONNX), backed by a CC-density heuristic
- **LLM Simplification**: Gemini API via `google-genai`
- **Text-to-Speech**: gTTS, with Web Speech API fallback
- **Evaluation**: pandas, scipy, BERTScore
- **Deployment (planned)**: Hugging Face

## The Pipeline

1. **Input & Preprocessing**: Unicode NFC normalisation, sentence tokenisation (`bnlp`)
2. **Readability Scoring**: composite score → Easy / Medium / Hard tier
3. **Sentence Routing**: BanglaBERT classifies each sentence Simple/Complex
4. **LLM Simplification**: Complex sentences sent to Gemini; Simple ones pass through unchanged
5. **Re-Scoring**: simplified text scored the same way, producing a before/after delta
6. **Accessible Rendering**: dyslexia-optimised layout, TTS, syllable dots, diff highlighting, copy/download

## Running the Application

### Prerequisites

- **Python 3.9+** (for the backend and ML pipeline)
- **Node.js 18+** (for the frontend)

### Backend

1. Create a `.env` file in the root directory and add your Gemini API key:
   ```env
   GEMINI_API_KEY=your_api_key_here
   ```

2. Setup and run the server:
```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS/Linux
pip install -r requirements.txt
uvicorn main:app --reload --port 8001
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```



### Evaluation Pipeline

With the backend running:

```bash
cd data
python split_passages.py       # curate passages (edit constants at top first)
python run_eval.py             # run the live pipeline over eval_passages.csv, resumable
python cc_after.py             # CC-density before/after
python vocab_simplicity.py     # easy-word-list vocabulary coverage before/after
python readability_formula.py  # Bangla Flesch-Kincaid-style grade estimate
python significance_test.py    # Wilcoxon signed-rank test + correlation analysis
```

## Project Structure

```
.
├── frontend/    React + Vite + Tailwind SPA
├── backend/     FastAPI server (main.py, simplify.py)
├── ml/          Readability scoring, sentence routing, syllabification
├── data/        Dataset curation and evaluation pipeline
└── docs/        Report, evaluation outputs, Model and Data Card
```

## Status

Implemented: FastAPI backend with all core endpoints, the rule-based readability scorer (calibrated on 935 passages), the fine-tuned sentence-router model (85.1% validation accuracy, exported to ONNX), the full frontend 3-panel UI, syllable dots, TTS with fallback, and the evaluation pipeline scripts.


## Future Improvements

- Human readability rating study (native Bangla readers, Likert scale)
- Improve the syllabifier
- Test generalization to non-textbook domains

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgements

- BengaliReadability dataset and CC algorithm — Chakraborty et al., AAAI 2021 ([github.com/tafseer-nayeem/BengaliReadability](https://github.com/tafseer-nayeem/BengaliReadability))
- BanglaBERT — csebuetnlp, NAACL 2022
- NCTB-QA dataset (arXiv 2025)

---

[^1]: Muzahid Ali et al., "Prevalence of Dyslexia in Primary School in Dhaka," *International Journal of Advanced Research*, 2015 ([journalijar.com](https://www.journalijar.com/article/7418/prevalence-of-dyslexia-in-primary-school-in-dhaka:-its-effects-on-children%E2%80%99s-academic-and-social-life/)); global figure from "Prevalence of Developmental Dyslexia in Primary School Children: A Systematic Review and Meta-Analysis," 2022 ([PMC8870220](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC8870220/)).
