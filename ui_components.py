"""
Reusable Streamlit rendering components for HR Compass.

Keeping presentation logic here (rather than inline in streamlit_app.py)
means each component can be developed, styled, and reasoned about
independently of page layout and session-state orchestration.
"""

import re
import streamlit as st

# ── Candidate name helper ────────────────────────────────────────────────────

_CN_NOISE = re.compile(
    r'\b(cv|resume|job|curriculum|vitae|application|ats|report|\d{4,})\b',
    re.IGNORECASE,
)


def candidate_name(filename: str) -> str:
    """Convert a CV filename to a readable First Last display name."""
    n = filename
    for ext in ('.pdf', '.PDF', '.txt', '.docx', '.doc'):
        n = n.replace(ext, '')
    n = _CN_NOISE.sub('', n)
    n = re.sub(r'[\s_\-\.]+', ' ', n).strip()
    words = [w for w in n.split() if len(w) > 1]
    return ' '.join(words[:2]).title() if words else filename.split('.')[0].title()


# ── Score gauge (SVG circle) ─────────────────────────────────────────────────

def render_score_gauge(final_score: float, confidence: str = '') -> None:
    """Render an SVG circular gauge for a candidate's final score."""
    r = 60
    circumference = 2 * 3.14159 * r
    offset = circumference * (1 - final_score / 100)
    fit_label = (
        "Strong fit"  if final_score >= 80 else
        "Good fit"    if final_score >= 65 else
        "Partial fit" if final_score >= 50 else
        "Weak fit"
    )
    colour = (
        '#16a34a' if final_score >= 75 else
        '#f59e0b' if final_score >= 50 else
        '#ef4444'
    )
    st.markdown(f"""
    <div class="gauge-wrap">
        <svg width="140" height="140" viewBox="0 0 140 140">
            <circle cx="70" cy="70" r="{r}" fill="none" stroke="#ECEEF1" stroke-width="8"/>
            <circle cx="70" cy="70" r="{r}" fill="none" stroke="{colour}" stroke-width="8"
                    stroke-dasharray="{circumference:.1f}" stroke-dashoffset="{offset:.1f}"
                    stroke-linecap="round" transform="rotate(-90 70 70)"/>
        </svg>
        <div style="margin-top:-84px;margin-bottom:70px;font-size:38px;font-weight:700;
                    color:{colour};letter-spacing:-0.03em;text-align:center;line-height:1;">
            {final_score:.0f}
        </div>
        <div class="gauge-label" style="color:{colour};">{fit_label}</div>
        <div class="gauge-sub">{confidence} confidence</div>
    </div>
    """, unsafe_allow_html=True)


# ── Score breakdown bars ──────────────────────────────────────────────────────

_SCORE_ROWS = [
    ("Skills match",    "skills_match",        "How many of the JD's required skills appear in the CV"),
    ("Keyword overlap", "semantic_similarity",  "Word-level overlap between CV and job description"),
    ("Experience",      "experience_relevance", "Evidence of relevant seniority and accomplishments"),
    ("Keyword density", "keyword_density",      "Concentration of JD terms throughout the CV"),
    ("Culture fit",     "culture_fit",          "Soft-skill indicators aligned with the role"),
    ("Seniority",       "seniority_alignment",  "Seniority level match between candidate and role"),
]


def render_score_breakdown(score_breakdown: dict) -> None:
    """Render labelled progress bars for the 6-factor score breakdown."""
    html = (
        '<div style="font-size:11px;font-weight:700;letter-spacing:.08em;'
        'text-transform:uppercase;color:#9ca3af;margin-bottom:12px;">'
        'What the scores mean</div>'
    )
    for label, key, tooltip in _SCORE_ROWS:
        val = float(score_breakdown.get(key, 0))
        colour = '#16a34a' if val >= 75 else '#f59e0b' if val >= 50 else '#ef4444'
        status = "Strong" if val >= 75 else "Moderate" if val >= 50 else "Weak"
        html += f"""
        <div style="margin-bottom:10px;">
            <div style="display:flex;justify-content:space-between;align-items:baseline;margin-bottom:3px;">
                <div style="font-size:13px;font-weight:600;color:#374151;">{label}</div>
                <div style="font-size:12px;color:{colour};font-weight:700;">{status} · {val:.0f}</div>
            </div>
            <div style="background:#f1f5f9;border-radius:4px;height:8px;overflow:hidden;">
                <div style="width:{val:.0f}%;height:100%;background:{colour};border-radius:4px;"></div>
            </div>
            <div style="font-size:11px;color:#9ca3af;margin-top:2px;">{tooltip}</div>
        </div>"""
    st.markdown(html, unsafe_allow_html=True)


# ── GPT executive-summary card ───────────────────────────────────────────────

def render_gpt_card(llm: dict) -> None:
    """Render the GPT executive summary card if LLM data is present."""
    rec = llm.get('interview_recommendation', 'Consider')
    rec_cls = (
        'rec-shortlist' if rec == 'Shortlist' else
        'rec-consider'  if rec == 'Consider'  else
        'rec-decline'
    )
    strengths_html = "".join(
        f'<div style="font-size:13px;color:#4B5563;margin-bottom:4px;">· {s}</div>'
        for s in llm.get('key_strengths', [])
    )
    st.markdown(f"""
    <div class="gpt-card">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
            <div class="gpt-card-title">GPT Executive Summary</div>
            <span class="rec-badge {rec_cls}">{rec}</span>
        </div>
        <div style="font-size:14px;color:#4B5563;line-height:1.65;margin-bottom:14px;">
            {llm.get('executive_summary', '')}
        </div>
        <div style="font-size:11px;letter-spacing:.08em;text-transform:uppercase;
                    color:#9CA3AF;font-weight:600;margin-bottom:8px;">Key strengths</div>
        {strengths_html}
    </div>
    """, unsafe_allow_html=True)


def render_keyword_summary_card(strategic_summary: str) -> None:
    """Render the Phase-1 keyword match summary card."""
    summary_clean = re.sub(r'\*\*(.+?)\*\*', r'\1', strategic_summary)
    st.markdown(f"""
    <div class="gpt-card">
        <div class="gpt-card-title">Match Summary</div>
        <div style="font-size:14px;color:#4B5563;line-height:1.65;">{summary_clean}</div>
    </div>
    """, unsafe_allow_html=True)
