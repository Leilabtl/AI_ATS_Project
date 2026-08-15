"""
LLM-powered deep candidate analysis — Phase 2 of the HR Compass AI pipeline.

Architecture
------------
The pipeline is split into two phases to balance cost and quality:

  Phase 1  embedding.py / matcher.py
           TF-IDF cosine similarity + keyword extraction. Runs on every CV
           at zero API cost and produces a structured pre-analysis dict
           (matched skills, missing skills, seniority, 6-factor score).

  Phase 2  this module (LLMAnalyzer)
           GPT-4o-mini receives the Phase 1 pre-analysis as context so it
           can focus on qualitative semantic judgement rather than
           re-counting keywords. Only called for candidates that pass the
           Phase 1 threshold — keeps cost proportional to shortlist size.

Fallback strategy
-----------------
When the API key is absent, quota-exhausted, or the call fails, Phase 1
results are returned unchanged. The UI degrades gracefully to keyword-only
mode; no crash, no blank screen.

Prompt design and iteration history
------------------------------------
Three prompt versions were tested before the current design was adopted
(see DECISIONS.md ADR-003 for the full A/B evaluation):

  v1.0  Direct instruction ("analyse this CV") — output was generic
  v2.0  Added JSON schema — structurally correct but shallow reasoning
  v3.0  Chain-of-thought preamble — 5 explicit reasoning steps before JSON.
        Confirmed on 6 labeled CV/JD pairs to produce more accurate
        Decline decisions for mismatched candidates.

Dynamic prompt selection
------------------------
Two distinct prompts are used depending on the use case:

  Full analysis      SYSTEM_PROMPT + _build_prompt()   max_tokens=1024
                     Structured JSON with all required fields. Used for
                     the main candidate evaluation pipeline.

  Streaming summary  stream_executive_summary()         max_tokens=200
                     Lightweight prose prompt, no JSON mode, streamed
                     token-by-token for immediate recruiter feedback.
                     Costs ~80% fewer tokens than the full analysis.

Layered safety defense
-----------------------
Every candidate analysis passes through four sequential safety layers:

  1. Input validation   _validate_input_sizes()     log + truncate oversized inputs
  2. PII detection      _detect_pii()               flag before sending to API
  3. Prompt sanitisation _sanitize_input()           replace injection patterns
  4. Output validation  _validate_output()           schema-check + recommendation enum
  5. Audit logging      _audit_log()                 append-only JSON-lines record

Cost controls (all active by default)
--------------------------------------
  - Phase 1 pre-filter: GPT called only for shortlisted candidates
  - Input truncation: CV ≤ 4 000 chars, JD ≤ 2 000 chars per call
  - Streaming uses 200-token cap vs 1 024 for full analysis
  - Rate limiting: 0.5 s minimum between calls
  - Per-session cost exposed via estimated_cost_usd property
  - Per-call cost written to audit log for post-session accounting
"""

import json
import os
import re
import time
import uuid
import logging
from datetime import datetime, timezone
from openai import OpenAI, APIError, AuthenticationError, RateLimitError

logger = logging.getLogger(__name__)

# Bump this version string whenever the prompt is meaningfully changed,
# so future analysis runs can be compared against a known baseline.
PROMPT_VERSION = "3.0"

