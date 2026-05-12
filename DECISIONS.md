# Architecture Decision Records — HR Compass

This document records the key architectural and design decisions made during development,
including the reasoning and trade-offs behind each choice.

---

## ADR-001: Two-Phase AI Pipeline (Keyword Pre-screen → GPT Deep Analysis)

**Status:** Accepted  
**Date:** 2026-01

### Context
Evaluating 50–500 CVs entirely with GPT would be slow and expensive (~$0.15 per 1M tokens × many calls). A pure keyword approach is fast but misses nuance.

### Decision
Use a two-phase pipeline:
- **Phase 1** — `SemanticMatcher` (Jaccard word overlap, zero API cost) runs on every CV and produces a pre-analysis dict with matched/missing skills, seniority, and a 6-factor score.
- **Phase 2** — `LLMAnalyzer` (GPT-4o-mini) receives the pre-analysis as context and focuses on qualitative judgement rather than re-counting skills.

### Consequences
- **Pro:** Cost scales with shortlist size, not total CV count.
- **Pro:** Graceful degradation — if the API key is absent or quota is exhausted, Phase 1 results are still shown.
- **Con:** Phase 1 uses Jaccard (word overlap), not neural embeddings, so synonyms are not matched. Noted as a known limitation.

---

## ADR-002: OpenAI GPT-4o-mini as the LLM

**Status:** Accepted  
**Date:** 2026-01

### Context
Multiple LLM options were considered: OpenAI GPT-4o, GPT-4o-mini, Anthropic Claude, and Google Gemini.

### Decision
Use **GPT-4o-mini** via the `openai` Python SDK.

### Reasons
1. User already had an active OpenAI API key.
2. GPT-4o-mini offers a strong quality/cost balance ($0.15 / 1M input tokens vs $2.50 for GPT-4o).
3. JSON mode (`response_format={"type":"json_object"}`) guarantees parseable structured output — eliminates the need to strip markdown fences.
4. The openai SDK is mature, well-documented, and already the de-facto standard for course-level AI projects.

### Consequences
- **Pro:** Reliable JSON output, low cost.
- **Con:** Vendor lock-in to OpenAI. Migrating to another provider would require rewriting `_call_api`.

---

## ADR-003: Chain-of-Thought System Prompt

**Status:** Accepted  
**Date:** 2026-01

### Context
Initial tests with a direct "score this CV" prompt produced generic, repetitive output. The model would often recycle language across fields.

### Decision
The system prompt (`PROMPT_VERSION = "3.0"`) instructs the model to follow a 5-step reasoning chain before writing JSON:
1. Identify 3-5 critical technical requirements.
2. Decide whether the CV meets, partially meets, or misses each.
3. Consider career trajectory.
4. Estimate interview readiness.
5. Only then synthesise into JSON.

### Consequences
- **Pro:** Output is noticeably more specific and candidate-tailored.
- **Pro:** Prompt version is tracked in the system prompt so future outputs can be compared against a known baseline.
- **Con:** Longer system prompt increases input tokens by ~150 tokens per call (~$0.00002 — negligible).

---

## ADR-004: Output Schema Validation with Auto-Retry

**Status:** Accepted  
**Date:** 2026-01

### Context
Even with JSON mode, the model can occasionally omit required fields or use an invalid `interview_recommendation` value.

### Decision
Every GPT response is validated against `_SCHEMA` (required keys + type checks) and checked for valid recommendations (`Shortlist`, `Consider`, `Decline`). On failure, the call is retried once automatically. After two failures, `None` is returned and the UI falls back to Phase 1 results.

### Consequences
- **Pro:** No malformed data reaches the UI; at most doubles cost of a failed call.
- **Con:** Maximum 2 API calls per candidate in the worst case.

---

## ADR-005: Prompt Injection Protection

**Status:** Accepted  
**Date:** 2026-01

### Context
CV text is untrusted user input. A malicious applicant could embed jailbreak instructions to manipulate the model's output or extract system prompt content.

### Decision
`_sanitize_input()` in `LLMAnalyzer` applies a regex blocklist of known injection patterns (e.g., "ignore all previous instructions", "act as", `<<SYS>>`) before any CV text is sent to the API. Matches are replaced with `[REDACTED]`.

### Consequences
- **Pro:** Mitigates the most common prompt injection patterns documented in OWASP LLM Top 10.
- **Con:** Regex blocklist is not exhaustive; novel jailbreak patterns may bypass it. A more robust approach would use an LLM-based content classifier as a pre-filter.

---

## ADR-006: Streamlit as the UI Framework

**Status:** Accepted  
**Date:** 2025-12

### Context
The project is a course prototype, not a production SaaS. Options considered: Flask + React, FastAPI + React, Streamlit.

### Decision
Use **Streamlit** for the entire frontend and server.

### Reasons
1. Python-only — no JavaScript required, keeping the project within one language.
2. Built-in widgets (file uploader, tabs, progress bars, session state) cover all UI needs.
3. One-command deployment to Streamlit Community Cloud (free tier).
4. Rapid iteration — a UI change is one line of Python.

### Consequences
- **Pro:** Fast development, zero frontend build tooling.
- **Con:** Single-user session model. `candidate_pool.json` is a flat file shared across all sessions — unsuitable for multi-user production. A database backend would be needed to scale.

---

## ADR-007: Flat-File Persistence (JSON)

**Status:** Accepted  
**Date:** 2025-12

### Context
Candidate pool data needs to persist across Streamlit sessions.

### Decision
Use a single `candidate_pool.json` flat file managed by `candidate_pool.py`.

### Reasons
- Zero external dependencies (no database server to provision).
- Sufficient for a single-user prototype.
- Human-readable for debugging.

### Consequences
- **Pro:** Simple, portable, no setup required.
- **Con:** No concurrent-write safety. Multiple simultaneous users would corrupt the file. Documented in Known Limitations.

---

## ADR-008: Token-Aware Input Truncation

**Status:** Accepted  
**Date:** 2026-01

### Context
GPT-4o-mini has a 128k context window, but long CVs increase cost and processing time without proportional quality gain.

### Decision
CV text is hard-capped at **4 000 characters** and job description at **2 000 characters** in `_build_prompt()`. These limits preserve the most relevant content (header + skills sections appear near the start of most CVs) while keeping each call under ~1 500 tokens.

### Consequences
- **Pro:** Predictable per-call cost ceiling.
- **Con:** Very long CVs (portfolios, academic CVs) lose content beyond 4 000 chars. A smarter approach would extract structured sections (experience, skills) before truncating.
