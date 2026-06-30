# 🧠 Shohoj Lipi — DEV-A Game Plan
> **SciBlitz AI Challenge 2026 | IEEE CUET | Track C — Education & Accessibility**  
> *Your Role: **Member A — AI/NLP Lead***

---

## 📌 Project Overview (Quick Ref)

| Item | Detail |
|---|---|
| **App Name** | Shohoj Lipi (সহজ লিপি) |
| **Problem** | 10–15% of Bangladeshi school-age children have dyslexia; no AI-powered Bangla reading tool exists |
| **Stack** | BanglaBERT + Qwen2.5-Instruct / GPT-4o-mini + FastAPI + React + Tailwind |
| **Deadline** | Day 7 — July 8, 2026 by 11:59 PM BST |
| **Competition** | SciBlitz AI Challenge 2026, IEEE CUET |
| **Track** | C — Education & Accessibility |
| **GitHub Repo** | `shohoj-lipi-dyslexia` (public from Day 7, commits from Day 1) |

---

## 👤 Your Role: Member A — AI/NLP Lead

**Full Ownership:**
- ✅ BanglaBERT fine-tuning (readability classifier + sentence tagger)
- ✅ LLM simplification pipeline and prompt engineering
- ✅ BERTScore evaluation
- ✅ Model export to HuggingFace Hub
- ✅ Final review of Methodology + Results sections of report

---

## 🏗️ System Architecture (Your Stage)

The pipeline has 4 stages. You own **Stages 2 & 3**:

```
[Stage 1 - Member C]     [Stage 2 - YOU]              [Stage 3 - YOU]            [Stage 4 - Member B]
Input & Preprocessing → Readability Classification → LLM Simplification     → Accessible Rendering
     (bnlp)               (BanglaBERT)                (Qwen2.5 / GPT-4o-mini)    (React + CSS)
```

### Stage 2 — Readability Classification
- Fine-tuned **BanglaBERT** assigns:
  - Per-sentence: `Simple` or `Complex`
  - Full passage: `Easy / Medium / Hard` + numeric readability score

### Stage 3 — LLM Simplification
- Complex sentences → LLM prompt → simplified sentence
- Simple sentences → **pass through unchanged** (no LLM call)
- Prompt constraints: shorter clauses, prefer the 3,396 easy words, avoid rare conjuncts

---

## 📦 Datasets You Need (Download Day 1)

| Dataset | Size | Your Use Case | Source |
|---|---|---|---|
| BengaliReadability — Document corpus | 618 docs | Fine-tune BanglaBERT (3-class grade tier) | `github.com/tafseer-nayeem/BengaliReadability` |
| BengaliReadability — Sentence corpus | 96,000+ sentences | Sentence-level complexity tagger (Simple/Complex) | Same repo |
| Easy-word list | 3,396 words | Vocabulary constraint in LLM prompts | Same repo |
| Consonant-conjunct algorithm | 341 validated words | CC-density metric computation | Same repo |
| Pronunciation dictionary | 67,000+ words | Syllable segmentation (for TTS + /syllabify endpoint) | Same repo |

> **License:** MIT — public, safe to use in competition.

---

## 🛠️ Your Tech Stack

| Tool | Purpose |
|---|---|
| `csebuetnlp/banglaBERT` via HuggingFace | Base model for fine-tuning |
| `transformers` (HuggingFace) | Fine-tuning framework |
| `Qwen2.5-3B-Instruct` (local GGUF, 4-bit) | Primary LLM for simplification |
| `GPT-4o-mini` API | Fallback LLM if Qwen quality is poor |
| Google Colab T4 | Training environment (free tier) |
| `scikit-learn` | Accuracy / F1 metrics |
| `bert-score` | Semantic fidelity evaluation |
| HuggingFace Hub | Model hosting + inference API |

---

## 📅 7-Day Task Breakdown — DEV-A Only

### ✅ DAY 1 — Foundation & Data (July 2)

**Objectives:** Setup environment, load BanglaBERT, verify training loop

- [ ] Clone BengaliReadability repo
- [ ] Audit document corpus (618 docs) — confirm train/val splits
- [ ] Audit sentence corpus (96K) — note class distribution
- [ ] Set up Colab notebook: load `csebuetnlp/banglaBERT`
- [ ] Verify fine-tuning loop runs on **10 sample rows** (sanity check before full train)
- [ ] Commit at least one file to GitHub

**📤 Commit:** Colab notebook with BanglaBERT loaded + 10-row fine-tune test running

