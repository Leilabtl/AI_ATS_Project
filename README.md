# HR Compass — AI Talent Navigation

An AI-powered Applicant Tracking System (ATS) that combines a fast **keyword pre-screening layer**
with a **GPT-4o-mini semantic deep analysis layer** to rank candidates, detect bias, and generate
professional recruitment reports.

> **Course:** AI In Practice · XAMK · Spring 2026
> **Developer:** Leila Baratlou
> **Version:** 2.5.0 | **Status:** Fully Operational

---

## How the AI Matching Works

This project intentionally uses **two different levels of language understanding**, each chosen
for a specific reason.

### Phase 1 — Keyword Pre-Screening (Jaccard Similarity)

The first pass uses **Jaccard similarity** — a word-overlap score between the CV and the job
description. It also performs exact-match skill extraction against a curated keyword dictionary
(Python, Docker, AWS, SQL, etc.) and detects seniority level via keyword rules.

```
Jaccard Score = |words in CV ∩ words in JD| / |words in CV ∪ words in JD|
```

**Why keyword matching here?**
- Zero API cost — can screen hundreds of CVs instantly
- Deterministic and fully explainable — every score can be traced back to specific word matches
- Sufficient for a fast first filter: a CV with no overlap with the JD genuinely isn't a match

**Limitation:** Jaccard has no understanding of meaning. "ML engineer" and
"machine learning specialist" score zero overlap even though they mean the same thing.
This is why Phase 2 exists.

### Phase 2 — Semantic Deep Analysis (GPT-4o-mini)

The top candidates from Phase 1 are passed to **OpenAI GPT-4o-mini** for genuine semantic
understanding. GPT reads the full CV and job description and reasons about:

- Whether skills in the CV *semantically* satisfy JD requirements (including synonyms and
  adjacent technologies)
- Career trajectory — is this role a natural next step for this candidate?
- Interview readiness — would this person need significant ramp-up?
- Specific, actionable skill gaps with concrete learning paths

This is **true semantic analysis**: the model understands context, intent, and meaning — not
just word overlap.

**Why GPT here and not in Phase 1?**
Each GPT call has a cost (~$0.001 per CV). Running it on every CV in a 500-CV batch is
expensive. The keyword layer acts as a cheap filter so GPT is only called on candidates who
pass a minimum relevance threshold.

### The Combined Score

The final ranking combines both layers:

```
Final Score =
  0.35 × Jaccard Similarity       (Phase 1 — word overlap)
+ 0.25 × Skills Match             (Phase 1 — keyword extraction)
+ 0.15 × Experience Relevance     (Phase 1 — keyword heuristics)
+ 0.15 × Keyword Density          (Phase 1 — term concentration)
+ 0.05 × Culture Fit              (Phase 1 — soft-skill keywords)
+ 0.05 × Seniority Alignment      (Phase 1 — level detection)

GPT Analysis    →  executive summary, gap roadmap, interview recommendation
                   (qualitative layer on top of the numeric score)
```

---