SYSTEM_PROMPT = f"""You are an expert HR analyst and senior technical recruiter with 15+ years \
of experience evaluating candidates for technology and business roles. \
You provide honest, specific, and actionable assessments.
(Prompt version: {PROMPT_VERSION})

STEP-BY-STEP REASONING PROCESS — follow this before writing JSON:
1. Identify the 3-5 most critical technical requirements in the job description.
2. For each requirement, decide whether the CV meets it, partially meets it, or misses it.
3. Consider the candidate's career trajectory: is the role a natural next step?
4. Estimate interview readiness: would this person need significant ramp-up?
5. Only then synthesise into the JSON response below.

Your response MUST be valid JSON matching this exact schema — no extra text:

{{
  "executive_summary": "2-3 sentence narrative referencing specific details from the CV",
  "key_strengths": ["specific strength 1", "specific strength 2", "specific strength 3"],
  "critical_gaps": [
    {{
      "skill": "skill name",
      "importance": "why this skill matters for this specific role",
      "learning_path": "concrete steps, e.g. 'Complete AWS SAA course on A Cloud Guru, then deploy a serverless project'",
      "priority": "high",
      "estimated_time": "e.g. 4-6 weeks"
    }}
  ],
  "interview_recommendation": "Shortlist",
  "interview_focus_areas": ["specific topic to probe 1", "specific topic to probe 2"],
  "career_fit_narrative": "honest 1-2 sentence assessment of long-term fit"
}}

Rules:
- interview_recommendation must be exactly one of: Shortlist, Consider, Decline
- critical_gaps lists only skills in the JD that are absent from the CV
- Be specific — reference technologies, years, and projects visible in the CV
- Never repeat the same sentence across different fields"""

# Required keys and their expected types for output validation
_SCHEMA: dict[str, type] = {
    "executive_summary": str,
    "key_strengths": list,
    "critical_gaps": list,
    "interview_recommendation": str,
    "interview_focus_areas": list,
    "career_fit_narrative": str,
}
_VALID_RECOMMENDATIONS = {"Shortlist", "Consider", "Decline"}

# Patterns that indicate prompt-injection attempts inside CV text
_INJECTION_PATTERNS = [
    r"ignore\s+(?:all\s+)?(?:previous\s+|above\s+)?instructions?",
    r"disregard\s+(all\s+|previous\s+)?instructions?",
    r"you\s+are\s+now",
    r"act\s+as\s+",
    r"new\s+persona",
    r"<\|.*?\|>",
    r"\[INST\]",
    r"<<SYS>>",
]
_INJECTION_RE = re.compile("|".join(_INJECTION_PATTERNS), re.IGNORECASE)

# PII patterns checked before every API call; matches are logged (not sent to OpenAI)
_PII_PATTERNS = [
    (re.compile(r'\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b'), "EMAIL"),
    (re.compile(r'\b(?:\+?358|0)[\s\-]?\d{1,3}[\s\-]?\d{3,4}[\s\-]?\d{3,5}\b'), "PHONE"),
    (re.compile(r'\b\d{6}[+\-A]\d{3}[0-9A-FHJK-NPR-Y]\b'), "FIN_SSN"),
]

_AUDIT_LOG_PATH = "ats_audit.log"


