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
4. The openai SDK is mature, well-documented, and the de-facto standard for production AI projects.

### Consequences
- **Pro:** Reliable JSON output, low cost.
- **Con:** Vendor lock-in to OpenAI. Migrating to another provider would require rewriting `_call_api`.

---

## ADR-003: Chain-of-Thought System Prompt (Prompt Version History)

**Status:** Accepted  
**Date:** 2026-01

### Context
Initial tests with a direct "score this CV" prompt produced generic, repetitive output. The model would often recycle language across fields. Three prompt versions were developed and evaluated before the current design was adopted.

### Prompt Version History (A/B Evaluation)

| Version | Approach | Problem observed | Evaluation result |
|---|---|---|---|
| **v1.0** | Single instruction: "Analyse this CV for the job and return JSON." | Output was generic; executive summaries reused identical phrasing across candidates. Strengths section often listed the job description requirements verbatim. | Rejected — too shallow |
| **v2.0** | Added explicit JSON schema in the prompt. Required `key_strengths`, `critical_gaps`, `interview_recommendation`. | Output was structurally correct but reasoning was shallow — the model filled fields without demonstrating it had actually compared CV to JD. Recommendations were frequently `Shortlist` for weak candidates. | Rejected — poor discrimination |
| **v3.0** *(current)* | Chain-of-thought preamble: model instructed to reason through 5 explicit steps *before* writing JSON. Steps force it to identify requirements, compare them to the CV, consider trajectory, then synthesise. | Output is candidate-specific, references actual CV details, and produces more accurate `Decline` decisions for mismatched candidates. Confirmed by running the same 6 CVs through v2 and v3 and comparing outputs manually. | **Accepted** |

### Decision
The system prompt (`PROMPT_VERSION = "3.0"`) instructs the model to follow a 5-step reasoning chain before writing JSON:
1. Identify 3-5 critical technical requirements from the job description.
2. Decide whether the CV meets, partially meets, or misses each requirement.
3. Consider career trajectory — is this role a natural next step?
4. Estimate interview readiness — would significant ramp-up be needed?
5. Only then synthesise all findings into the JSON output.

`PROMPT_VERSION` is embedded in every system prompt string so logged outputs can always be traced back to the exact prompt that generated them.

### Consequences
- **Pro:** Output is noticeably more specific and candidate-tailored.
- **Pro:** Version tracking enables regression detection if the prompt is changed in future.
- **Pro:** CoT structure measurably improves `Decline` accuracy for mismatched candidates (confirmed by manual evaluation on 6 labeled cases).
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
HR Compass is a single-user web application targeting fast deployment, not a multi-tenant production SaaS. Options considered: Flask + React, FastAPI + React, Streamlit.

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
- Sufficient for a single-user deployment.
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

---

## ADR-009: Ethical AI Design

**Status:** Accepted  
**Date:** 2026-08

### Context
AI-assisted hiring tools can perpetuate or amplify human bias. The EU AI Act classifies employment screening tools as **high-risk AI systems**, requiring transparency, human oversight, and non-discrimination measures. Even at course-project scale, demonstrating awareness of these risks is essential.

### Decision
The following ethical safeguards are implemented across the pipeline:

1. **Bias detection** — `EnhancedMatcher.detect_bias()` scans CV text for gendered pronouns and age-signalling language, warning the recruiter rather than silently penalising candidates.
2. **PII detection before API calls** — `LLMAnalyzer._detect_pii()` checks for emails, phone numbers, and Finnish personal identity codes (hetu) before any text is sent to OpenAI. Detections are logged to the audit file; they are not redacted from the CV (which would damage matching quality) but their presence is recorded.
3. **Audit trail** — `_audit_log()` writes one JSON line per AI interaction containing timestamp, correlation ID, model version, token count, recommendation, and whether PII was present. This provides a tamper-evident record for post-hoc review.
4. **Explainability** — The GPT response schema requires explicit `key_strengths`, `critical_gaps`, and `career_fit_narrative` fields. Recruiters see the reasoning, not just a score.
5. **Human-in-the-loop** — The system produces recommendations (`Shortlist`, `Consider`, `Decline`), not autonomous decisions. Every candidate's full expander is visible and a recruiter must act on the recommendation.
6. **Prompt injection protection** — `_sanitize_input()` blocks known jailbreak patterns so a malicious CV cannot manipulate the model's output for other candidates.