## AI Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        HR Compass Pipeline                      │
│                                                                 │
│  PDF CVs ──► pdfplumber ──► clean_text()                        │
│                                    │                            │
│                          ┌─────────▼──────────┐                │
│                          │  Phase 1 (free)     │                │
│                          │  SemanticMatcher    │                │
│                          │  · Jaccard sim.     │  ← keyword     │
│                          │  · Skill extraction │    matching    │
│                          │  · Seniority detect │                │
│                          │  · 6-factor score   │                │
│                          └─────────┬──────────┘                │
│                                    │  pre_analysis dict         │
│                          ┌─────────▼──────────┐                │
│                          │  Phase 2 (GPT API)  │                │
│                          │  LLMAnalyzer        │  ← semantic    │
│                          │  · CoT reasoning    │    analysis    │
│                          │  · Synonym aware    │                │
│                          │  · JSON mode output │                │
│                          │  · Schema validate  │                │
│                          │  · Auto-retry (×1)  │                │
│                          └─────────┬──────────┘                │
│                                    │  llm_analysis dict         │
│                          ┌─────────▼──────────┐                │
│                          │  Results & Reports  │                │
│                          │  PDF · CSV · Email  │                │
│                          │  Market Intelligence│                │
│                          └─────────────────────┘               │
└─────────────────────────────────────────────────────────────────┘
```

---

## Key Features

| Feature | Description |
|---|---|
| **Two-phase AI pipeline** | Phase 1: fast Jaccard keyword pre-screening · Phase 2: GPT semantic deep analysis |
| **Explainable scoring** | 6-factor weighted formula with per-factor breakdown shown in UI |
| **Bias detection** | Flags name-based, age-related, and gender-coded language |
| **GPT semantic summary** | Candidate-specific narrative generated by `gpt-4o-mini` — understands synonyms and context |
| **Skill gap roadmaps** | Prioritised learning paths with time estimates |
| **Interview prep** | Auto-generated focus areas per candidate |
| **Market Intelligence** | Aggregate GPT analysis across the full candidate pool — identifies talent supply gaps and JD optimisation tips |
| **PDF & CSV reports** | One-click professional report generation |
| **Email templates** | BCC-ready shortlist / longlist / rejection templates |
| **Batch processing** | 50–500+ CVs at ~1–2 s each |

---

## Prompt Engineering Decisions

The GPT layer uses several deliberate techniques to improve output quality:

| Technique | Implementation |
|---|---|
| **Chain-of-thought** | System prompt instructs GPT to reason through 5 steps before writing JSON — reduces hallucinations |
| **JSON mode** | `response_format={"type":"json_object"}` guarantees parseable output every time |
| **Dynamic context injection** | Pre-computed matched/missing skills and scores injected into the user prompt so GPT focuses on nuanced semantic judgement, not re-counting keywords |
| **Token-aware truncation** | CV capped at 4 000 chars, JD at 2 000 chars to control cost |
| **Output schema validation** | Every response validated against a strict field/type schema; retried once on failure |
| **Prompt injection protection** | CV text sanitised before sending — known jailbreak patterns replaced with `[REDACTED]` |
| **Cost monitoring** | Token usage and estimated USD cost tracked per session and shown in the Settings tab |
| **Prompt versioning** | `PROMPT_VERSION = "3.0"` embedded in the system prompt for reproducibility |

---

## Technical Stack

| Layer | Technology |
|---|---|
| UI / server | Streamlit (Python) |
| PDF parsing | pdfplumber |
| Phase 1 NLP | Jaccard similarity + keyword extraction (`embedding.py`) |
| Phase 2 LLM | OpenAI `gpt-4o-mini` via openai SDK — semantic understanding |
| Report generation | ReportLab (PDF), pandas (CSV) |
| Data persistence | JSON flat files |
| Environment config | python-dotenv |
| Containerisation | Docker (`Dockerfile` included) |
| Testing | pytest — 69 tests, all passing |

---

## Project Structure

```
AI_ATS_Project/
├── streamlit_app.py      # Main UI and orchestration
├── matcher.py            # EnhancedMatcher — scoring formula + bias detection
├── embedding.py          # SemanticMatcher — Jaccard similarity + keyword extraction (Phase 1)
├── llm_analyzer.py       # LLMAnalyzer — GPT-4o-mini semantic analysis (Phase 2)
├── report_generator.py   # PDF, CSV, and email report generation
├── candidate_pool.py     # Persistent multi-job candidate storage
├── advanced_features.py  # Diversity metrics, interview questions, predictive scores
├── parser.py             # PDF text + email extraction
├── preprocessing.py      # Text normalisation
├── DECISIONS.md          # Architecture Decision Records (8 ADRs)
├── Dockerfile            # Container build for deployment
├── tests/
│   └── test_matching.py  # 69 unit tests (pytest)
├── requirements.txt
├── .env.example          # Template — copy to .env and add your key
└── .gitignore
```

---

## Local Setup

### 1. Clone the repository

```bash
git clone https://github.com/Leilabtl/AI_ATS_Project.git
cd AI_ATS_Project
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

```bash
cp .env.example .env
# Open .env and paste your OpenAI API key
```

### 4. Run the app

```bash
streamlit run streamlit_app.py
# App opens at http://localhost:8501
```

### 5. Run tests

```bash
python -m pytest tests/ -v
# 69 tests, all passing
```

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `OPENAI_API_KEY` | Yes (for GPT semantic analysis) | OpenAI API key. Without it the app still works using Phase 1 keyword matching only. |

The app loads `.env` automatically on startup. The keyword pre-screening pipeline works fully
without an API key — GPT semantic analysis is additive.

---

## Deployment

### Docker

```bash
docker build -t hr-compass .
docker run -p 8501:8501 -e OPENAI_API_KEY=sk-... hr-compass
```

### Streamlit Community Cloud (recommended — free)

1. Push code to your GitHub `main` branch.
2. Go to [share.streamlit.io](https://share.streamlit.io) → **New app**.
3. Select repo `Leilabtl/AI_ATS_Project`, branch `main`, file `streamlit_app.py`.
4. Under **Advanced settings → Secrets**, add:
   ```toml
   OPENAI_API_KEY = "sk-..."
   ```
5. Set Python version to **3.11**.
6. Click **Deploy**.

---

## Safety & Responsible AI

| Measure | Implementation |
|---|---|
| Prompt injection resistance | `LLMAnalyzer._sanitize_input()` strips known jailbreak patterns from CV text before sending to GPT |
| Output schema validation | Every GPT response validated against a strict field/type schema before use |
| Graceful fallback | If GPT fails or key is absent, Phase 1 keyword results are shown instead |
| Bias detection | Flags name-, age-, and gender-coded language in CVs for recruiter awareness |
| Cost monitoring | Token usage and estimated USD cost shown live in the Settings tab |
| Secrets management | API key loaded from `.env` (gitignored) or Streamlit Secrets — never hardcoded |
| Input size guardrails | CV truncated at 4 000 chars, JD at 2 000 chars; warnings logged when inputs exceed thresholds |
| Rate limiting | Minimum 0.5 s interval enforced between API calls to prevent accidental bursts |

---

## Known Limitations & Future Work

- **Phase 1 semantic gap:** Jaccard similarity misses synonyms. A future version could replace it with `sentence-transformers` for true neural embedding similarity, removing the need for a two-phase approach.
- **GPT cost scaling:** For very large batches (500+ CVs), a stricter Phase 1 threshold (e.g. top 50 only) would reduce cost significantly.
- **PDF parsing:** Fails on scanned / image-only PDFs. Adding OCR (e.g. Tesseract) would handle these.
- **Single-user:** `candidate_pool.json` is a shared flat file. A database backend (SQLite or PostgreSQL) would be needed for multi-user deployment.