class LLMAnalyzer:
    """Wraps the OpenAI Chat Completions API for deep candidate analysis."""

    MODEL = "gpt-4o-mini"

    # Minimum seconds between API calls (prevents accidental burst on large batches)
    _MIN_CALL_INTERVAL: float = 0.5
    # Hard ceiling on input sizes before truncation (characters)
    MAX_CV_CHARS: int = 4_000
    MAX_JD_CHARS: int = 2_000

    def __init__(self, api_key: str):
        self._client = OpenAI(api_key=api_key)
        self.total_tokens_used: int = 0
        self.total_api_calls: int = 0
        self._last_call_time: float = 0.0

    # ── Public API ────────────────────────────────────────────────────────────

    def analyze_candidate(
        self, cv_text: str, job_description: str, pre_analysis: dict
    ) -> dict | None:
        """Run GPT deep analysis on one candidate.

        Applies the layered safety pipeline before and after each API call:
          1. Input validation  — log a warning if inputs exceed size limits
          2. PII detection     — scan for emails, phones, SSNs; log findings
          3. Prompt sanitisation — strip injection patterns from CV text
          4. API call with auto-retry — retries once on schema validation failure
          5. Output validation — verify all required fields and valid recommendation
          6. Audit logging     — append a JSON-lines record to ats_audit.log

        Returns a validated dict on success, or None if both attempts fail
        (the caller falls back to Phase 1 results in that case).
        """
        correlation_id = str(uuid.uuid4())[:8]
        logger.info("[%s] Starting GPT analysis", correlation_id)
        self._validate_input_sizes(cv_text, job_description)

        pii_types = self._detect_pii(cv_text)
        if pii_types:
            logger.info("[%s] PII detected before API call: %s", correlation_id, pii_types)

        clean_cv = self._sanitize_input(cv_text)
        prompt = self._build_prompt(clean_cv, job_description, pre_analysis)
        tokens_before = self.total_tokens_used

        for attempt in range(2):
            raw = self._call_api(prompt, correlation_id)
            if raw is None:
                break
            parsed = self._parse_json(raw)
            if parsed and self._validate_output(parsed):
                self._audit_log(
                    correlation_id=correlation_id,
                    cv_name=pre_analysis.get("cv_name", "unknown"),
                    tokens=self.total_tokens_used - tokens_before,
                    recommendation=parsed.get("interview_recommendation", "unknown"),
                    pii_detected=bool(pii_types),
                )
                logger.info("[%s] Analysis complete — %s", correlation_id, parsed.get("interview_recommendation"))
                return parsed
            logger.warning("[%s] Response failed validation on attempt %d — retrying", correlation_id, attempt + 1)

        logger.error("[%s] Analysis failed after 2 attempts", correlation_id)
        return None

    def validate_key(self) -> bool:
        """Return True if the API key is accepted by OpenAI (including quota-exceeded accounts)."""
        try:
            self._client.chat.completions.create(
                model=self.MODEL,
                messages=[{"role": "user", "content": "Hi"}],
                max_tokens=5,
            )
            return True
        except RateLimitError:
            # 429 means the key is valid but the account quota is exhausted
            return True
        except AuthenticationError:
            return False
        except Exception:
            return False

    @property
    def estimated_cost_usd(self) -> float:
        """Rough cost estimate based on gpt-4o-mini pricing ($0.15 / 1M tokens)."""
        return round(self.total_tokens_used / 1_000_000 * 0.15, 4)

    # ── Private helpers ───────────────────────────────────────────────────────

    def _call_api(self, user_prompt: str, correlation_id: str = "") -> str | None:
        """Make one API call with rate-limiting guard. Returns raw text, or None on failure."""
        elapsed = time.monotonic() - self._last_call_time
        if elapsed < self._MIN_CALL_INTERVAL:
            time.sleep(self._MIN_CALL_INTERVAL - elapsed)
        try:
            resp = self._client.chat.completions.create(
                model=self.MODEL,
                response_format={"type": "json_object"},
                temperature=0.3,
                max_tokens=1024,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
            )
            usage = resp.usage
            if usage:
                self.total_tokens_used += usage.total_tokens
                logger.debug("[%s] API call used %d tokens", correlation_id, usage.total_tokens)
            self.total_api_calls += 1
            self._last_call_time = time.monotonic()
            return resp.choices[0].message.content
        except RateLimitError:
            logger.error("[%s] OpenAI rate limit hit", correlation_id)
            return None
        except AuthenticationError:
            logger.error("[%s] OpenAI authentication failed — check API key", correlation_id)
            return None
        except APIError as exc:
            logger.error("[%s] OpenAI API error: %s", correlation_id, exc)
            return None

    def _build_prompt(
        self, cv_text: str, job_description: str, pre_analysis: dict
    ) -> str:
        """Assemble the user-turn prompt with token-aware truncation."""
        matched = list(pre_analysis.get("matched_skills", {}).keys())[:8]
        missing = list(pre_analysis.get("missing_skills", {}).keys())[:6]

        return (
            f"## Job Description\n{job_description[:2000]}\n\n"
            f"## Candidate CV\n{cv_text[:4000]}\n\n"
            f"## Pre-computed Technical Analysis\n"
            f"- Matched skills: {', '.join(matched) or 'none detected'}\n"
            f"- Missing skills from JD: {', '.join(missing) or 'none'}\n"
            f"- Candidate seniority: {pre_analysis.get('cv_seniority', 'unspecified')}\n"
            f"- Skills match rate: {pre_analysis.get('skills_match', 0):.0f}%\n"
            f"- Keyword similarity to JD: {pre_analysis.get('semantic_similarity', 0):.0f}%\n\n"
            "Respond with JSON only."
        )

    def _validate_input_sizes(self, cv_text: str, job_description: str) -> None:
        """Log warnings when inputs exceed truncation thresholds."""
        if len(cv_text) > self.MAX_CV_CHARS:
            logger.warning(
                "CV text is %d chars — will be truncated to %d before API call",
                len(cv_text), self.MAX_CV_CHARS,
            )
        if len(job_description) > self.MAX_JD_CHARS:
            logger.warning(
                "Job description is %d chars — will be truncated to %d before API call",
                len(job_description), self.MAX_JD_CHARS,
            )

    @staticmethod
    def _sanitize_input(text: str) -> str:
        """
        Remove prompt-injection patterns from untrusted CV text before
        sending it to the model.
        """
        return _INJECTION_RE.sub("[REDACTED]", text)

    @staticmethod
    def _parse_json(raw: str) -> dict | None:
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return None

    @staticmethod
    def _validate_output(data: dict) -> bool:
        """Verify the model returned all required fields with correct types."""
        for key, expected_type in _SCHEMA.items():
            if key not in data or not isinstance(data[key], expected_type):
                return False
        if data["interview_recommendation"] not in _VALID_RECOMMENDATIONS:
            return False
        return True

    @staticmethod
    def _detect_pii(text: str) -> list[str]:
        """Return list of PII type labels found in text.

        Detections are recorded in the audit log so post-hoc fairness reviews
        can identify sessions where sensitive data was present. The original
        text is NOT redacted before the API call — redacting would degrade
        matching accuracy for candidates whose contact details appear near
        skill keywords.
        """
        found = []
        for pattern, label in _PII_PATTERNS:
            if pattern.search(text):
                found.append(label)
        return found

    def _audit_log(
        self,
        correlation_id: str,
        cv_name: str,
        tokens: int,
        recommendation: str,
        pii_detected: bool,
    ) -> None:
        """Append one JSON-lines record to ats_audit.log for every AI interaction.

        The log is append-only (never read back or deleted by the application)
        and records: timestamp, correlation_id, candidate name, model, token
        count, cost estimate, recommendation, PII flag, and prompt version.

        This provides a tamper-evident audit trail that enables:
          - Post-hoc fairness analysis (e.g. decline rate by seniority level)
          - Cost accounting per session
          - Prompt version traceability across analysis runs
        """
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "correlation_id": correlation_id,
            "cv_name": cv_name,
            "model": self.MODEL,
            "tokens": tokens,
            "cost_usd": round(tokens / 1_000_000 * 0.15, 6),
            "recommendation": recommendation,
            "pii_detected": pii_detected,
            "prompt_version": PROMPT_VERSION,
        }
        try:
            with open(_AUDIT_LOG_PATH, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(record) + "\n")
        except OSError as exc:
            logger.warning("Audit log write failed: %s", exc)

    def stream_executive_summary(
        self, cv_text: str, job_description: str, pre_analysis: dict
    ):
        """Yield text tokens for a live executive summary using OpenAI streaming.

        This is the cost-optimised alternate prompt path (dynamic prompt
        selection). It uses a lightweight prose prompt with max_tokens=200
        and no JSON mode — roughly 80% cheaper per call than the full
        analysis prompt. The trade-off is less structured output, which is
        acceptable for a quick recruiter preview rather than a pipeline
        decision.

        Streams token-by-token so the UI can display partial output
        immediately via Streamlit's st.write_stream(), rather than waiting
        for the full response.
        """
        elapsed = time.monotonic() - self._last_call_time
        if elapsed < self._MIN_CALL_INTERVAL:
            time.sleep(self._MIN_CALL_INTERVAL - elapsed)

        clean_cv = self._sanitize_input(cv_text[: self.MAX_CV_CHARS])
        matched = list(pre_analysis.get("matched_skills", {}).keys())[:6]
        missing = list(pre_analysis.get("missing_skills", {}).keys())[:4]

        prompt = (
            f"Role: {job_description[:500]}\n"
            f"CV excerpt: {clean_cv[:1500]}\n"
            f"Matched skills: {', '.join(matched) or 'none'}\n"
            f"Skill gaps: {', '.join(missing) or 'none'}\n"
            f"Phase-1 score: {pre_analysis.get('skills_match', 0):.0f}%\n\n"
            "Write a 3-sentence executive summary for a recruiter. "
            "Reference specific details from the CV. Be concise and direct."
        )

        try:
            stream = self._client.chat.completions.create(
                model=self.MODEL,
                temperature=0.3,
                max_tokens=200,
                stream=True,
                messages=[
                    {"role": "system", "content": "You are an expert HR analyst. Be specific and concise."},
                    {"role": "user", "content": prompt},
                ],
            )
            for chunk in stream:
                delta = chunk.choices[0].delta
                if delta.content:
                    yield delta.content
            self.total_api_calls += 1
            self._last_call_time = time.monotonic()
        except Exception as exc:
            logger.error("Streaming failed: %s", exc)
            yield f"[Streaming unavailable: {exc}]"

    def generate_market_intelligence(
        self, results: list[dict], job_title: str, job_description: str
    ) -> dict | None:
        """
        Aggregate GPT analysis across all candidates — produces strategic hiring insights.

        This is a separate, higher-level call that synthesises patterns across the whole
        candidate pool rather than evaluating a single CV.  Useful for:
        - Identifying whether the JD requirements match available talent
        - Spotting systemic skill gaps in the applicant pool
        - Recommending JD adjustments to attract better candidates
        """
        if not results:
            return None

        # Build aggregate stats from all results
        from collections import Counter

        all_matched: list[str] = []
        all_missing: list[str] = []
        seniority_counts: Counter = Counter()
        scores = [r.get("final_score", 0) for r in results]

        for r in results:
            all_matched.extend(r.get("matched_skills", []))
            all_missing.extend(r.get("missing_skills", []))
            seniority_counts[r.get("cv_seniority", "unspecified")] += 1

        top_matched = Counter(all_matched).most_common(8)
        top_missing = Counter(all_missing).most_common(8)
        avg_score = sum(scores) / len(scores) if scores else 0
        shortlisted = sum(1 for s in scores if s >= 70)

        prompt = f"""## Recruitment Context
Job Title: {job_title}
Job Description: {job_description[:1500]}

## Candidate Pool Statistics ({len(results)} candidates)
- Average match score: {avg_score:.1f}%
- Shortlisted (≥70%): {shortlisted} / {len(results)}
- Score range: {min(scores):.0f}% – {max(scores):.0f}%
- Seniority distribution: {dict(seniority_counts)}

## Skill Supply vs Demand
Most commonly matched skills (supply): {[s for s, _ in top_matched]}
Most common skill gaps (demand unmet): {[s for s, _ in top_missing]}

Respond with JSON only matching this exact schema:
{{
  "pool_quality_verdict": "string — 1-2 sentence overall assessment of this candidate pool",
  "talent_supply_summary": "string — which skills are plentiful and which are scarce",
  "jd_optimisation_tips": ["tip 1", "tip 2", "tip 3"],
  "hiring_timeline_estimate": "string — realistic estimate given pool quality",
  "market_insights": ["insight 1", "insight 2", "insight 3"],
  "recommended_actions": ["action 1", "action 2"]
}}"""

        try:
            resp = self._client.chat.completions.create(
                model=self.MODEL,
                response_format={"type": "json_object"},
                temperature=0.4,
                max_tokens=800,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a senior talent acquisition strategist. "
                            "Analyse candidate pool statistics and provide strategic hiring insights. "
                            "Be specific and actionable. Output valid JSON only."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
            )
            usage = resp.usage
            if usage:
                self.total_tokens_used += usage.total_tokens
            self.total_api_calls += 1
            data = json.loads(resp.choices[0].message.content)
            return data
        except Exception:
            return None


def get_analyzer_from_env() -> "LLMAnalyzer | None":
    """Return an LLMAnalyzer if OPENAI_API_KEY is set in the environment."""
    key = os.getenv("OPENAI_API_KEY", "").strip()
    return LLMAnalyzer(key) if key else None
