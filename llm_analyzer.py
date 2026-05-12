"""
LLM-powered deep candidate analysis using OpenAI GPT.

Pipeline design:
  Phase 1 — keyword pre-screening  (matcher.py / embedding.py, no API cost)
  Phase 2 — GPT deep analysis       (this module, called per candidate)

Key engineering decisions:
  - Chain-of-thought instruction tells GPT to reason before answering
  - JSON mode guarantees parseable output (no markdown fences to strip)
  - Output schema validation + 1 automatic retry on malformed response
  - Input sanitisation blocks prompt-injection patterns from CV text
  - Cost tracking: exposes token counts so the UI can display total usage
"""

import json
import os
import re
import time
import logging
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
        """
        Run GPT deep analysis on one candidate.

        Returns a validated dict on success, or None if both attempts fail.
        Retries once automatically when the model returns malformed JSON or
        an output that fails schema validation.
        """
        self._validate_input_sizes(cv_text, job_description)
        clean_cv = self._sanitize_input(cv_text)
        prompt = self._build_prompt(clean_cv, job_description, pre_analysis)

        for attempt in range(2):
            raw = self._call_api(prompt)
            if raw is None:
                break
            parsed = self._parse_json(raw)
            if parsed and self._validate_output(parsed):
                return parsed
            logger.warning("GPT response failed validation on attempt %d — retrying", attempt + 1)

        return None

    def validate_key(self) -> bool:
        """Return True if the API key is accepted by OpenAI."""
        try:
            self._client.chat.completions.create(
                model=self.MODEL,
                messages=[{"role": "user", "content": "Hi"}],
                max_tokens=5,
            )
            return True
        except (AuthenticationError, APIError):
            return False
        except Exception:
            return False

    @property
    def estimated_cost_usd(self) -> float:
        """Rough cost estimate based on gpt-4o-mini pricing ($0.15 / 1M tokens)."""
        return round(self.total_tokens_used / 1_000_000 * 0.15, 4)

    # ── Private helpers ───────────────────────────────────────────────────────

    def _call_api(self, user_prompt: str) -> str | None:
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
            self.total_api_calls += 1
            self._last_call_time = time.monotonic()
            return resp.choices[0].message.content
        except RateLimitError:
            logger.error("OpenAI rate limit hit")
            return None
        except AuthenticationError:
            logger.error("OpenAI authentication failed — check API key")
            return None
        except APIError as exc:
            logger.error("OpenAI API error: %s", exc)
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
