import streamlit as st
from matcher import EnhancedMatcher
from report_generator import ReportGenerator
from advanced_features import AdvancedATS
from candidate_pool import CandidatePool
from llm_analyzer import LLMAnalyzer, get_analyzer_from_env
from roles_data import ROLES, ROLE_LIST, SENIORITY_LEVELS, SENIORITY_CONTEXT
from pipeline import process_cv_batch
from ui_components import (
    candidate_name as _candidate_name,
    render_score_gauge,
    render_score_breakdown,
    render_gpt_card,
    render_keyword_summary_card,
)
import os
import re
import sys
import subprocess
from pathlib import Path
import pandas as pd
import plotly.express as px
from datetime import datetime
from io import BytesIO
import json
import zipfile
from collections import Counter

# Load .env if present (so ANTHROPIC_API_KEY can be set without the UI)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

JOB_TITLE_FILE = 'job_titles.json'


def load_saved_job_titles(file_path=JOB_TITLE_FILE):
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                titles = json.load(f)
            if isinstance(titles, list):
                return [t.strip() for t in titles if isinstance(t, str) and t.strip()]
        except Exception:
            pass
    return []


def save_job_titles(titles, file_path=JOB_TITLE_FILE):
    unique_titles = []
    for title in titles:
        if isinstance(title, str):
            clean = title.strip()
            if clean and clean not in unique_titles:
                unique_titles.append(clean)
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(unique_titles, f, indent=2, ensure_ascii=False)
    except Exception:
        pass

# Page config
st.set_page_config(
    page_title="HR Compass - AI Talent Navigation",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Global CSS (Helix design system) ────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

:root {
    --bg:          #F8F9FA;
    --surface:     #FFFFFF;
    --ink:         #0F1115;
    --ink-2:       #4B5563;
    --ink-3:       #9CA3AF;
    --divider:     #EEF0F3;
    --hover:       #F3F4F6;
    --accent:      #4F46E5;
    --accent-soft: #EEF0FE;
    --track:       #ECEEF1;
    --shadow:      0 2px 8px rgba(0,0,0,0.06);
}

/* ── Base ── */
html, body, .stApp {
    font-family: 'Inter', ui-sans-serif, system-ui, sans-serif !important;
    font-feature-settings: "cv11","ss01";
    -webkit-font-smoothing: antialiased;
    letter-spacing: -0.005em;
    background: var(--bg) !important;
    color: var(--ink) !important;
}
#MainMenu, footer, header { visibility: hidden; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: var(--surface) !important;
    border-right: 1px solid var(--divider) !important;
}
.nav-label {
    font-size: 11px; letter-spacing: .08em; text-transform: uppercase;
    color: var(--ink-3); padding: 0 12px; margin: 24px 0 8px; font-weight: 500;
}
.nav-item {
    display: flex; align-items: center; gap: 12px;
    padding: 9px 12px; border-radius: 8px;
    font-size: 14px; color: var(--ink-2); font-weight: 500;
    margin: 1px 0; transition: background .12s;
}
.nav-item.active { background: var(--accent-soft); color: var(--accent); }
.nav-item:hover:not(.active) { background: var(--hover); color: var(--ink); }

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    gap: 32px; border-bottom: 1px solid var(--divider); background: transparent;
}
.stTabs [data-baseweb="tab"] {
    height: 48px; background: transparent; border: none;
    color: var(--ink-3) !important; font-weight: 500 !important; padding: 0 4px;
    font-size: 14px !important;
}
.stTabs [aria-selected="true"] {
    color: var(--accent) !important;
    border-bottom: 2px solid var(--accent) !important;
}

/* ── Metric cards ── */
.metric-card {
    background: var(--surface);
    border-radius: 14px;
    padding: 24px;
    box-shadow: var(--shadow);
    flex: 1; min-width: 180px;
}
.metric-val {
    font-size: 2.25rem; font-weight: 600; color: var(--ink);
    line-height: 1; letter-spacing: -0.03em;
}
.metric-lab {
    font-size: 13px; color: var(--ink-3); margin-top: 8px; font-weight: 400;
}