---

### ✅ DAY 2 — Classifier Training (July 3)

**Objectives:** Trained BanglaBERT classifiers for both document-level and sentence-level

#### Document-Level Classifier (Grade Tier: Easy / Medium / Hard)
- [ ] Fine-tune BanglaBERT on **618 docs**
  - 80/20 train/val split
  - 5 epochs
  - AdamW, lr = `2e-5`
  - 3-class output head
- [ ] Log accuracy + F1 per class
- [ ] Save best checkpoint to `/models`

#### Sentence-Level Complexity Tagger (Simple / Complex binary)
- [ ] Fine-tune BanglaBERT on **96K sentence corpus**
  - Can sub-sample to **30K** for speed (still large enough)
  - Binary classification
- [ ] Save best checkpoint

**📤 Commit:** Both trained checkpoints in `/models`, training logs/metrics

---

### ✅ DAY 3 — LLM Simplification Pipeline (July 4)

**Objectives:** LLM simplification working end-to-end; write `/simplify` endpoint

#### Prompt Design
```
System: You are a Bangla language accessibility expert. Your job is to 
simplify complex Bangla sentences for children with dyslexia. 
Prefer words from this list: [snippet of 3,396 easy words]. 
Keep clauses short. Avoid rare conjunct consonants.

User: Simplify this sentence: {sentence}
```

- [ ] Design and iterate on the simplification prompt
- [ ] Test on **20 complex sentences** from eval corpus
- [ ] Compare **Qwen2.5-3B** (local Colab) vs **GPT-4o-mini** (API) on quality
- [ ] Choose primary LLM based on quality comparison
- [ ] Write `/simplify` endpoint wrapping the chosen LLM
- [ ] Add **sentence-level routing logic:**
  - `complexity_tag == Simple` → skip LLM, pass through
  - `complexity_tag == Complex` → send to LLM

**📤 Commit:** `/simplify` endpoint passing 20 test cases

---

### ✅ DAY 4 — Full Pipeline Integration + BERTScore Eval (July 5)

**Objectives:** BERTScore evaluation, prompt iteration

- [ ] Run **BERTScore** on 50 simplified passages:
  - Original vs. Simplified
  - Model: `bert-base-multilingual-cased`
  - Target: **F1 ≥ 0.82**
- [ ] If BERTScore < 0.80 → iterate on prompt
- [ ] Add **5 few-shot examples** in prompt for worst-performing passages
- [ ] Add **3 preloaded example inputs** (easy/medium/hard) as "Try an example" buttons (coordinate with Member B)

**📤 Commit:** BERTScore results CSV/notebook in `/docs`

---

### ✅ DAY 5 — Evaluation & Final Metrics (July 6)

**Objectives:** All quantitative metrics finalized

- [ ] Compute final **classifier accuracy/F1** on held-out document corpus
- [ ] Compare vs. AAAI 2021 paper baseline
- [ ] Compute **mean grade-level drop** across all 200 eval passages
- [ ] Compile full evaluation table (all 6 metrics — see below)
- [ ] Deliver final numbers to **Member D** for report

**📤 Commit:** Complete eval metrics + numbers in `/docs`

---

### ✅ DAY 6 — Model Export & Demo Prep (July 7)

**Objectives:** Model live on HuggingFace Hub; demo friction removed

- [ ] Export BanglaBERT model to **HuggingFace Hub** (private first, verify, then public)
- [ ] Test inference via Hub API (ensure cold-start works)
- [ ] Verify 3 preloaded example inputs work on live Vercel URL
- [ ] Review final Methodology + Results sections of the report

**📤 Commit:** HuggingFace Hub model card link in README

---

### ✅ DAY 7 — Submission Day (July 8)

**Deadline: 11:59 PM BST**

- [ ] Review + proofread Methodology section of report
- [ ] Review + proofread Results section of report
- [ ] Verify all numbers match eval notebook output
- [ ] Push final **Model Card** to `/docs`
- [ ] Cross-verify all 5 submission deliverables (with Member D)

---

## 📊 Evaluation Metrics (Your Responsibility to Compute)