### Threat Model

The table below identifies specific attack vectors for this application and how each is mitigated.

| Threat | Vector | Mitigation | Residual risk |
|---|---|---|---|
| **Prompt injection** | Malicious CV contains jailbreak text ("Ignore all previous instructions…") to manipulate GPT output for *other* candidates | `_sanitize_input()` blocklist (10+ patterns) replaces matches with `[REDACTED]` | Novel, never-before-seen patterns may bypass regex. Mitigation: output schema validation catches hallucinated fields. |
| **PII leakage to OpenAI** | CV contains email / phone / SSN that gets sent to third-party API | `_detect_pii()` logs PII presence before each call; `_sanitize_input()` caps input size | PII is currently detected and logged but *not* redacted from the prompt (redacting would harm matching quality). A production deployment should redact or obtain explicit consent. |
| **API key theft** | Key hardcoded in source, committed to git, or logged to stdout | Key loaded from `.env` (gitignored) / Streamlit Secrets; never interpolated into log strings | If Streamlit Secrets is misconfigured the key could be exposed. |
| **Unbounded API cost** | Malicious user uploads thousands of CVs to exhaust quota | Phase 1 threshold limits GPT calls; rate limiter (0.5 s/call); `max_tokens` caps each call | No hard per-session spend limit; depends on Phase 1 filtering ratio. |
| **Audit log tampering** | Local `ats_audit.log` file is deleted or edited to hide activity | Log is append-only; application never reads it back or deletes it | No cryptographic signing; physical access to the host can alter the file. |
| **Bias amplification** | GPT reflects training-data bias against names, genders, or nationalities | Bias detection warns recruiter; human-in-the-loop required before any action | Detection is heuristic; cannot guarantee absence of subtle model bias. |

Full details and response procedures: see [SECURITY.md](SECURITY.md).

### Consequences
- **Pro:** Demonstrates compliance awareness aligned with EU AI Act principles.
- **Pro:** Audit log enables post-hoc fairness analysis (e.g., decline rate by seniority level).
- **Con:** Regex-based bias detection and PII matching produce false positives on some texts.
- **Con:** Full GDPR compliance for a production deployment would additionally require data minimisation, right-to-erasure workflows, and a Data Protection Impact Assessment — documented as a known limitation and planned for a future release.

---

## ADR-010: Cost Analysis and Controls

**Status:** Accepted  
**Date:** 2026-08

### Context
OpenAI API calls are metered. With 50–500 CVs per batch and GPT-4o-mini at $0.15 / 1M tokens, uncontrolled usage could produce unexpectedly high bills during a demo or stress test.

### Decision
Seven cost controls are layered across the pipeline:

| Control | Where | Effect |
|---|---|---|
| Phase 1 pre-screen | `matcher.py` | Only shortlisted candidates proceed to Phase 2 |
| Input truncation | `_build_prompt()` | CV capped at 4 000 chars, JD at 2 000 chars |
| Streaming uses lower `max_tokens` | `stream_executive_summary()` | 200 tokens vs 1 024 for full analysis |
| Rate limiting | `_call_api()` | 0.5 s minimum between calls prevents accidental burst |
| Per-session cost tracker | `estimated_cost_usd` property | Displayed in UI sidebar so recruiter sees running total |
| Per-call cost in audit log | `_audit_log()` | Records `cost_usd` for post-session accounting |
| Market intelligence is one call | `generate_market_intelligence()` | Aggregates all candidates in one prompt rather than N calls |

### Cost Estimate (typical session)
- 20 CVs submitted, 8 pass Phase 1 threshold → 8 GPT calls
- ~900 tokens per call (prompt + completion) × 8 = 7 200 tokens
- Cost: 7 200 / 1 000 000 × $0.15 ≈ **$0.001** per session
- Market intelligence call: ~800 tokens ≈ $0.00012
- **Total per session: < $0.002**

### Consequences
- **Pro:** Negligible cost per session; the full development and testing period is likely under $0.10 total.
- **Pro:** Cost is visible to the user in real time, building trust.
- **Con:** Input truncation may drop relevant content from very long CVs (see ADR-008).
