# Changelog — HR Compass ATS

All notable changes are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [2.0.0] — 2026-08-15

### Added
- **Correlation IDs** — every `analyze_candidate()` call generates a UUID-based
  8-character correlation ID that threads through all log messages for that
  analysis, making multi-candidate log traces easy to follow.
- **Audit logging** — `_audit_log()` appends one JSON line to `ats_audit.log`
  per AI interaction, recording timestamp, correlation ID, candidate name,
  model used, token count, cost estimate, recommendation, and whether PII was
  detected.
- **PII detection** — `_detect_pii()` scans CV text before each API call and
  flags emails, Finnish phone numbers, and Finnish personal identity codes.
  Findings are logged (for audit purposes) but not sent to OpenAI.
- **Streaming executive summary** — `stream_executive_summary()` streams a
  3-sentence summary live, token by token, using the OpenAI streaming API.
  A `⚡ Stream Live AI Summary` button in each candidate expander triggers it
  via Streamlit's `st.write_stream()`.
- **Prompt evaluation test suite** — `tests/test_prompt_eval.py` adds 30 new
  tests covering: PII detection (9), audit log format (6), sanitization
  pipeline (2), labeled CV/JD routing cases (9), and streaming structure (4).
- **ADR-009** — Ethical AI design decisions documented in `DECISIONS.md`.
- **ADR-010** — Cost analysis and controls documented in `DECISIONS.md`.

---

## [1.2.0] — CI/CD, Analytics & Streamlit Configuration

### Added
- GitHub Actions CI workflow (`.github/workflows/test.yml`) — runs pytest on
  every push/PR to main; Docker image pushed to GHCR on merge to main.
- Multi-stage Dockerfile and `docker-compose.yml` for containerised deployment.
- `.streamlit/config.toml` — Helix design-system theme (indigo primary colour,
  slate text, white background, 200 MB upload limit).
- `.streamlit/secrets.toml.template` — flat-format template showing where to
  place `OPENAI_API_KEY`; the real file is `.gitignore`-d.
- Plotly charts in the Analytics tab: score distribution histogram, skills
  frequency bar chart, and seniority breakdown pie chart.

### Changed
- Inline SVG gauge, score bar, GPT card, and keyword card blocks replaced with
  calls to reusable functions in `ui_components.py`.
- `requirements.txt` extended with `scikit-learn>=1.3.0`, `plotly>=5.18.0`,
  `pytest>=7.0.0`.

### Fixed
- Stale widget bug in the individual report viewer: hardcoded `key=` on
  disabled `st.text_area` caused Streamlit to freeze the first candidate's
  report. Fixed with dynamic keys (`key=f"report_preview_{_rpt_sel}"`).

---

## [1.1.0] — Modular Pipeline, TF-IDF Scoring & Code Quality

### Added
- `pipeline.py` — `process_single_cv()` and `process_cv_batch()` with
  progress/status callbacks; extracted from `streamlit_app.py` main loop.
- `ui_components.py` — `candidate_name()`, `render_score_gauge()`,
  `render_score_breakdown()`, `render_gpt_card()`, `render_keyword_summary_card()`.
- TF-IDF cosine similarity (`ngram_range=(1,2)`, `sublinear_tf=True`) replaces
  Jaccard word-overlap in `SemanticMatcher`.

### Changed
- Duplicate `_candidate_name()` in `report_generator.py` removed; now imports
  from `ui_components`.
- Dead code removed: unused `import tempfile`, unused `extract_skills` import
  in `matcher.py`, unused `historical_data` parameter in `advanced_features.py`.

---

## [1.0.0] — Initial Release

### Added
- Two-phase AI pipeline: TF-IDF keyword pre-screen (Phase 1) +
  GPT-4o-mini deep analysis (Phase 2).
- Chain-of-thought system prompt (v3.0) with JSON mode output.
- Output schema validation + 1 automatic retry on malformed response.
- Prompt injection protection (`_sanitize_input`).
- Cost tracking (`estimated_cost_usd` property, ~$0.15/1M tokens).
- Rate limiting (0.5 s minimum between API calls).
- Candidate pool persistence (`candidate_pool.json`).
- Report generation: PDF and plain-text exports via ReportLab.
- Email template builder for shortlist / longlist / rejection emails.
- Advanced features: interview question generation, diversity metrics,
  skill gap analytics, predictive success scoring.
- 69 unit tests at initial release.