| # | Metric | What It Measures | How to Compute |
|---|---|---|---|
| 1 | **Classifier Accuracy / F1** | Grade tier prediction quality | `sklearn` metrics on held-out 20% of 618-doc corpus; compare to AAAI 2021 baseline |
| 2 | **Sentence-Level Accuracy** | Simple vs. Complex sentence classification | BanglaBERT fine-tuned on 96K corpus; same paper baseline available |
| 3 | **Readability Score Delta** | Did simplification lower reading difficulty? | Classifier on original vs. simplified; report mean grade-level drop across 100 test passages |
| 4 | **CC-Density Reduction** | Conjunct-consonant crowding reduced? | Apply paper's CC algorithm to original vs. simplified; report mean CC count per 100 chars |
| 5 | **BERTScore (Semantic Fidelity)** | Does simplified text preserve meaning? | `bert-score` with `bert-base-multilingual-cased`; target **F1 ≥ 0.82** |
| 6 | **Human Readability Rating** | Does it feel easier to read? | 5-point Likert scale by 3–5 native Bangla readers on 30 sample transformations (Member D organizes) |

---

## ⚠️ Risk Register — Risks That Affect You

| Risk | Severity | Day | Your Mitigation |
|---|---|---|---|
| LLM output poor for complex Bangla conjuncts | **High** | Day 3 | Switch to GPT-4o-mini API; add few-shot examples to prompt; fall back to rule-based shortening |
| BanglaBERT fine-tune fails on small 618-doc corpus | **Med** | Day 2 | Data augmentation via BanglaT5 (back-translation bn→en→bn) to 3× corpus size; OR use XGBoost on CC-density + sentence-length features as backup |
| BERTScore < 0.80 after simplification | **Med** | Day 4 | Add few-shot examples; adjust temperature; tighten easy-word constraint in prompt |

---

## 🔗 Key Resources for DEV-A

| Resource | URL |
|---|---|
| BengaliReadability Dataset | `github.com/tafseer-nayeem/BengaliReadability` |
| BanglaBERT (HuggingFace) | `huggingface.co/csebuetnlp/banglaBERT` |
| Qwen2.5-3B-Instruct GGUF | `huggingface.co/Qwen/Qwen2.5-3B-Instruct-GGUF` |
| NCTB-QA Passages | `arXiv:2603.05462` |
| bert-score (pip) | `pip install bert-score` — use `bert-base-multilingual-cased` |
| bnlp Toolkit | `pip install bnlp-toolkit` |

---

## 👥 Team Interface Points (Who You Hand Off To)

| Handoff | To Whom | When |
|---|---|---|
| BanglaBERT checkpoint (for `/classify` endpoint) | **Member C** | End of Day 2 |
| Simplification quality comparison results (Qwen vs GPT) | **Member C** | End of Day 3 |
| `/process` endpoint integration (classify + simplify chained) | **Member C** | Day 4 |
| 3 preloaded example inputs (easy/medium/hard Bangla text) | **Member B** | Day 6 |
| Final eval numbers (all 6 metrics) | **Member D** | End of Day 5 |
| Final model card | **Member D** | Day 7 |

---

## 📋 Submission Checklist (Final Day 7)

- [ ] ✅ Live URL (Vercel)
- [ ] ✅ Report PDF (8 pages)
- [ ] ✅ GitHub link (public, commits from Day 1)
- [ ] ✅ Demo video (YouTube unlisted)
- [ ] ✅ Model & Data Card PDF

---

## 📝 Report Sections You Own

| Section | Pages | Your Content |
|---|---|---|
| **Methodology & AI/ML Approach** | 2.5 | BanglaBERT architecture, hyperparameters (AdamW, lr=2e-5, 5 epochs, 80/20 split), LLM prompt template, sentence routing logic, dataset stats, CC-density computation |
| **Results** | 2.5 | Classifier accuracy/F1 vs. AAAI 2021 baseline, mean grade-level drop across 200 passages, BERTScore distribution, CC-density before/after |
| **Review** | — | Final proofread of Methodology + Results on Day 7 |

---

## 🎯 Success Criteria for DEV-A

By the end of the competition, you should have:

1. ✅ A **fine-tuned BanglaBERT** classifier with accuracy/F1 **better than or comparable to the AAAI 2021 baseline**
2. ✅ A working **LLM simplification pipeline** that routes simple/complex sentences correctly
3. ✅ **BERTScore F1 ≥ 0.82** across 50 test passages
4. ✅ Mean **grade-level drop** measurable across 200 eval passages
5. ✅ Model publicly hosted on **HuggingFace Hub** with a model card
6. ✅ All numbers verified and handed to Member D before Day 7 deadline

---

> *"Every child deserves to read their own textbook."*  
> — Shohoj Lipi | পাঠ সহায় | SciBlitz AI Challenge 2026