/* ── Candidate list ── */
.cand-list {
    background: var(--surface); border-radius: 14px;
    box-shadow: var(--shadow); overflow: hidden; margin-top: 8px;
}
.cand-row {
    display: grid; grid-template-columns: 44px 1fr 56px;
    gap: 16px; align-items: center; padding: 18px 24px;
    border-bottom: 1px solid var(--divider); transition: background .12s;
}
.cand-row:last-child { border-bottom: none; }
.cand-row:hover { background: #FBFBFC; }
.cand-avatar {
    width: 44px; height: 44px; border-radius: 50%;
    background: #F1F2F4; color: var(--ink-2);
    display: flex; align-items: center; justify-content: center;
    font-size: 14px; font-weight: 600; letter-spacing: -0.01em;
    flex-shrink: 0;
}
.cand-name { font-size: 15px; font-weight: 600; color: var(--ink); letter-spacing: -0.01em; }
.cand-meta { font-size: 13px; color: var(--ink-2); margin-top: 3px; font-weight: 400; }
.score-circle {
    width: 52px; height: 52px; border-radius: 50%;
    background: var(--accent); color: #fff;
    display: flex; align-items: center; justify-content: center;
    font-size: 16px; font-weight: 600; letter-spacing: -0.02em;
    flex-shrink: 0;
}
.score-circle.mid { opacity: .78; }
.score-circle.low { opacity: .55; }

/* ── Detail panel ── */
.detail-card {
    background: var(--surface); border-radius: 14px;
    box-shadow: var(--shadow); padding: 0; overflow: hidden;
    margin-top: 16px;
}
.detail-head {
    display: flex; align-items: center; gap: 16px; padding: 28px 28px 20px;
    border-bottom: 1px solid var(--divider);
}
.detail-avatar {
    width: 56px; height: 56px; border-radius: 50%;
    background: var(--accent-soft); color: var(--accent);
    display: flex; align-items: center; justify-content: center;
    font-size: 18px; font-weight: 600; flex-shrink: 0;
}
.detail-name { font-size: 18px; font-weight: 600; color: var(--ink); letter-spacing: -0.02em; }
.detail-meta { font-size: 13px; color: var(--ink-2); margin-top: 4px; }

/* ── Score gauge ── */
.gauge-wrap {
    display: flex; flex-direction: column; align-items: center; padding: 28px 0 20px;
}
.gauge-label { margin-top: 14px; font-size: 14px; font-weight: 500; color: var(--accent); }
.gauge-sub   { margin-top: 6px; font-size: 13px; color: var(--ink-3); text-align: center; }

/* ── Score breakdown bars ── */
.section-eyebrow {
    font-size: 11px; letter-spacing: .08em; text-transform: uppercase;
    color: var(--ink-3); font-weight: 600; margin-bottom: 16px;
}
.bd-row {
    display: grid; grid-template-columns: 120px 1fr 36px;
    gap: 14px; align-items: center; margin-bottom: 12px;
}
.bd-label { font-size: 13px; color: var(--ink-2); font-weight: 500; }
.bd-track {
    height: 6px; background: var(--track); border-radius: 3px; overflow: hidden;
}
.bd-fill  { height: 100%; background: var(--accent); border-radius: 3px; }
.bd-value { font-size: 13px; color: var(--ink); font-weight: 600; text-align: right; }

/* ── Skill fit two-column ── */
.skill-cols { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; margin-top: 8px; }
.skill-col-title { font-size: 13px; font-weight: 600; margin-bottom: 10px; }
.skill-col-title.meets { color: var(--accent); }
.skill-col-title.gap   { color: var(--ink-3); }
.skill-item { font-size: 14px; font-weight: 500; color: var(--ink); margin-bottom: 8px; line-height: 1.3; }
.skill-item.gap-item   { color: var(--ink-2); }
.skill-sub  { font-size: 12px; color: var(--ink-3); font-weight: 400; display: block; margin-top: 2px; }

/* ── Rec badge ── */
.rec-badge {
    display: inline-block; padding: 3px 12px; border-radius: 20px;
    font-size: 12px; font-weight: 700; letter-spacing: -0.005em;
}
.rec-shortlist { background: var(--accent-soft); color: var(--accent); }
.rec-consider  { background: #FEF9C3; color: #854D0E; }
.rec-decline   { background: #FEE2E2; color: #991B1B; }

/* ── GPT insight card ── */
.gpt-card {
    background: var(--surface); border-radius: 14px;
    box-shadow: var(--shadow); padding: 24px; margin-bottom: 16px;
    border-left: 4px solid var(--accent);
}
.gpt-card-title {
    font-size: 13px; font-weight: 600; color: var(--accent);
    letter-spacing: -0.005em; margin-bottom: 10px;
}

/* ── Gap item card ── */
.gap-card {
    background: var(--bg); border-radius: 10px;
    padding: 14px 16px; margin-bottom: 10px;
}
.gap-card-title { font-size: 14px; font-weight: 600; color: var(--ink); }
.gap-card-meta  { font-size: 12px; color: var(--ink-3); margin-top: 2px; }
.gap-card-path  { font-size: 13px; color: var(--ink-2); margin-top: 8px; line-height: 1.5; }

/* ── Action buttons ── */
.btn-primary {
    background: var(--accent); color: #fff; border: none;
    border-radius: 10px; padding: 10px 20px; font-size: 14px;
    font-weight: 500; cursor: pointer; box-shadow: var(--shadow);
}
.btn-ghost {
    background: var(--surface); color: var(--ink);
    box-shadow: inset 0 0 0 1px var(--divider);
    border: none; border-radius: 10px; padding: 10px 20px;
    font-size: 14px; font-weight: 500; cursor: pointer;
}

/* ── Inputs ── */
.stTextArea textarea, .stTextInput input {
    background: var(--surface) !important;
    border: 1px solid var(--divider) !important;
    color: var(--ink) !important; border-radius: 10px !important;
    font-family: 'Inter', sans-serif !important;
}

/* ── Info / status boxes ── */
.status-active {
    background: var(--accent-soft); border-radius: 10px;
    padding: 10px 14px; color: var(--accent); font-weight: 600;
    font-size: 13px; margin-top: 4px;
}
.status-inactive {
    background: #FEF9C3; border-radius: 10px;
    padding: 10px 14px; color: #854D0E; font-weight: 600;
    font-size: 13px; margin-top: 4px;
}
.premium-header {
    font-weight: 600; font-size: 20px; color: var(--ink);
    margin: 32px 0 16px; letter-spacing: -0.02em;
}
</style>
""", unsafe_allow_html=True)


# Initialize session state
if 'results' not in st.session_state:
    st.session_state.results = None

# Bootstrap LLM analyzer from OPENAI_API_KEY in .env on first load
if 'llm_analyzer' not in st.session_state:
    st.session_state.llm_analyzer = get_analyzer_from_env()  # None if key not set

# ── Top bar ──────────────────────────────────────────────────────────────────
st.markdown(f"""
<div style="display:flex;justify-content:space-between;align-items:center;
            padding:14px 0 14px;border-bottom:1px solid #EEF0F3;margin-bottom:28px;">
    <div style="font-size:13px;color:#9CA3AF;font-weight:500;">
        Open roles &nbsp;/&nbsp;
        <span style="color:#0F1115;font-weight:600;">{st.session_state.get('current_job_title', 'New Role')}</span>
    </div>
    <div style="display:flex;gap:10px;align-items:center;">
        <span style="background:#EEF0FE;color:#4F46E5;font-size:11px;font-weight:600;
                     padding:3px 10px;border-radius:6px;letter-spacing:.03em;">v2.5</span>
    </div>
</div>
""", unsafe_allow_html=True)

from embedding import SemanticMatcher
matcher = EnhancedMatcher(SemanticMatcher())

# ── Sidebar Navigation ───────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="padding: 28px 8px 0;">
        <div style="font-size:17px;font-weight:600;color:#0F1115;letter-spacing:-0.02em;line-height:1;">HR Compass</div>
        <div style="font-size:12px;color:#9CA3AF;font-weight:400;margin-top:3px;">Talent intelligence</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div style="margin-top:28px;"></div>', unsafe_allow_html=True)
    st.markdown('<div class="nav-label">Workspace</div>', unsafe_allow_html=True)
    st.markdown('<div class="nav-item active">Job Setup</div>', unsafe_allow_html=True)
    st.markdown('<div class="nav-item">Candidate Pool</div>', unsafe_allow_html=True)
    st.markdown('<div class="nav-item">Analytics</div>', unsafe_allow_html=True)
    st.markdown('<div class="nav-item">Reports</div>', unsafe_allow_html=True)

    st.markdown('<div class="nav-label">Intelligence</div>', unsafe_allow_html=True)
    st.markdown('<div class="nav-item">Scoring models</div>', unsafe_allow_html=True)
    st.markdown('<div class="nav-item">Settings</div>', unsafe_allow_html=True)

    n_cvs = len(st.session_state.results) if st.session_state.get('results') else 0
    job_name = st.session_state.get('current_job_title', '—')
    st.markdown(f"""
    <div style="margin-top:auto;padding:20px 8px 8px;">
        <div style="background:#F8F9FA;border-radius:10px;padding:14px 16px;">
            <div style="font-size:11px;letter-spacing:.08em;text-transform:uppercase;
                        color:#9CA3AF;font-weight:600;margin-bottom:10px;">Current job</div>
            <div style="font-size:13px;font-weight:500;color:#0F1115;">{job_name}</div>
            <div style="font-size:12px;color:#9CA3AF;margin-top:4px;">{n_cvs} candidate{'s' if n_cvs != 1 else ''} processed</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# Defaults so other tabs can always reference these variables regardless of
# which tab is active or whether the Job Setup tab has been completed.
job_title = ""
job_description = ""
uploaded_files = []
process_button = False

# Main app tabs
tab_job, tab_pool, tab_analytics, tab_settings = st.tabs(["Job Setup", "Candidate Pool", "Analytics", "Settings"])

with tab_job:
        st.session_state.selected_sidebar_tab = "Job Setup"

        # ── First-time onboarding guide (shown only when no results exist) ────
        if not st.session_state.get("results"):
            st.markdown("""
            <div style="background:linear-gradient(135deg,#eef2ff 0%,#f0f9ff 100%);
                        border:1px solid #c7d2fe;border-radius:14px;padding:24px 28px;
                        margin-bottom:28px;">
                <div style="font-size:18px;font-weight:700;color:#312e81;margin-bottom:6px;">
                    👋 Welcome to HR Compass
                </div>
                <div style="font-size:13px;color:#4338ca;margin-bottom:18px;">
                    Screen your first candidates in three steps:
                </div>
                <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:14px;">
                    <div style="background:white;border-radius:10px;padding:16px;
                                border:1px solid #e0e7ff;text-align:center;">
                        <div style="font-size:24px;margin-bottom:8px;">1️⃣</div>
                        <div style="font-weight:600;color:#1e1b4b;font-size:13px;margin-bottom:4px;">
                            Pick a Role
                        </div>
                        <div style="font-size:12px;color:#6b7280;">
                            Select the job title from the dropdown below. The job description auto-fills — edit it to match your exact requirements.
                        </div>
                    </div>
                    <div style="background:white;border-radius:10px;padding:16px;
                                border:1px solid #e0e7ff;text-align:center;">
                        <div style="font-size:24px;margin-bottom:8px;">2️⃣</div>
                        <div style="font-weight:600;color:#1e1b4b;font-size:13px;margin-bottom:4px;">
                            Upload CVs
                        </div>
                        <div style="font-size:12px;color:#6b7280;">
                            Drag and drop PDF CVs (1–500 files). The AI screens all of them automatically — fast keyword match first, then deep GPT analysis.
                        </div>
                    </div>
                    <div style="background:white;border-radius:10px;padding:16px;
                                border:1px solid #e0e7ff;text-align:center;">
                        <div style="font-size:24px;margin-bottom:8px;">3️⃣</div>
                        <div style="font-weight:600;color:#1e1b4b;font-size:13px;margin-bottom:4px;">
                            Review & Export
                        </div>
                        <div style="font-size:12px;color:#6b7280;">
                            Ranked results appear below. Export a PDF report, CSV, or email templates for your shortlist — all in one click.
                        </div>
                    </div>
                </div>
                <div style="font-size:11px;color:#6366f1;margin-top:14px;text-align:center;">
                    💡 Tip: No API key? The keyword matching layer still works fully — GPT analysis is optional.
                </div>
            </div>
            """, unsafe_allow_html=True)

        # ── Role title (searchbox autocomplete) ───────────────────────────────
        saved_roles   = load_saved_job_titles()
        custom_roles  = sorted([r for r in saved_roles if r not in ROLES], key=str.lower)
        _all_titles   = ROLE_LIST + custom_roles   # full searchable list

        col_role, col_seniority = st.columns([3, 1])

        with col_role:
            _CUSTOM_ROLE = "── Enter custom role ──"
            _select_opts = [""] + _all_titles + [_CUSTOM_ROLE]
            _selected = st.selectbox(
                "Job Title",
                options=_select_opts,
                index=0,
                format_func=lambda x: "🔍 Select or type a role…" if x == "" else x,
                key="role_selectbox",
                help="Start typing to filter predefined roles. Choose the last option to enter any custom title.",
            )
            if _selected == _CUSTOM_ROLE:
                base_role = st.text_input(
                    "Custom Role Title",
                    placeholder="e.g. DevRel Engineer, AI Researcher…",
                    key="custom_role_input",
                ).strip()
                if base_role and base_role not in _all_titles:
                    save_job_titles(saved_roles + [base_role])
            else:
                base_role = _selected.strip()

        with col_seniority:
            seniority = st.selectbox(
                "Seniority Level",
                options=["(not specified)"] + SENIORITY_LEVELS,
                index=0,
                key="seniority_level",
                help="Select the required experience level for this role.",
            )

        # Derived full job title shown as info pill
        _seniority_prefix = "" if seniority == "(not specified)" else seniority + " "
        job_title = (_seniority_prefix + base_role).strip() if base_role else ""
        if job_title:
            st.info(f"**Posting as:** {job_title}", icon="🏷️")
        else:
            st.warning("Type a role title above to continue.", icon="⚠️")

        # ── Job description: auto-fill + seniority context injection ──────────
        _ctx  = SENIORITY_CONTEXT.get(seniority, "") if seniority != "(not specified)" else ""
        _base_jd = ROLES.get(base_role, "")   # empty string for custom roles

        # Recompute default JD whenever base_role or seniority changes
        _state_key = f"{base_role}||{seniority}"
        if st.session_state.get("_jd_state_key") != _state_key:
            st.session_state["_jd_state_key"] = _state_key
            if _ctx and _base_jd:
                st.session_state.job_desc = _ctx + "\n\n" + _base_jd
            elif _ctx:
                st.session_state.job_desc = _ctx
            elif _base_jd:
                st.session_state.job_desc = _base_jd
            # else: custom role with no seniority — leave blank for user to write

        job_description = st.text_area(
            "Job Description",
            height=320,
            value=st.session_state.get("job_desc", ""),
            key="job_desc",
            help="Auto-filled from the template. Edit freely — your edits are used for scoring.",
        )

        if job_title:
            uploaded_files = st.file_uploader(
                "📤 Upload CVs (PDF)",
                type="pdf",
                accept_multiple_files=True,
                help="Drag & drop PDF files here, or click Browse. Accepts 1–500 files. Scanned/image PDFs may not parse correctly.",
            )
            _n_files = len(uploaded_files) if uploaded_files else 0
            if _n_files > 0:
                st.caption(f"✅ {_n_files} file{'s' if _n_files != 1 else ''} ready — click Analyze to start.")
            process_button = st.button(
                "🚀 Analyze Candidates",
                type="primary",
                use_container_width=True,
                disabled=_n_files == 0,
                help="Run Phase 1 keyword pre-screening on all uploaded CVs, then Phase 2 GPT analysis on the best matches (requires API key).",
            )
        else:
            st.markdown("""
            <div style="background:#f8fafc;border:1px dashed #cbd5e1;border-radius:12px;
                        padding:24px;text-align:center;color:#64748b;margin-top:8px;">
                <div style="font-size:32px;margin-bottom:8px;">☝️</div>
                <div style="font-weight:600;font-size:14px;color:#374151;">Select a role to continue</div>
                <div style="font-size:12px;margin-top:4px;">
                    Choose a job title from the dropdown above — the job description will auto-fill and you can then upload CVs.
                </div>
            </div>
            """, unsafe_allow_html=True)
    
with tab_analytics:
    _analytics_results = st.session_state.get("results") or []

    if not _analytics_results:
        st.info("Run a candidate analysis first (Job Setup tab) to see charts here.", icon="📊")
    else:
        st.subheader("📊 Candidate Pool Analytics")

        # ── Score distribution histogram ──────────────────────────────────────
        _scores = [r.get("final_score", 0) for r in _analytics_results]
        _score_df = pd.DataFrame({"Final Score": _scores})
        _fig_hist = px.histogram(
            _score_df,
            x="Final Score",
            nbins=10,
            range_x=[0, 100],
            color_discrete_sequence=["#6366f1"],
            labels={"Final Score": "Final Score (0–100)", "count": "Candidates"},
            title="Score Distribution",
        )
        _fig_hist.update_layout(bargap=0.1, plot_bgcolor="white", paper_bgcolor="white",
                                title_font_size=16, margin=dict(t=40, b=30))
        st.plotly_chart(_fig_hist, use_container_width=True)

        _col_pie, _col_bar = st.columns(2)

        # ── Seniority breakdown pie ───────────────────────────────────────────
        with _col_pie:
            _seniority_counts = Counter(
                r.get("cv_seniority", "unspecified")
                for r in _analytics_results
            )
            _sen_df = pd.DataFrame(
                _seniority_counts.items(), columns=["Seniority", "Count"]
            )
            _fig_pie = px.pie(
                _sen_df,
                names="Seniority",
                values="Count",
                color_discrete_sequence=px.colors.qualitative.Pastel,
                title="Seniority Breakdown",
            )
            _fig_pie.update_layout(title_font_size=16, margin=dict(t=40, b=10))
            st.plotly_chart(_fig_pie, use_container_width=True)

        # ── Top matched skills bar chart ──────────────────────────────────────
        with _col_bar:
            _all_matched: list[str] = []
            for r in _analytics_results:
                _all_matched.extend(r.get("matched_skills", []))
            _skill_counts = Counter(_all_matched).most_common(12)
            if _skill_counts:
                _sk_df = pd.DataFrame(_skill_counts, columns=["Skill", "Candidates"])
                _fig_bar = px.bar(
                    _sk_df,
                    x="Candidates",
                    y="Skill",
                    orientation="h",
                    color="Candidates",
                    color_continuous_scale="Teal",
                    title="Top Matched Skills",
                )
                _fig_bar.update_layout(
                    yaxis=dict(autorange="reversed"),
                    coloraxis_showscale=False,
                    plot_bgcolor="white",
                    paper_bgcolor="white",
                    title_font_size=16,
                    margin=dict(t=40, b=10),
                )
                st.plotly_chart(_fig_bar, use_container_width=True)
            else:
                st.info("No matched skills data available.")

    # ── GPT Market Intelligence ──────────────────────────────────────────────
    st.divider()
    st.subheader("🌐 GPT Market Intelligence")
    st.markdown(
        "Get GPT-powered strategic insights across your entire candidate pool: "
        "talent supply analysis, JD optimisation tips, and hiring timeline estimates."
    )

    results_for_intel = st.session_state.get("results") or []
    llm_intel = st.session_state.get("llm_analyzer")

    if not results_for_intel:
        st.info("Run a candidate analysis first (Job Setup tab) to unlock Market Intelligence.")
    elif not llm_intel:
        st.warning("Configure your OpenAI API key in the Settings tab to enable Market Intelligence.")
    else:
        intel_key = f"market_intel_{len(results_for_intel)}"
        if intel_key not in st.session_state:
            if st.button("🚀 Generate Market Intelligence Report", use_container_width=True):
                job_title_intel = st.session_state.get("current_job_title", "this role")
                job_desc_intel = st.session_state.get("job_desc", "")
                with st.spinner("GPT is analysing your candidate pool..."):
                    intel = llm_intel.generate_market_intelligence(
                        results_for_intel, job_title_intel, job_desc_intel
                    )
                if intel:
                    st.session_state[intel_key] = intel
                    st.rerun()
                else:
                    st.error("Market intelligence generation failed. Check API key and retry.")

        if intel_key in st.session_state:
            intel = st.session_state[intel_key]

            # Pool quality verdict
            st.markdown(f"""
            <div style="background:#f0fdf4;border:1px solid #86efac;border-left:5px solid #16a34a;
                        padding:16px 20px;border-radius:10px;margin-bottom:16px;">
                <div style="font-weight:700;color:#166534;margin-bottom:6px;">
                    🏆 Pool Quality Verdict
                </div>
                <div style="color:#14532d;font-size:1rem;line-height:1.6;">
                    {intel.get("pool_quality_verdict", "—")}
                </div>
            </div>""", unsafe_allow_html=True)

            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**📊 Talent Supply Summary**")
                st.info(intel.get("talent_supply_summary", "—"))

                st.markdown("**⏱ Hiring Timeline Estimate**")
                st.info(intel.get("hiring_timeline_estimate", "—"))

            with col2:
                tips = intel.get("jd_optimisation_tips", [])
                if tips:
                    st.markdown("**✏️ JD Optimisation Tips**")
                    for tip in tips:
                        st.markdown(f"- {tip}")

                actions = intel.get("recommended_actions", [])
                if actions:
                    st.markdown("**⚡ Recommended Actions**")
                    for action in actions:
                        st.markdown(f"- {action}")

            insights = intel.get("market_insights", [])
            if insights:
                st.markdown("**💡 Market Insights**")
                for insight in insights:
                    st.markdown(f"""
                    <div style="background:#eff6ff;border:1px solid #bfdbfe;padding:10px 14px;
                                border-radius:8px;margin-bottom:8px;color:#1e40af;">
                        💡 {insight}
                    </div>""", unsafe_allow_html=True)

with tab_settings:
    st.session_state.selected_sidebar_tab = "Settings"
    st.subheader("📋 Candidate Selection Settings")
    
    # Initialize defaults
    longlist_count = st.session_state.get('longlist_count', 200)
    shortlist_count = st.session_state.get('shortlist_count', 20)
    
    # Selection mode
    selection_mode = st.radio(
        "📊 Selection Method:",
        options=["Ranking-Based", "Score Threshold"],
        help="Choose how to categorize candidates"
    )
    
    if selection_mode == "Ranking-Based":
        st.info("📌 Select top N candidates by ranking")
        
        # Get total number of candidates if results exist
        max_candidates = len(st.session_state.results) if st.session_state.results else 500
        
        longlist_count = st.slider(
            "📋 Longlist Size",
            min_value=1,
            max_value=max(max_candidates, 200),
            value=min(200, max_candidates),
            help="Number of candidates to include in longlist"
        )
        
        shortlist_count = st.slider(
            "🎯 Shortlist Size",
            min_value=1,
            max_value=longlist_count,
            value=min(20, longlist_count),
            help="Number of top candidates for interviews (cannot exceed longlist)"
        )
        
        st.session_state.longlist_count = longlist_count
        st.session_state.shortlist_count = shortlist_count
        st.session_state.use_thresholds = False
        st.session_state.shortlist_threshold = 70
        st.session_state.longlist_threshold = 50
        
    else:  # Score Threshold-based
        st.info("📊 Every candidate is classified purely by their match score — no fixed count caps apply.")

        shortlist_threshold = st.slider(
            "🎯 Shortlist Threshold (%)",
            min_value=1,
            max_value=100,
            value=st.session_state.get('shortlist_threshold', 70),
            step=5,
            key="shortlist_thresh_slider",
            help="Score ≥ this value → automatically shortlisted for interview.",
        )

        # Constrain longlist max to one step below shortlist so the invariant
        # longlist < shortlist is enforced at the slider level, not just post-hoc.
        _ll_max = max(0, shortlist_threshold - 1)
        _ll_default = max(0, min(st.session_state.get('longlist_threshold', 50), _ll_max))
        longlist_threshold = st.slider(
            "📋 Longlist Threshold (%)",
            min_value=0,
            max_value=_ll_max,
            value=_ll_default,
            step=5,
            key="longlist_thresh_slider",
            help="Score ≥ this value (but below shortlist threshold) → longlisted. Below → rejected.",
        )

        # Boundary validation — belt-and-suspenders after slider constraint
        _thresholds_valid = shortlist_threshold > longlist_threshold
        if not _thresholds_valid:
            st.error("⚠️ Shortlist threshold must be strictly higher than the longlist threshold.")
        else:
            # Visual score-band preview
            st.markdown(f"""
            <div style="border:1px solid #e2e8f0;border-radius:12px;overflow:hidden;
                        margin:16px 0;font-size:13px;font-weight:600;">
                <div style="background:#f0fdf4;border-bottom:1px solid #e2e8f0;
                            padding:10px 16px;display:flex;justify-content:space-between;">
                    <span>🎯 Shortlist</span>
                    <span style="color:#16a34a;">score ≥ {shortlist_threshold}%</span>
                </div>
                <div style="background:#eff6ff;border-bottom:1px solid #e2e8f0;
                            padding:10px 16px;display:flex;justify-content:space-between;">
                    <span>📋 Longlist</span>
                    <span style="color:#2563eb;">{longlist_threshold}% ≤ score &lt; {shortlist_threshold}%</span>
                </div>
                <div style="background:#fef2f2;padding:10px 16px;
                            display:flex;justify-content:space-between;">
                    <span>❌ Rejected</span>
                    <span style="color:#dc2626;">score &lt; {longlist_threshold}%</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # Persist — counts set to a high sentinel so downstream ranking-mode
        # slicing never accidentally caps threshold-classified results.
        st.session_state.use_thresholds = True
        st.session_state.shortlist_threshold = shortlist_threshold
        st.session_state.longlist_threshold = longlist_threshold
        st.session_state.shortlist_count = 9999
        st.session_state.longlist_count = 9999

    st.divider()
    if st.session_state.get('use_thresholds', False):
        _st = st.session_state.get('shortlist_threshold', 70)
        _lt = st.session_state.get('longlist_threshold', 50)
        st.caption(f"🎯 Shortlist: candidates with score ≥ {_st}%")
        st.caption(f"📋 Longlist:  candidates with {_lt}% ≤ score < {_st}%")
        st.caption(f"❌ Rejected:  candidates with score < {_lt}%")
    else:
        st.caption(f"📊 Longlist: top {longlist_count} candidates by score")
        st.caption(f"🎯 Shortlist: top {shortlist_count} candidates by score")

    st.divider()
    if st.button("🗑️ Clear saved job titles", type="secondary"):
        save_job_titles([])
        if os.path.exists(JOB_TITLE_FILE):
            try:
                os.remove(JOB_TITLE_FILE)
            except Exception:
                pass
        st.success("Saved job titles removed. Refresh the page to reload the default role list.")

    # ── OpenAI GPT Configuration ──────────────────────────────────────────────
    st.divider()
    st.subheader("🤖 OpenAI GPT Deep Analysis")
    st.markdown(
        "Connect your OpenAI API key to unlock **GPT-powered analysis**: "
        "genuine semantic understanding, chain-of-thought reasoning, nuanced executive "
        "summaries, and contextual skill gap recommendations. "
        "Get a key at [platform.openai.com](https://platform.openai.com)."
    )

    # Seed from env var on first load
    if "openai_api_key" not in st.session_state:
        st.session_state.openai_api_key = os.getenv("OPENAI_API_KEY", "")

    api_key_input = st.text_input(
        "OpenAI API Key",
        value=st.session_state.openai_api_key,
        type="password",
        placeholder="sk-...",
        help="Stored only in this browser session — never written to disk from here.",
    )

    col_save, col_status = st.columns([1, 2])
    with col_save:
        if st.button("💾 Save & Test Key", use_container_width=True):
            if api_key_input.strip():
                test_analyzer = LLMAnalyzer(api_key_input.strip())
                with st.spinner("Testing connection to OpenAI..."):
                    if test_analyzer.validate_key():
                        st.session_state.openai_api_key = api_key_input.strip()
                        st.session_state.llm_analyzer = test_analyzer
                        st.success("✅ API key verified — GPT deep analysis enabled!")
                    else:
                        st.error("❌ Key validation failed. Check the key and try again.")
            else:
                st.warning("Please enter an API key first.")

    with col_status:
        llm = st.session_state.get("llm_analyzer")
        if llm:
            calls = llm.total_api_calls
            cost = llm.estimated_cost_usd
            st.markdown(
                f'<div style="background:#f0fdf4;border:1px solid #86efac;border-radius:8px;'
                f'padding:10px 14px;color:#166534;font-weight:600;margin-top:4px;">'
                f"🟢 GPT Active — {calls} API call{'s' if calls != 1 else ''} this session "
                f"(≈ ${cost:.4f} est. cost)"
                f"</div>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<div style="background:#fefce8;border:1px solid #fde047;border-radius:8px;'
                'padding:10px 14px;color:#854d0e;font-weight:600;margin-top:4px;">'
                "🟡 GPT Not Configured — keyword matching only (set OPENAI_API_KEY in .env)"
                "</div>",
                unsafe_allow_html=True,
            )

with tab_pool:
    st.subheader("🌐 Candidate Pool Manager")
    st.info("Manage candidates across multiple job openings")
        
    # Initialize candidate pool
    if 'candidate_pool' not in st.session_state:
        st.session_state.candidate_pool = CandidatePool()
        
    pool = st.session_state.candidate_pool
        
    # Pool Statistics - Professional Cards
    stats = pool.get_pool_statistics()
    shortlist_total = sum(job.get('shortlist_count', 0) for job in pool.get_all_jobs())
    
    st.markdown("""
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-bottom: 2rem;">
        <div class="metric-card">
            <div class="metric-value">{:,}</div>
            <div class="metric-label">Total Candidates</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">{:,}</div>
            <div class="metric-label">Active Jobs</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">{:.1f}%</div>
            <div class="metric-label">Average Score</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">{:,}</div>
            <div class="metric-label">Total Shortlisted</div>
        </div>
    </div>
    """.format(
        stats['total_candidates'],
        stats['total_jobs'], 
        stats['average_score'],
        shortlist_total
    ), unsafe_allow_html=True)
    
    # Pool actions
    pool_action = st.radio("Choose action:", options=["View All Pools", "View by Job", "Export Pool", "Clear Pool"])
    
    if pool_action == "View All Pools":
        # Show summary of all job pools
        jobs = pool.get_all_jobs()
        if jobs:
            st.subheader("📋 Job Pools Overview")
            for job in jobs:
                with st.expander(f"🏢 {job['title']} (ID: {job['job_id']})"):
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Total Candidates", job.get('candidate_count', 0))
                    with col2:
                        st.metric("Shortlisted", job.get('shortlist_count', 0))
                    with col3:
                        st.metric("Longlisted", job.get('longlist_count', 0))
                    with col4:
                        st.metric("Min Score", f"{job.get('min_score', 50)}%")

                    st.markdown(f"**Folder:** `{job.get('folder', 'N/A')}`")
                    
                    # Show candidates by category
                    candidates = pool.get_candidates_by_job(job['job_id'])
                    if candidates:
                        categories = ['shortlist', 'longlist', 'rejected']
                        tabs = st.tabs([f"🎯 Shortlist ({len([c for c in candidates if c.get('category') == 'shortlist'])})", 
                                      f"📋 Longlist ({len([c for c in candidates if c.get('category') == 'longlist'])})", 
                                      f"❌ Rejected ({len([c for c in candidates if c.get('category') == 'rejected'])})"])
                        
                        for i, category in enumerate(categories):
                            with tabs[i]:
                                cat_candidates = [c for c in candidates if c.get('category') == category]
                                if cat_candidates:
                                    cat_df = pd.DataFrame([{
                                        'Candidate': _candidate_name(c['filename']),
                                        'Email': c['email'],
                                        'Score': f"{c['final_score']}%",
                                        'Seniority': c['cv_seniority'].title(),
                                        'Matched Skills': len(c['matched_skills']),
                                        'Added': c['added_date'][:10]
                                    } for c in cat_candidates])
                                    st.dataframe(cat_df, use_container_width=True, hide_index=True)
                                else:
                                    st.info(f"No candidates in {category}")
        else:
            st.info("No job pools created yet")
    
    elif pool_action == "View by Job":
        jobs = pool.get_all_jobs()
        if jobs:
            job_options = [f"{job['title']} ({job['job_id']})" for job in jobs]
            selected_job_display = st.selectbox("Select Job Pool:", job_options)
            
            if selected_job_display:
                selected_job_id = selected_job_display.split('(')[-1].rstrip(')')
                candidates = pool.get_candidates_by_job(selected_job_id)
                selected_job = next((j for j in jobs if j['job_id'] == selected_job_id), None)

                if selected_job:
                    st.markdown(f"**Folder:** `{selected_job.get('folder', 'N/A')}`")
                    if selected_job.get('folder') and Path(selected_job.get('folder')).exists():
                        if st.button(f"📁 Open folder for {selected_job['title']}"):
                            try:
                                folder_path = selected_job.get('folder')
                                if sys.platform.startswith('win'):
                                    os.startfile(folder_path)
                                elif sys.platform == 'darwin':
                                    subprocess.run(['open', folder_path], check=False)
                                else:
                                    subprocess.run(['xdg-open', folder_path], check=False)
                            except Exception as open_err:
                                st.error(f"Could not open folder: {open_err}")
                    else:
                        st.warning("Pool folder not yet created on disk for this job.")

                if candidates:
                    st.subheader(f"👥 Candidates for {selected_job_display}")
                    pool_df = pd.DataFrame([{
                        'Candidate': _candidate_name(c['filename']),
                        'Email': c['email'],
                        'Category': c.get('category', 'unassigned').title(),
                        'Score': f"{c['final_score']}%",
                        'Seniority': c['cv_seniority'].title(),
                        'Matched Skills': len(c['matched_skills']),
                        'Added': c['added_date'][:10]
                    } for c in candidates])
                    st.dataframe(pool_df, use_container_width=True, hide_index=True)
                else:
                    st.info("No candidates in this job pool")
        else:
            st.info("No job pools available")
    
    elif pool_action == "Export Pool":
        csv_data = pool.export_candidates_csv()
        if csv_data:
            st.download_button(
                label="📥 Download Pool as CSV",
                data=csv_data,
                file_name=f"Candidate_Pool_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        else:
            st.info("No candidates to export")
    
    elif pool_action == "Clear Pool":
        if st.button("🗑️ Clear All Candidates", use_container_width=True):
            pool.clear_pool()
            st.session_state.candidate_pool = CandidatePool()
            st.success("✓ Pool cleared!")

# Main content
if process_button and job_title and job_description and uploaded_files:
    # Clear previous results to prevent UI "ghosting"
    st.session_state.results = []
    
    progress_bar = st.progress(0)
    status_text = st.empty()

    results, errors = process_cv_batch(
        uploaded_files,
        job_description,
        matcher,
        llm_analyzer=st.session_state.get('llm_analyzer'),
        progress_cb=lambda frac: progress_bar.progress(frac),
        status_cb=lambda msg: status_text.text(msg),
    )

    for fname, err_msg in errors:
        st.error(f"Error processing {fname}: {err_msg}")

    status_text.empty()
    progress_bar.empty()
    
    st.markdown("""
    <div style="background: #ecfdf5; border: 1px solid #10b981; border-radius: 12px; padding: 1.5rem; margin: 1rem 0; display: flex; align-items: center; gap: 1rem;">
        <div style="font-size: 2rem;">✅</div>
        <div>
            <div style="color: #065f46; font-weight: 700; font-size: 1.1rem;">Analysis Pipeline Complete</div>
            <div style="color: #047857; font-size: 0.9rem;">{} candidate(s) processed and synchronized to Talent Cloud.</div>
        </div>
    </div>
    """.format(len(results)), unsafe_allow_html=True)
    
    # Automatically assign candidates to job pools
    if 'candidate_pool' not in st.session_state:
        st.session_state.candidate_pool = CandidatePool()
    
    pool = st.session_state.candidate_pool
    st.session_state.current_job_title = job_title
    
    # Auto-assign candidates to pools (mode-aware)
    _use_ranking = not st.session_state.get('use_thresholds', False)
    job_id, assigned = pool.auto_assign_candidates(
        results,
        job_title,
        job_description,
        shortlist_threshold=st.session_state.get('shortlist_threshold', 70),
        longlist_threshold=st.session_state.get('longlist_threshold', 50),
        use_ranking_mode=_use_ranking,
        shortlist_count=st.session_state.get('shortlist_count', 20),
        longlist_count=st.session_state.get('longlist_count', 200),
    )
    
    # Summary of assignment
    st.markdown(f"""
    <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; margin-bottom: 2rem;">
        <div class="metric-card">
            <div class="metric-val" style="color: #10b981; font-size: 1.5rem;">{len(assigned['shortlist'])}</div>
            <div class="metric-lab" style="font-size: 0.7rem;">Shortlisted</div>
        </div>
        <div class="metric-card">
            <div class="metric-val" style="color: #2563eb; font-size: 1.5rem;">{len(assigned['longlist'])}</div>
            <div class="metric-lab" style="font-size: 0.7rem;">Longlisted</div>
        </div>
        <div class="metric-card">
            <div class="metric-val" style="color: #ef4444; font-size: 1.5rem;">{len(assigned['rejected'])}</div>
            <div class="metric-lab" style="font-size: 0.7rem;">Filtered</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # SAVE RESULTS TO SESSION STATE
    st.session_state.results = results
    st.rerun()




# ── Results Processing & Rendering (New) ──────────────────────────────────────
if st.session_state.results:
    results = st.session_state.results
    report_gen = ReportGenerator()
    
    # Sorting and Categorization
    rejected_candidates = []
    if st.session_state.get('use_thresholds', False):
        categorized = report_gen.categorize_by_thresholds(
            results,
            shortlist_threshold=st.session_state.shortlist_threshold,
            longlist_threshold=st.session_state.longlist_threshold,
            shortlist_count=st.session_state.shortlist_count,
            longlist_count=st.session_state.longlist_count
        )
        results_sorted = categorized['shortlist'] + categorized['longlist']
        results_sorted = sorted(results_sorted, key=lambda x: x['final_score'], reverse=True)
        rejected_candidates = categorized['rejected']
    else:
        results_sorted = sorted(results, key=lambda x: x['final_score'], reverse=True)

    # Dashboard Metrics
    avg_score = sum(r['final_score'] for r in results) / len(results)
    top_score = results_sorted[0]['final_score'] if results_sorted else 0
    
    st.markdown(f"""
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 1.5rem; margin: 2rem 0;">
        <div class="metric-card">
            <div class="metric-lab">Top Match</div>
            <div class="metric-val" style="color: #2563eb;">{top_score}%</div>
        </div>
        <div class="metric-card">
            <div class="metric-lab">Average Alignment</div>
            <div class="metric-val">{avg_score:.1f}%</div>
        </div>
        <div class="metric-card">
            <div class="metric-lab">Processing Confidence</div>
            <div class="metric-val" style="color: #059669;">High AI</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Candidate list (Helix card rows) ──────────────────────────────────────
    list_meta = f"Showing <b style='color:#0F1115'>{len(results_sorted)}</b> of <b style='color:#0F1115'>{len(results)}</b> candidates"
    st.markdown(f'<div style="font-size:13px;color:#9CA3AF;font-weight:500;padding:4px 0 12px;">{list_meta}</div>', unsafe_allow_html=True)

    rows_html = ""
    for idx, r in enumerate(results_sorted, 1):
        score = r['final_score']
        opacity_class = "" if score >= 80 else " mid" if score >= 60 else " low"
        display_name = _candidate_name(r['filename'])
        initials = "".join(w[0].upper() for w in display_name.split()[:2]) or display_name[:2].upper()
        seniority = r['cv_seniority'].title()
        matched = len(r['matched_skills'])
        has_gpt = "· GPT" if r.get('llm_analysis') else ""
        rows_html += f"""
        <div class="cand-row">
            <div class="cand-avatar">{initials}</div>
            <div>
                <div class="cand-name">#{idx} {display_name}</div>
                <div class="cand-meta">{seniority} · {matched} skills matched{has_gpt}</div>
            </div>
            <div class="score-circle{opacity_class}">{score:.0f}</div>
        </div>"""

    st.markdown(f'<div class="cand-list">{rows_html}</div>', unsafe_allow_html=True)

    # ── Native Section Navigation (Option B: horizontal column row) ───────────
    st.divider()
    _nc1, _nc2, _nc3, _nc4, _nc5 = st.columns(5)
    _nav_defs = [
        (_nc1, "📊 Candidate\nAnalysis",    "#sec-analysis"),
        (_nc2, "⚖️ Comparative\nAnalysis",  "#sec-compare"),
        (_nc3, "🎯 HR\nRecommendations",    "#sec-recommend"),
        (_nc4, "📧 Email\n& Reports",       "#sec-reports"),
        (_nc5, "🎤 Interview\nPrep",        "#sec-interview"),
    ]
    for _col, _label, _href in _nav_defs:
        with _col:
            st.markdown(
                f'<a href="{_href}" style="display:block;text-align:center;padding:10px 6px;'
                'background:#f8fafc;border-radius:10px;text-decoration:none;'
                'color:#374151;font-size:12px;font-weight:600;border:1px solid #e2e8f0;'
                f'white-space:pre-line;line-height:1.4;">{_label}</a>',
                unsafe_allow_html=True,
            )
    st.divider()

    # ── Section 1: Detailed Candidate Analysis ────────────────────────────────
    st.markdown('<div id="sec-analysis"></div>', unsafe_allow_html=True)
    st.subheader("📊 Detailed Candidate Analysis")
    st.caption("Individual scoring breakdown, skill profiles, gap analysis & roadmaps")
    
    for idx, result in enumerate(results_sorted, 1):
        with st.expander(f"#{idx} — {_candidate_name(result['filename'])} ({result.get('confidence_level', 'Evaluated')})", expanded=(idx == 1)):
            
            # 1. Executive Summary — LLM version takes priority, keyword fallback otherwise
            llm = result.get('llm_analysis')
            if llm and llm.get('executive_summary'):
                render_gpt_card(llm)
            elif result.get('strategic_summary'):
                render_keyword_summary_card(result['strategic_summary'])

            # Live streaming summary button (only when analyzer is available + cv text present)
            _stream_analyzer = st.session_state.get('llm_analyzer')
            _cv_txt = result.get('cv_text', '')
            if _stream_analyzer and _cv_txt:
                if st.button(
                    "⚡ Stream Live AI Summary",
                    key=f"stream_live_{idx}",
                    help="Generate a quick executive summary streamed live, token by token",
                ):
                    st.markdown("**Live AI Executive Summary:**")
                    st.write_stream(
                        _stream_analyzer.stream_executive_summary(_cv_txt, job_description, result)
                    )

            # 2. Score gauge + breakdown
            final_score = result['final_score']
            confidence = result.get('confidence_level', '')

            col_a, col_b = st.columns([1, 2])
            with col_a:
                render_score_gauge(final_score, confidence)

            with col_b:
                scores = result.get('score_breakdown', {})
                render_score_breakdown(scores)

            st.divider()

            # 3. Gap Analysis & Roadmap
            _raw_areas = result.get('improvement_areas', [])
            # Strip markdown and filter out any residual template filler
            _gap_items = [
                re.sub(r'\*\*(.+?)\*\*', r'\1', a).strip()
                for a in _raw_areas
                if len(a.strip()) > 20
                and 'Study fundamentals of' not in a
                and 'Acquire hands-on experience' not in a
            ]
            if _gap_items:
                st.markdown("### 🛠️ Key Concerns for This Candidate")
                _gaps_html = ""
                _icons = ["⚠️", "📉", "🎯", "💼"]
                for _gi, _gap_text in enumerate(_gap_items):
                    _icon = _icons[_gi % len(_icons)]
                    _gaps_html += f"""
                    <div style="display:flex;gap:14px;align-items:flex-start;
                                background:#fffbf0;border:1px solid #fde68a;border-radius:10px;
                                padding:14px 18px;margin-bottom:10px;
                                box-shadow:0 1px 3px rgba(0,0,0,0.04);">
                        <div style="font-size:20px;flex-shrink:0;margin-top:1px;">{_icon}</div>
                        <div style="font-size:14px;color:#374151;line-height:1.7;">{_gap_text}</div>
                    </div>"""
                st.markdown(_gaps_html, unsafe_allow_html=True)

            st.divider()

            # 4. Verified Skills
            st.markdown("### 🎯 Verified Technical Expertise")
            valid_skills = [s.strip() for s in result.get('matched_skills', []) if len(s.strip()) > 1]
            if valid_skills:
                _skills_html = '<div style="display:flex;flex-wrap:wrap;gap:8px;margin-top:4px;">'
                for skill in valid_skills:
                    proficiency = result.get('skill_proficiency', {}).get(skill, 'Verified')
                    _skills_html += f"""<div style="background:#f0fdf4;border:1px solid #bbf7d0;
                        color:#15803d;padding:5px 12px;border-radius:20px;font-size:13px;font-weight:500;">
                        ✓ {skill.title()} <span style="opacity:.65;font-size:11px;">· {proficiency}</span></div>"""
                _skills_html += '</div>'
                st.markdown(_skills_html, unsafe_allow_html=True)
            else:
                st.info("🔍 No specific technical skill matches identified.")

            # 5. Priority Development Areas
            # When GPT analysis is available its critical_gaps section (below) is authoritative —
            # don't also show the Phase 1 keyword-based recommendations which have no real insight.
            if not llm:
                st.markdown("### 📈 Priority Development Areas")
                blacklist_categories = ['languages', 'skills', 'tools', 'technologies',
                                        'experience', 'development', 'management']
                valid_recommendations = [
                    rec for rec in result.get('recommendations', [])
                    if len(rec.get('skill', '').strip()) > 1
                    and rec.get('skill', '').lower() not in blacklist_categories
                ]
                if valid_recommendations:
                    _recs_html = ""
                    for rec in valid_recommendations[:6]:
                        _effort = rec.get('effort', 2)
                        _priority_label = "High Priority" if _effort >= 3 else "Medium Priority" if _effort >= 2 else "Lower Priority"
                        _priority_bg    = "#fef2f2" if _effort >= 3 else "#fffbeb" if _effort >= 2 else "#f0f9ff"
                        _priority_color = "#dc2626" if _effort >= 3 else "#d97706" if _effort >= 2 else "#0369a1"
                        _border_color   = "#fca5a5" if _effort >= 3 else "#fcd34d" if _effort >= 2 else "#7dd3fc"
                        _suggestion = re.sub(r'\*\*(.+?)\*\*', r'\1', rec.get('suggestion', '')).strip()
                        _impact     = re.sub(r'\*\*(.+?)\*\*', r'\1', rec.get('impact', 'Career growth')).strip()
                        _recs_html += f"""
                        <div style="background:#fff;border:1px solid {_border_color};border-radius:10px;
                                    padding:16px 18px;margin-bottom:12px;box-shadow:0 1px 3px rgba(0,0,0,0.04);">
                            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
                                <div style="font-size:15px;font-weight:700;color:#0f172a;">
                                    {rec.get('skill','Skill').title()}
                                </div>
                                <span style="background:{_priority_bg};color:{_priority_color};
                                             border:1px solid {_border_color};padding:3px 10px;
                                             border-radius:20px;font-size:11px;font-weight:700;
                                             letter-spacing:.04em;">{_priority_label}</span>
                            </div>
                            <div style="font-size:13.5px;color:#374151;line-height:1.6;margin-bottom:10px;">
                                {_suggestion}
                            </div>
                            <div style="display:flex;gap:16px;flex-wrap:wrap;">
                                <div style="font-size:12px;color:#6b7280;">
                                    <span style="font-weight:600;color:#374151;">Impact:</span> {_impact}
                                </div>
                                <div style="font-size:12px;color:#6b7280;">
                                    <span style="font-weight:600;color:#374151;">Estimated effort:</span> {rec.get('time', '2–4 weeks')}
                                </div>
                            </div>
                        </div>"""
                    st.markdown(_recs_html, unsafe_allow_html=True)
                else:
                    st.info("💡 Add your OpenAI API key in Settings to get AI-powered skill gap analysis for this candidate.")

            # 7. Career Advice (keyword-based, always shown)
            if result.get('career_advice'):
                st.info(f"💡 **Strategic Career Guidance:** {result['career_advice']}")

            # 8. GPT Deep Analysis
            if llm:
                st.divider()
                st.markdown("### 🤖 AI Deep Analysis")

                gaps = llm.get('critical_gaps', [])
                focus_areas = llm.get('interview_focus_areas', [])
                narrative = llm.get('career_fit_narrative', '')

                if gaps:
                    st.markdown(
                        '<div style="font-size:13px;font-weight:700;letter-spacing:.07em;'
                        'text-transform:uppercase;color:#6b7280;margin-bottom:10px;">'
                        'Critical skill gaps identified by AI</div>',
                        unsafe_allow_html=True
                    )
                    _gaps_gpt_html = ""
                    for gap in gaps:
                        _p = gap.get('priority', 'medium').lower()
                        _p_label = "High priority" if _p == 'high' else "Medium priority" if _p == 'medium' else "Lower priority"
                        _p_color = "#dc2626" if _p == 'high' else "#d97706" if _p == 'medium' else "#16a34a"
                        _p_bg    = "#fef2f2" if _p == 'high' else "#fffbeb" if _p == 'medium' else "#f0fdf4"
                        _p_border = "#fca5a5" if _p == 'high' else "#fcd34d" if _p == 'medium' else "#86efac"
                        _importance = re.sub(r'\*\*(.+?)\*\*', r'\1', gap.get('importance', '')).strip()
                        _learning   = re.sub(r'\*\*(.+?)\*\*', r'\1', gap.get('learning_path', '')).strip()
                        _gaps_gpt_html += f"""
                        <div style="background:#fff;border:1px solid {_p_border};border-radius:10px;
                                    padding:16px 18px;margin-bottom:12px;box-shadow:0 1px 3px rgba(0,0,0,0.04);">
                            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
                                <div style="font-size:15px;font-weight:700;color:#0f172a;">
                                    {gap.get('skill','').title()}
                                </div>
                                <div style="display:flex;gap:8px;align-items:center;">
                                    <span style="background:{_p_bg};color:{_p_color};border:1px solid {_p_border};
                                                 padding:3px 10px;border-radius:20px;font-size:11px;font-weight:700;">
                                        {_p_label}
                                    </span>
                                    <span style="font-size:12px;color:#6b7280;">
                                        {gap.get('estimated_time','—')}
                                    </span>
                                </div>
                            </div>
                            <div style="font-size:13px;color:#64748b;font-style:italic;margin-bottom:8px;">
                                {_importance}
                            </div>
                            <div style="background:#f8fafc;border-radius:6px;padding:10px 12px;
                                        font-size:13.5px;color:#1e293b;line-height:1.6;">
                                <span style="font-weight:600;color:#374151;">Recommended path: </span>{_learning}
                            </div>
                        </div>"""
                    st.markdown(_gaps_gpt_html, unsafe_allow_html=True)
                else:
                    st.success("✅ No critical skill gaps identified — this candidate is a strong technical match.")

                if focus_areas:
                    _fa_html = (
                        '<div style="font-size:13px;font-weight:700;letter-spacing:.07em;'
                        'text-transform:uppercase;color:#6b7280;margin:16px 0 10px 0;">'
                        'Recommended interview focus areas</div>'
                        '<div style="display:flex;flex-direction:column;gap:8px;">'
                    )
                    for _i, _area in enumerate(focus_areas, 1):
                        _fa_html += f"""
                        <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;
                                    padding:10px 14px;font-size:13.5px;color:#374151;display:flex;gap:10px;">
                            <span style="font-weight:700;color:#6366f1;min-width:20px;">{_i}.</span>
                            <span>{_area}</span>
                        </div>"""
                    _fa_html += '</div>'
                    st.markdown(_fa_html, unsafe_allow_html=True)

                if narrative:
                    _narrative_clean = re.sub(r'\*\*(.+?)\*\*', r'\1', narrative).strip()
                    st.markdown(
                        f'<div style="background:#f0f9ff;border:1px solid #bae6fd;border-radius:10px;'
                        f'padding:14px 18px;margin-top:14px;font-size:14px;color:#0369a1;line-height:1.65;">'
                        f'<span style="font-weight:700;">🧭 Long-term career fit: </span>{_narrative_clean}'
                        f'</div>',
                        unsafe_allow_html=True
                    )

            st.divider()
            
            # Individual PDF & Text Report Downloads
            pdf_col, txt_col, pool_col = st.columns(3)
            
            with pdf_col:
                try:
                    pdf_individual = report_gen.generate_individual_pdf_report(result)
                    st.download_button(
                        label=f"📄 Download PDF Report",
                        data=pdf_individual,
                        file_name=f"ATS_Individual_{Path(result['filename']).stem}_{datetime.now().strftime('%Y%m%d')}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
                except Exception as e:
                    st.error(f"PDF generation error: {str(e)[:50]}")
            
            with txt_col:
                detailed_txt = report_gen.generate_detailed_candidate_report(result)
                st.download_button(
                    label=f"📝 Download Text Report",
                    data=detailed_txt,
                    file_name=f"ATS_Individual_{Path(result['filename']).stem}_{datetime.now().strftime('%Y%m%d')}.txt",
                    mime="text/plain",
                    use_container_width=True
                )
            
            with pool_col:
                # Show pool assignment status
                pool = st.session_state.candidate_pool
                candidate_in_pool = any(c['filename'] == result['filename'] for c in pool.get_all_candidates())
                if candidate_in_pool:
                    st.success("✅ Auto-assigned to job pool")
                else:
                    st.info("⏳ Will be auto-assigned after analysis")
            
            # Show job recommendations
            pool = st.session_state.candidate_pool
            all_jobs = pool.get_all_jobs()
            if all_jobs:
                recommendations = pool.get_job_recommendations(result, all_jobs)
                if recommendations:
                    st.divider()
                    st.markdown("**🎯 Recommended For Other Jobs:**")
                    for rec in recommendations:
                        st.markdown(f"""
                        <div class="recommendation-box">
                        <strong>→ {rec['job_title']}</strong><br/>
                        Fit Score: {rec['fit_score']:.0f}% | {rec['reason']}
                        </div>
                        """, unsafe_allow_html=True)
    
    # ── Section 2: Comparative Analysis ──────────────────────────────────────
    if len(results_sorted) > 1:
        st.markdown('<div id="sec-compare"></div>', unsafe_allow_html=True)
        st.divider()
        st.subheader("⚖️ Comparative Analysis")
        st.caption("Dimension-by-dimension comparison, winner banner & candidate verdicts")

        _cpal = ['#6366f1', '#f59e0b', '#10b981', '#ef4444', '#8b5cf6', '#06b6d4']

        def _skills_list(r, key):
            """Return skills as a list regardless of whether the field is a dict or list."""
            val = r.get(key, [])
            return list(val.keys()) if isinstance(val, dict) else list(val)

        def _get_score(r, path):
            parts = path.split('.')
            v = r
            for p in parts:
                v = v.get(p, 0) if isinstance(v, dict) else 0
            return float(v or 0)

        _best = results_sorted[0]
        _best_name = _candidate_name(_best.get('filename', ''))
        _best_score = _best['final_score']
        _best_llm = _best.get('llm_analysis') or {}
        _best_rec = _best_llm.get('interview_recommendation', '')
        _best_score_color = '#16a34a' if _best_score >= 75 else '#f59e0b' if _best_score >= 50 else '#ef4444'

        # ── Winner banner (all values pre-computed — no nested f-strings) ──────
        _rec_badge = ''
        if _best_rec:
            _rc = {'Shortlist': '#16a34a', 'Consider': '#d97706', 'Decline': '#dc2626'}.get(_best_rec, '#6366f1')
            _rec_badge = (
                f'<span style="background:{_rc}22;color:{_rc};font-weight:700;'
                f'font-size:12px;padding:3px 10px;border-radius:20px;margin-left:10px;">'
                f'{_best_rec}</span>'
            )
        st.markdown(
            f'<div style="background:#f0fdf4;border:1.5px solid #86efac;border-radius:14px;'
            f'padding:22px 28px;margin-bottom:20px;">'
            f'<div style="font-size:11px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;'
            f'color:#16a34a;margin-bottom:6px;">Top Recommended Candidate</div>'
            f'<div style="font-size:24px;font-weight:800;color:#0f172a;margin-bottom:6px;">'
            f'🏆 {_best_name}</div>'
            f'<div style="font-size:14px;color:#374151;">Overall match score: '
            f'<strong style="color:{_best_score_color};">{_best_score:.0f}%</strong>'
            f'{_rec_badge}</div>'
            f'</div>',
            unsafe_allow_html=True
        )

        # ── Dimension comparison — one st.markdown per dimension row ───────────
        _dims = [
            ("Overall Match Score", "final_score"),
            ("Skills Match",        "score_breakdown.skills_match"),
            ("Experience",          "score_breakdown.experience_relevance"),
            ("Keyword Overlap",     "score_breakdown.semantic_similarity"),
            ("Culture Fit",         "score_breakdown.culture_fit"),
            ("Seniority Fit",       "score_breakdown.seniority_alignment"),
        ]

        st.markdown(
            '<div style="font-size:11px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;'
            'color:#9ca3af;margin:18px 0 10px 0;">Dimension-by-dimension comparison</div>',
            unsafe_allow_html=True
        )

        for _dim_label, _dim_key in _dims:
            # Build entire row as one string — no conditionals inside HTML
            _row = (
                f'<div style="margin-bottom:16px;">'
                f'<div style="font-size:13px;font-weight:700;color:#374151;margin-bottom:6px;">'
                f'{_dim_label}</div>'
            )
            for _ci, _r in enumerate(results_sorted):
                _cn = _candidate_name(_r['filename'])
                _v  = _get_score(_r, _dim_key)
                _dot_col  = _cpal[_ci % len(_cpal)]
                _bar_col  = '#16a34a' if _v >= 75 else '#f59e0b' if _v >= 50 else '#ef4444'
                _v_int    = int(_v)
                _row += (
                    f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:5px;">'
                    f'<div style="width:130px;font-size:12px;color:#6b7280;'
                    f'white-space:nowrap;overflow:hidden;text-overflow:ellipsis;flex-shrink:0;">'
                    f'<span style="display:inline-block;width:9px;height:9px;border-radius:50%;'
                    f'background:{_dot_col};margin-right:6px;vertical-align:middle;"></span>'
                    f'{_cn}</div>'
                    f'<div style="flex:1;background:#f1f5f9;border-radius:4px;height:12px;overflow:hidden;">'
                    f'<div style="width:{_v_int}%;height:100%;background:{_bar_col};border-radius:4px;"></div>'
                    f'</div>'
                    f'<div style="width:36px;text-align:right;font-size:12px;font-weight:700;'
                    f'color:{_bar_col};">{_v_int}</div>'
                    f'</div>'
                )
            _row += '</div>'
            st.markdown(_row, unsafe_allow_html=True)

        # ── Candidate verdict cards ────────────────────────────────────────────
        st.markdown(
            '<div style="font-size:11px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;'
            'color:#9ca3af;margin:24px 0 12px 0;">Candidate verdicts</div>',
            unsafe_allow_html=True
        )
        _card_cols = st.columns(min(len(results_sorted), 3))
        _ranks = ['🥇', '🥈', '🥉']
        for _ci, _r in enumerate(results_sorted):
            _cn     = _candidate_name(_r['filename'])
            _sc     = _r['final_score']
            _col    = _cpal[_ci % len(_cpal)]
            _scol   = '#16a34a' if _sc >= 75 else '#f59e0b' if _sc >= 50 else '#ef4444'
            _llm    = _r.get('llm_analysis') or {}
            _rec    = _llm.get('interview_recommendation', '')
            _rank   = _ranks[_ci] if _ci < 3 else f'#{_ci + 1}'

            # Matched and missing — handle list or dict
            _match_list   = _skills_list(_r, 'matched_skills')[:3]
            _missing_list = [s for s in _skills_list(_r, 'missing_skills') if len(s) > 2][:3]
            _strengths    = [re.sub(r'\*\*(.+?)\*\*', r'\1', s).strip()
                             for s in _llm.get('key_strengths', [])[:2]]

            # Build card as one clean string
            _card = (
                f'<div style="background:#fff;border-top:4px solid {_col};border:1px solid #e2e8f0;'
                f'border-radius:12px;padding:18px;box-shadow:0 2px 6px rgba(0,0,0,0.05);">'
                f'<div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:10px;">'
                f'<div><div style="font-size:20px;">{_rank}</div>'
                f'<div style="font-size:15px;font-weight:800;color:#0f172a;">{_cn}</div></div>'
                f'<div style="text-align:right;">'
                f'<div style="font-size:28px;font-weight:800;color:{_scol};line-height:1;">{_sc:.0f}</div>'
                f'<div style="font-size:10px;color:#9ca3af;">/ 100</div></div>'
                f'</div>'
            )
            if _rec:
                _rbg = {'Shortlist': '#f0fdf4', 'Consider': '#fffbeb', 'Decline': '#fef2f2'}.get(_rec, '#f8fafc')
                _rcl = {'Shortlist': '#16a34a', 'Consider': '#d97706', 'Decline': '#dc2626'}.get(_rec, '#6b7280')
                _card += (
                    f'<div style="background:{_rbg};color:{_rcl};font-size:11px;font-weight:700;'
                    f'letter-spacing:.06em;text-transform:uppercase;padding:4px 10px;'
                    f'border-radius:20px;display:inline-block;margin-bottom:10px;">{_rec}</div>'
                )
            show_skills = _strengths or _match_list
            if show_skills:
                _card += (
                    '<div style="font-size:11px;font-weight:700;color:#9ca3af;'
                    'text-transform:uppercase;letter-spacing:.06em;margin-bottom:5px;">'
                    + ('Strengths' if _strengths else 'Matched skills') + '</div>'
                )
                for _s in (show_skills):
                    _card += f'<div style="font-size:12px;color:#374151;margin-bottom:3px;">&#10003; {_s.title()}</div>'
            if _missing_list:
                _card += (
                    '<div style="font-size:11px;font-weight:700;color:#9ca3af;'
                    'text-transform:uppercase;letter-spacing:.06em;margin:10px 0 5px 0;">Key gaps</div>'
                )
                for _g in _missing_list:
                    _card += f'<div style="font-size:12px;color:#dc2626;margin-bottom:3px;">&#10007; {_g.title()}</div>'
            _card += '</div>'

            with _card_cols[_ci % 3]:
                st.markdown(_card, unsafe_allow_html=True)
    
    # ── Section 3: HR Recommendations & Selection ────────────────────────────
    st.markdown('<div id="sec-recommend"></div>', unsafe_allow_html=True)
    st.divider()
    st.subheader("🎯 HR Recommendations & Selection")
    st.caption("Shortlist, longlist, tier verdicts & hiring next-steps")
    
    # Determine longlist and shortlist based on mode
    if st.session_state.get('use_thresholds', False):
        # Threshold-based: use categorized results
        shortlist = categorized['shortlist']
        longlist = categorized['longlist']
    else:
        # Ranking-based: use top N
        longlist_count = st.session_state.longlist_count
        shortlist_count = st.session_state.shortlist_count
        longlist = results_sorted[:longlist_count]
        shortlist = results_sorted[:shortlist_count]
    
    # Longlist & Shortlist Display (Robust Native Version)
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f'<div style="font-weight: 700; font-size: 1.1rem; color: #6366f1; margin-bottom: 1rem;">📋 LONGLIST ({len(longlist)})</div>', unsafe_allow_html=True)
        if longlist:
            long_df = pd.DataFrame([{
                'Rank': f"#{i+1}",
                'Candidate': _candidate_name(r['filename']),
                'Score': f"{r['final_score']}%"
            } for i, r in enumerate(longlist)])
            st.dataframe(long_df, hide_index=True, use_container_width=True)
            st.success(f"✓ {len(longlist)} selected")
        else:
            st.warning("No longlisted candidates")
            
    with col2:
        st.markdown(f'<div style="font-weight: 700; font-size: 1.1rem; color: #10b981; margin-bottom: 1rem;">🎯 SHORTLIST ({len(shortlist)})</div>', unsafe_allow_html=True)
        if shortlist:
            short_df = pd.DataFrame([{
                'Rank': f"#{i+1}",
                'Candidate': _candidate_name(r['filename']),
                'Fit': r.get('confidence_level', 'Strong')
            } for i, r in enumerate(shortlist)])
            st.dataframe(short_df, hide_index=True, use_container_width=True)
            st.info(f"ℹ️ {len(shortlist)} selected for interview")
        else:
            st.warning("No shortlisted candidates")

    
    # === RECOMMENDATIONS ===
    st.divider()
    st.markdown('<div class="premium-header">🎯 HR Recommendations</div>', unsafe_allow_html=True)
    st.markdown(
        '<p style="color:#6B7280;font-size:14px;margin-bottom:24px;">'
        f'Ranked assessment of all {len(results_sorted)} candidate(s) — sorted by match score.</p>',
        unsafe_allow_html=True,
    )

    if not results_sorted:
        st.warning("No candidates meet the minimum threshold. Adjust settings and re-run.")
    else:
        import re as _re2

        def _clean_name(filename):
            n = filename
            for ext in ('.pdf', '.PDF', '.txt', '.docx', '.doc'):
                n = n.replace(ext, '')
            n = _re2.sub(r'\b(cv|resume|job|curriculum|vitae|application|\d{4,})\b', '', n, flags=_re2.IGNORECASE)
            n = _re2.sub(r'[\s_\-\.]+', ' ', n).strip()
            words = [w for w in n.split() if len(w) > 1]
            return ' '.join(words[:2]).title() if words else filename.split('.')[0].title()

        def _strip_md(text):
            return _re2.sub(r'\*\*(.+?)\*\*', r'\1', text or '')

        all_cards_html = ""

        for _rank, _c in enumerate(results_sorted, 1):
            _score     = _c['final_score']
            _name      = _clean_name(_c['filename'])
            _seniority = _c.get('cv_seniority', 'unspecified').title()
            _matched   = [s.title() for s in _c.get('matched_skills', []) if len(s) > 1][:6]
            _missing   = [s.title() for s in _c.get('missing_skills', []) if len(s) > 1][:5]
            _summary   = _strip_md(_c.get('strategic_summary', ''))

            # GPT analysis takes priority for summary
            _llm = _c.get('llm_analysis') or {}
            if _llm.get('executive_summary'):
                _summary = _llm['executive_summary']
            _gpt_rec = _llm.get('interview_recommendation', '')

            # Tier colours and labels
            if _score >= 85:
                _border, _bg      = '#059669', '#f0fdf4'
                _badge_col        = '#059669'
                _label            = 'Excellent Match'
                _next_step        = 'Move to interview immediately. This is a top-priority candidate who meets or exceeds all core requirements.'
                _hr_note          = 'Allocate senior interviewer time. Candidate is likely fielding competing offers.'
            elif _score >= 70:
                _border, _bg      = '#2563eb', '#eff6ff'
                _badge_col        = '#2563eb'
                _label            = 'Strong Match'
                _next_step        = 'Schedule a technical interview within the week. Explore the identified skill gaps during the conversation.'
                _hr_note          = 'Ask about learning agility and recent upskilling. Gaps are bridgeable.'
            elif _score >= 60:
                _border, _bg      = '#d97706', '#fffbeb'
                _badge_col        = '#d97706'
                _label            = 'Moderate Match'
                _next_step        = 'Consider for a growth-focused or junior variant of the role, or hold for a future opening.'
                _hr_note          = 'Discuss onboarding support and a structured 90-day ramp plan if moving forward.'
            else:
                _border, _bg      = '#dc2626', '#fef2f2'
                _badge_col        = '#dc2626'
                _label            = 'Weak Match'
                _next_step        = 'Not recommended for this role at this time. Send a respectful rejection.'
                _hr_note          = 'Keep on file if the role evolves or a junior position opens up.'

            # Score ring colour
            _ring_pct = int(_score)

            # Build skills pills HTML
            def _pills(items, color, check):
                if not items:
                    return '<span style="color:#9CA3AF;font-size:13px;">None identified</span>'
                return ''.join(
                    f'<span style="display:inline-block;background:{color}22;color:{color};'
                    f'border:1px solid {color}44;border-radius:20px;padding:2px 10px;'
                    f'font-size:12px;font-weight:600;margin:3px 3px 3px 0;">{check} {p}</span>'
                    for p in items
                )

            _skill_pills   = _pills(_matched, '#059669', '✓')
            _gap_pills     = _pills(_missing, '#dc2626', '✗')
            _gpt_badge     = (f'<span style="background:#7c3aed;color:#fff;font-size:10px;'
                              f'font-weight:700;padding:2px 8px;border-radius:12px;margin-left:8px;">'
                              f'GPT: {_gpt_rec}</span>') if _gpt_rec else ''

            all_cards_html += f"""
<div style="border:1.5px solid {_border};border-radius:14px;background:{_bg};
            padding:24px 28px;margin-bottom:20px;box-shadow:0 2px 8px rgba(0,0,0,0.06);">

  <!-- Header row -->
  <div style="display:flex;justify-content:space-between;align-items:flex-start;
              flex-wrap:wrap;gap:12px;margin-bottom:16px;">
    <div>
      <div style="font-size:11px;color:#9CA3AF;font-weight:600;letter-spacing:.06em;
                  text-transform:uppercase;margin-bottom:4px;">#{_rank} of {len(results_sorted)} · {_seniority}</div>
      <div style="font-size:22px;font-weight:700;color:#0F1115;letter-spacing:-0.02em;">
        {_name}{_gpt_badge}
      </div>
    </div>
    <div style="display:flex;align-items:center;gap:12px;">
      <div style="text-align:center;">
        <div style="font-size:36px;font-weight:800;color:{_border};line-height:1;">{_ring_pct}<span style="font-size:16px;">%</span></div>
        <div style="font-size:11px;color:#9CA3AF;margin-top:2px;">match score</div>
      </div>
      <div style="background:{_badge_col};color:#fff;font-size:12px;font-weight:700;
                  padding:6px 16px;border-radius:20px;letter-spacing:.04em;">
        {_label}
      </div>
    </div>
  </div>

  <!-- Summary -->
  <div style="font-size:14px;color:#374151;line-height:1.7;margin-bottom:18px;
              padding:12px 16px;background:rgba(0,0,0,0.03);border-radius:8px;">
    {_summary if _summary else 'No summary available.'}
  </div>

  <!-- Skills grid -->
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:18px;">
    <div>
      <div style="font-size:11px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;
                  color:#059669;margin-bottom:8px;">Verified Skills</div>
      <div>{_skill_pills}</div>
    </div>
    <div>
      <div style="font-size:11px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;
                  color:#dc2626;margin-bottom:8px;">Skill Gaps</div>
      <div>{_gap_pills}</div>
    </div>
  </div>

  <!-- Next step -->
  <div style="border-top:1px solid {_border}33;padding-top:14px;margin-top:4px;">
    <div style="font-size:13px;color:#374151;margin-bottom:6px;">
      <strong style="color:{_border};">Next step:</strong> {_next_step}
    </div>
    <div style="font-size:12px;color:#6B7280;font-style:italic;">
      💼 HR note: {_hr_note}
    </div>
  </div>

</div>"""

        st.markdown(all_cards_html, unsafe_allow_html=True)
    
    # ── Section 4: Email Templates & Reports ──────────────────────────────────
    st.markdown('<div id="sec-reports"></div>', unsafe_allow_html=True)
    st.divider()
    st.subheader("📧 Email Templates & Reports")
    st.caption("BCC-ready shortlist / longlist / rejection emails and CSV exports")
    
    email_tab1, email_tab2, email_tab3 = st.tabs(["🎉 Shortlist Emails", "📋 Longlist Emails", "❌ Rejection Emails"])
    
    with email_tab1:
        st.subheader("Interview Invitation Emails")
        shortlist_template = report_gen.generate_email_template(
            'shortlist', results_sorted,
            st.session_state.longlist_count,
            st.session_state.shortlist_count
        )
        
        st.write(f"**Recipients:** {shortlist_template['recipient_count']} candidates")
        st.text_input("Subject Line:", value=shortlist_template['subject'], disabled=True)
        
        st.text_area("Email Body (with placeholders):", value=shortlist_template['body'], height=200, disabled=True, key="shortlist_email_body")

        bcc_display = shortlist_template['bcc_list'].replace(", ", "\n")
        st.text_area("📧 BCC List (one per line):", value=bcc_display, height=150, disabled=True, key="shortlist_bcc_list")
        
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                label="📥 Download Email Template (TXT)",
                data=shortlist_template['body'],
                file_name=f"ATS_Shortlist_Email_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain",
                use_container_width=True
            )
        with col2:
            st.download_button(
                label="📧 Download BCC List (TXT)",
                data=shortlist_template['bcc_list'],
                file_name=f"ATS_Shortlist_BCC_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain",
                use_container_width=True
            )
        
        st.info("💡 **How to use:** Copy BCC list and paste into your email client's BCC field for batch sending")
    
    with email_tab2:
        st.subheader("Longlist Notification Emails")
        longlist_template = report_gen.generate_email_template(
            'longlist', results_sorted,
            st.session_state.longlist_count,
            st.session_state.shortlist_count
        )
        
        st.write(f"**Recipients:** {longlist_template['recipient_count']} candidates")
        st.text_input("Subject Line:", value=longlist_template['subject'], disabled=True)
        
        st.text_area("Email Body:", value=longlist_template['body'], height=200, disabled=True, key="longlist_email_body")

        bcc_display = longlist_template['bcc_list'].replace(", ", "\n")
        st.text_area("📧 BCC List (one per line):", value=bcc_display, height=150, disabled=True, key="longlist_bcc_list")
        
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                label="📥 Download Email Template (TXT)",
                data=longlist_template['body'],
                file_name=f"ATS_Longlist_Email_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain",
                use_container_width=True
            )
        with col2:
            st.download_button(
                label="📧 Download BCC List (TXT)",
                data=longlist_template['bcc_list'],
                file_name=f"ATS_Longlist_BCC_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain",
                use_container_width=True
            )
        
        st.info("💡 **How to use:** Keep these candidates warm for future opportunities")
    
    with email_tab3:
        st.subheader("Rejection Emails")
        rejected_template = report_gen.generate_email_template(
            'rejected', results_sorted,
            st.session_state.longlist_count,
            st.session_state.shortlist_count
        )
        
        st.write(f"**Recipients:** {rejected_template['recipient_count']} candidates")
        st.text_input("Subject Line:", value=rejected_template['subject'], disabled=True)
        
        st.text_area("Email Body:", value=rejected_template['body'], height=200, disabled=True, key="rejected_email_body")

        bcc_display = rejected_template['bcc_list'].replace(", ", "\n")
        st.text_area("📧 BCC List (one per line):", value=bcc_display, height=150, disabled=True, key="rejected_bcc_list")
        
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                label="📥 Download Email Template (TXT)",
                data=rejected_template['body'],
                file_name=f"ATS_Rejection_Email_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain",
                use_container_width=True
            )
        with col2:
            st.download_button(
                label="📧 Download BCC List (TXT)",
                data=rejected_template['bcc_list'],
                file_name=f"ATS_Rejected_BCC_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain",
                use_container_width=True
            )
        
        st.info("💡 **How to use:** Professional rejection emails maintain your employer brand")
    
    # Download all email templates together
    st.subheader("📧 Download All Email Templates Together")
    email_report = report_gen.generate_email_bcc_report(
        results_sorted,
        st.session_state.longlist_count,
        st.session_state.shortlist_count
    )
    st.download_button(
        label="📥 Download Complete Email Guide (TXT)",
        data=email_report,
        file_name=f"ATS_Email_Guide_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
        mime="text/plain",
        use_container_width=True
    )
    st.caption("All three email templates with BCC lists and instructions")
    
    st.divider()
    
    # CSV & Other Downloads
    st.markdown("### 📊 CSV & Text Reports")
    
    # Download options
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("📊 Comprehensive CSV")
        comprehensive_csv = report_gen.generate_comprehensive_csv(
            results_sorted, 
            job_description,
            st.session_state.longlist_count,
            st.session_state.shortlist_count
        )
        csv_data = comprehensive_csv.to_csv(index=False)
        st.download_button(
            label="📥 Download Full Report (CSV)",
            data=csv_data,
            file_name=f"ATS_Comprehensive_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True
        )
        st.caption("Complete candidate data with all scoring factors")
    
    with col2:
        st.subheader("📋 Longlist/Shortlist")
        selection_report = report_gen.generate_longlist_shortlist_report(
            results_sorted,
            st.session_state.longlist_count,
            st.session_state.shortlist_count
        )
        st.download_button(
            label="📥 Download Selection Report (TXT)",
            data=selection_report,
            file_name=f"ATS_Selection_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain",
            use_container_width=True
        )
        st.caption("Longlist & Shortlist summary document")
    
    with col3:
        st.subheader("✨ Export All Details")
        if len(results_sorted) <= 10:
            all_details = "DETAILED CANDIDATE REPORTS\n"
            all_details += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            all_details += "=" * 80 + "\n\n"
            
            for result in results_sorted:
                detailed_report = report_gen.generate_detailed_candidate_report(result)
                all_details += detailed_report + "\n\n"
            
            st.download_button(
                label="📥 Download All Details (TXT)",
                data=all_details,
                file_name=f"ATS_All_Details_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain",
                use_container_width=True
            )
            st.caption("Complete detailed analysis for all candidates")
        else:
            st.info("📊 Too many candidates for detailed export. Export comprehensive CSV instead.")
    
    # === REJECTED CANDIDATES (Threshold Mode) ===
    if st.session_state.get('use_thresholds', False) and rejected_candidates:
        st.divider()
        st.markdown('<div style="font-weight: 700; font-size: 1.25rem; color: #ef4444; margin: 2rem 0 1rem 0;">❌ Rejected Candidates (Below Minimum Threshold)</div>', unsafe_allow_html=True)
        
        rejected_rows = ""
        for idx, r in enumerate(rejected_candidates, 1):
            rejected_rows += f"""
            <tr class="search-row">
                <td class="search-cell" style="font-weight: 700; color: #ef4444;">#{idx}</td>
                <td class="search-cell" style="color: white; font-weight: 600;">{_candidate_name(r['filename'])}</td>
                <td class="search-cell" style="color: #ef4444; font-weight: 700;">{r['final_score']}%</td>
                <td class="search-cell" style="color: #94a3b8;">{r['cv_seniority'].title()}</td>
            </tr>
            """
        
        st.markdown(f"""
        <table class="search-table">
            <thead>
                <tr>
                    <th style="color: #ef4444;">RANK</th>
                    <th>CANDIDATE</th>
                    <th style="color: #ef4444;">SCORE</th>
                    <th>LEVEL</th>
                </tr>
            </thead>
            <tbody>{rejected_rows}</tbody>
        </table>
        """, unsafe_allow_html=True)
        
        st.info("💡 These candidates did not meet the minimum score threshold and will receive rejection emails.")
        
        # Option to send rejection emails
        if len(rejected_candidates) > 0:
            with st.expander("📧 Prepare Rejection Emails"):
                rejected_emails = ", ".join([c.get('candidate_email', f"candidate_{idx}@example.com") 
                                            for idx, c in enumerate(rejected_candidates)])
                st.text_area("Email addresses for rejected candidates (BCC):",
                            value=rejected_emails,
                            height=100,
                            disabled=True)
                
                st.download_button(
                    label="📥 Download Rejection Email List",
                    data=rejected_emails,
                    file_name=f"Rejected_Candidates_Emails_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain",
                    use_container_width=True
                )
    
    # ── Section 5: Interview Prep & Advanced Analytics ────────────────────────
    st.markdown('<div id="sec-interview"></div>', unsafe_allow_html=True)
    st.divider()
    st.subheader("🎤 Interview Prep & Advanced Analytics")
    st.caption("AI interview questions, diversity metrics, skills analytics & integrations")

    advanced = AdvancedATS()
    
    adv_tab1, adv_tab2, adv_tab3, adv_tab4, adv_tab5, adv_tab6 = st.tabs([
        "❓ Interview Questions", 
        "📊 Diversity Metrics", 
        "📈 Skills Analytics",
        "🎯 Predictive Scores",
        "💬 Feedback & Insights",
        "📤 Integration Export"
    ])
    
    # Interview Questions Tab
    with adv_tab1:
        st.subheader("❓ AI-Generated Interview Questions")
        st.write("Tailored interview questions based on each candidate's profile and skill gaps.")
        
        _iv_opts = [_candidate_name(r['filename']) for r in results_sorted]
        _iv_sel  = st.selectbox("Select candidate for interview prep:", options=_iv_opts, key="interview_selector")
        interview_result = results_sorted[_iv_opts.index(_iv_sel)] if _iv_sel in _iv_opts else None
        
        if interview_result:
            questions = advanced.generate_interview_questions(interview_result, num_questions=6)
            
            st.markdown("### 📋 Recommended Interview Questions:")
            for idx, q in enumerate(questions, 1):
                st.write(f"**{idx}. {q}**")
            
            # Download questions
            questions_text = "\n\n".join([f"{idx}. {q}" for idx, q in enumerate(questions, 1)])
            st.download_button(
                label="📥 Download Interview Questions",
                data=questions_text,
                file_name=f"Interview_Questions_{_iv_sel.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.txt",
                mime="text/plain",
                use_container_width=True
            )
    
    # Diversity Metrics Tab
    with adv_tab2:
        st.subheader("📊 Diversity & Inclusion Metrics")
        
        diversity = advanced.calculate_diversity_metrics(results_sorted)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Candidates", diversity['total_candidates'])
        with col2:
            st.metric("High Scorers (70%+)", f"{diversity['acceptance_rate']['high_scorers']:.1f}%")
        with col3:
            st.metric("Unique Skills Found", diversity['skill_diversity']['unique_skills'])
        
        st.divider()
        
        # Seniority distribution
        st.markdown("#### Experience Level Distribution")
        seniority_df = pd.DataFrame(
            list(diversity['seniority_distribution'].items()),
            columns=['Level', 'Count']
        )
        st.bar_chart(seniority_df.set_index('Level'), use_container_width=True)
        
        # Skills distribution
        st.markdown("#### Top Skills in Candidate Pool")
        skills_df = pd.DataFrame(
            [{'Skill': s, 'Appearance': diversity['skill_diversity']['most_common_skills'].count(s)} 
             for s in diversity['skill_diversity']['most_common_skills']],
            columns=['Skill', 'Appearance']
        )
        if len(skills_df) > 0:
            st.bar_chart(skills_df.set_index('Skill'), use_container_width=True)
        
        # Recommendations
        st.markdown("#### 💡 Diversity Recommendations")
        for rec in diversity['recommendations']:
            st.write(f"• {rec}")
    
    # Skills Analytics Tab
    with adv_tab3:
        st.subheader("📈 Skills Analytics & Trending")
        
        analytics = advanced.generate_skills_analytics(results_sorted)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### ✅ Top Matched Skills")
            matched_df = pd.DataFrame(analytics['top_matched_skills'])
            if len(matched_df) > 0:
                st.dataframe(matched_df[['skill', 'percentage']], use_container_width=True, hide_index=True)
        
        with col2:
            st.markdown("#### ❌ Most Common Missing Skills")
            missing_df = pd.DataFrame(analytics['top_missing_skills'])
            if len(missing_df) > 0:
                st.dataframe(missing_df[['skill', 'percentage']], use_container_width=True, hide_index=True)
        
        st.divider()
        
        # Strategic Talent Assessment (Actionable Insights)
        st.markdown("#### 🎯 Strategic Talent Assessment")
        st.info("Aggregated analysis of the candidate pool versus job requirements.")
        
        # Calculate pool-wide gaps
        all_improvements = []
        for r in results_sorted:
            all_improvements.extend(r.get('improvement_areas', []))
        
        if all_improvements:
            common_improvements = Counter(all_improvements).most_common(5)
            st.markdown("**Common Portfolio Gaps Detected:**")
            for gap, count in common_improvements:
                percentage = (count / len(results_sorted)) * 100
                st.markdown(f"""
                <div class="improvement-item">
                    <span>⚠️</span> 
                    <div style="flex: 1;">
                        <strong>{gap}</strong><br/>
                        <small style="color: var(--text-muted);">Affects {percentage:.0f}% of applicants</small>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.success("✅ No systemic portfolio gaps identified. The candidate pool shows strong alignment with core requirements.")
        
        st.divider()
        
        # Skill proficiency heatmap
        st.markdown("#### 📊 Skill Proficiency Distribution")
        proficiency_data = []
        for skill, profs in list(analytics['skill_proficiency_distribution'].items())[:5]:
            from collections import Counter
            counts = Counter(profs)
            proficiency_data.append({
                'Skill': skill.title(),
                'Expert': counts.get('Expert', 0),
                'Advanced': counts.get('Advanced', 0),
                'Intermediate': counts.get('Intermediate', 0),
                'Junior': counts.get('Junior', 0)
            })
        
        if proficiency_data:
            prof_df = pd.DataFrame(proficiency_data)
            st.bar_chart(prof_df.set_index('Skill'), use_container_width=True)
    
    # Predictive Scores Tab
    with adv_tab4:
        st.subheader("🎯 Predictive Success Analysis")
        st.write("AI-powered predictions of candidate success likelihood based on multiple factors.")
        
        # Show top candidates with predictive scores
        st.markdown("#### Top Candidates with Success Predictions")
        
        predictive_data = []
        for result in results_sorted[:10]:
            prediction = advanced.calculate_predictive_success_score(result)
            predictive_data.append({
                'Candidate': _candidate_name(result['filename']),
                'Actual Score': result['final_score'],
                'Predictive Score': prediction['predictive_score'],
                'Success Likelihood': prediction['success_likelihood'],
                'Missing Skills Risk': prediction['key_factors']['missing_skills_risk']
            })
        
        pred_df = pd.DataFrame(predictive_data)
        st.dataframe(pred_df, use_container_width=True, hide_index=True)
        
        # Detailed prediction for selected candidate
        st.divider()
        st.markdown("#### Detailed Prediction Analysis")
        
        _pd_opts = [_candidate_name(r['filename']) for r in results_sorted]
        _pd_sel  = st.selectbox("Select candidate for detailed prediction:", options=_pd_opts, key="prediction_selector")
        pred_result = results_sorted[_pd_opts.index(_pd_sel)] if _pd_sel in _pd_opts else None
        
        if pred_result:
            prediction = advanced.calculate_predictive_success_score(pred_result)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Predictive Score", prediction['predictive_score'])
            with col2:
                st.metric("Confidence Range", f"{prediction['confidence_interval']['low']}-{prediction['confidence_interval']['high']}%")
            with col3:
                st.info(prediction['success_likelihood'])
            
            st.markdown("**Key Success Factors:**")
            for factor, value in prediction['key_factors'].items():
                st.write(f"• **{factor.replace('_', ' ').title()}:** {value}")
    
    # Personalized Feedback Tab
    with adv_tab5:
        st.subheader("💬 Personalized Candidate Feedback")
        st.write("AI-generated personalized feedback for each candidate.")
        
        _fb_opts = [_candidate_name(r['filename']) for r in results_sorted]
        _fb_sel  = st.selectbox("Select candidate for personalized feedback:", options=_fb_opts, key="feedback_selector")
        feedback_result = results_sorted[_fb_opts.index(_fb_sel)] if _fb_sel in _fb_opts else None
        
        if feedback_result:
            feedback = advanced.generate_personalized_feedback(feedback_result)
            
            # Strengths
            st.markdown("### 💪 Your Strengths")
            for strength in feedback['strengths']:
                st.success(f"✅ {strength}")
            
            # Areas for improvement
            st.markdown("### 🎯 Areas for Growth")
            for improvement in feedback['areas_for_improvement']:
                st.info(f"📌 {improvement}")
            
            # Learning path
            st.markdown("### 📚 Recommended Learning Path")
            for idx, item in enumerate(feedback['learning_path'], 1):
                with st.expander(f"{idx}. {item['skill']} ({item['effort_level']} effort • {item['estimated_time']})"):
                    st.write(f"**Suggestion:** {item['suggestion']}")
            
            # Generate feedback email
            st.divider()
            feedback_email = f"""Dear {_fb_sel},

Thank you for your interest in our position!

YOUR STRENGTHS:
{chr(10).join([f"• {s}" for s in feedback['strengths']])}

AREAS FOR GROWTH:
{chr(10).join([f"• {a}" for a in feedback['areas_for_improvement']])}

RECOMMENDED LEARNING PATH:
{chr(10).join([f"• {item['skill']}: {item['suggestion']}" for item in feedback['learning_path']])}

We encourage you to continue developing your skills and applying for future positions!

Best regards,
The Hiring Team
"""
            
            st.download_button(
                label="📧 Download Feedback Email",
                data=feedback_email,
                file_name=f"Feedback_{_fb_sel.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.txt",
                mime="text/plain",
                use_container_width=True
            )
    
    # Integration Export Tab
    with adv_tab6:
        st.subheader("📤 Integration Export Formats")
        st.write("Export results in formats compatible with other HR systems and platforms.")
        
        export_format = st.radio(
            "Select export format:",
            options=["JSON (API Integration)", "CSV (Excel/Spreadsheet)"],
            horizontal=True
        )
        
        if export_format == "JSON (API Integration)":
            json_export = advanced.export_integration_format(results_sorted, format_type='json')
            st.code(json_export[:500] + "...", language="json")
            
            st.download_button(
                label="📥 Download JSON Export (API Ready)",
                data=json_export,
                file_name=f"ATS_Export_API_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True
            )
        else:
            csv_export = advanced.export_integration_format(results_sorted, format_type='csv')
            st.code(csv_export[:500] + "...", language="csv")
            
            st.download_button(
                label="📥 Download CSV Export",
                data=csv_export,
                file_name=f"ATS_Export_CSV_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        
        st.info("""
        **Integration Options:**
        - 🔗 JSON format compatible with REST APIs
        - 📊 CSV format for spreadsheets and BI tools
        - 🔄 Direct API integration with HRIS systems (Workday, BambooHR, etc.)
        - 📱 Mobile app compatibility
        """)
    
    # Individual candidate detailed reports
    st.divider()
    st.markdown('<div class="subheader-title">📄 Individual Detailed Reports</div>', unsafe_allow_html=True)
    
    # Buttons for all individual reports
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("📥 Download All Reports")
        if st.button("📄 All as PDF Files", key="all_pdf_btn", use_container_width=True):
            with st.spinner("Generating PDFs..."):
                # Create a ZIP file with all PDFs
                import zipfile
                zip_buffer = BytesIO()
                with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                    for idx, result in enumerate(results_sorted, 1):
                        try:
                            pdf_data = report_gen.generate_individual_pdf_report(result)
                            pdf_filename = f"{idx:03d}_{Path(result['filename']).stem}.pdf"
                            zip_file.writestr(pdf_filename, pdf_data)
                        except Exception as e:
                            st.warning(f"Skipped {result['filename']}: {str(e)[:30]}")
                
                zip_buffer.seek(0)
                st.download_button(
                    label="📦 Download ZIP (All PDFs)",
                    data=zip_buffer.getvalue(),
                    file_name=f"ATS_Individual_Reports_PDFs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
                    mime="application/zip",
                    use_container_width=True,
                    key="download_all_pdfs"
                )
    
    with col2:
        st.subheader("📋 Combined Report")
        if st.button("📝 All as Single TXT", key="all_txt_btn", use_container_width=True):
            all_text_reports = "COMPREHENSIVE INDIVIDUAL CANDIDATE REPORTS\n"
            all_text_reports += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            all_text_reports += f"Total Candidates: {len(results_sorted)}\n"
            all_text_reports += "=" * 90 + "\n\n"
            
            for idx, result in enumerate(results_sorted, 1):
                all_text_reports += f"\n[CANDIDATE {idx}/{len(results_sorted)}]\n"
                all_text_reports += report_gen.generate_detailed_candidate_report(result)
                all_text_reports += "\n\n" + "=" * 90 + "\n\n"
            
            st.download_button(
                label="📥 Download Combined TXT",
                data=all_text_reports,
                file_name=f"ATS_All_Individual_Reports_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain",
                use_container_width=True,
                key="download_all_txt"
            )
    
    with col3:
        st.subheader("🎯 Select Specific")
        st.caption("Browse and download individual reports below")
    
    st.divider()
    
    # Individual report selector
    st.markdown("### 🔍 Browse Individual Candidate Reports")
    
    _rpt_opts = [_candidate_name(r['filename']) for r in results_sorted]
    _rpt_sel  = st.selectbox("Select candidate for detailed report:", options=_rpt_opts, key="report_selector")
    selected_result = results_sorted[_rpt_opts.index(_rpt_sel)] if _rpt_sel in _rpt_opts else None
    
    if selected_result:
        detailed_report_text = report_gen.generate_detailed_candidate_report(selected_result)
        
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.text_area(
                "📄 Detailed Report Preview:",
                value=detailed_report_text,
                height=400,
                disabled=True,
                key=f"report_preview_{_rpt_sel}",
            )

        with col2:
            try:
                pdf_individual = report_gen.generate_individual_pdf_report(selected_result)
                st.download_button(
                    label=f"📄 PDF",
                    data=pdf_individual,
                    file_name=f"ATS_Detailed_{Path(selected_result['filename']).stem}_{datetime.now().strftime('%Y%m%d')}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                    key=f"dl_pdf_{_rpt_sel}",
                )
            except Exception as e:
                st.error(f"PDF error: {str(e)[:30]}")

            st.download_button(
                label=f"📝 Text",
                data=detailed_report_text,
                file_name=f"ATS_Detailed_{Path(selected_result['filename']).stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain",
                use_container_width=True,
                key=f"dl_txt_{_rpt_sel}",
            )
        
        with col3:
            st.info("""
            **Report includes:**
            - Overall assessment
            - Detailed scoring
            - Seniority analysis
            - Skills analysis
            - Recommendations
            - Bias alerts
            - Final recommendation
            """)
    
    st.info(f"✅ Analysis completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

else:
    if not job_title or not job_description or not uploaded_files:
        st.info("👈 **Step 1:** Enter job title in the sidebar")
        st.info("👈 **Step 2:** Enter job description in the sidebar")
        st.info("👈 **Step 3:** Upload CVs in the sidebar")
        st.info("👈 **Step 4:** Click 'Analyze Candidates'")
