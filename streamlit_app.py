import streamlit as st
from matcher import EnhancedMatcher
from report_generator import ReportGenerator
from advanced_features import AdvancedATS
from candidate_pool import CandidatePool
from llm_analyzer import LLMAnalyzer, get_analyzer_from_env
import os
import sys
import subprocess
import tempfile
from pathlib import Path
import pandas as pd
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

# ── Global CSS ──────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
@import url('https://fonts.googleapis.com/icon?family=Material+Icons');

:root {
    --primary: #2563eb;
    --primary-light: #eff6ff;
    --sidebar-bg: #f8fafc;
    --border: #e2e8f0;
    --text-main: #020617;
    --text-muted: #334155;
    --bg-app: #ffffff;
    --card-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
}

/* Base Styles */
.stApp {
    background-color: var(--bg-app) !important;
    color: var(--text-main) !important;
}

#MainMenu, footer, header {visibility: hidden;}

/* Professional Typography - targeted to text blocks only to not break icons */
html, body, .stApp, .metric-card, .search-table, .nav-item, .sidebar-header, .premium-header, .sidebar-info {
    font-family: 'Inter', sans-serif;
}

/* Explicitly restore icons if they were caught in the override */
.material-icons, [class*="material-icons"], [data-testid="stExpander"] span {
    font-family: 'Material Icons', sans-serif !important;
}

/* Sidebar Styling */
[data-testid="stSidebar"] {
    background-color: var(--sidebar-bg) !important;
    border-right: 1px solid var(--border) !important;
}

.sidebar-header {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 24px 16px;
    margin-bottom: 24px;
}

.nav-label {
    color: var(--text-muted);
    font-size: 0.75rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    padding: 0 16px;
    margin: 24px 0 8px 0;
}

/* Sidebar Item (Custom) */
.nav-item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 10px 16px;
    border-radius: 8px;
    color: var(--text-main);
    font-size: 0.9rem;
    font-weight: 500;
    cursor: pointer;
    margin: 2px 12px;
    transition: all 0.2s;
}

.nav-item.active {
    background-color: var(--primary-light);
    color: var(--primary);
}

.nav-item:hover:not(.active) {
    background-color: #f1f5f9;
}

/* Metrics Dashboard */
.metric-row {
    display: flex;
    gap: 24px;
    margin: 24px 0;
}

.metric-card {
    background: #ffffff;
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 24px;
    flex: 1;
    min-width: 200px;
}

.metric-val {
    font-size: 2.5rem;
    font-weight: 700;
    color: var(--text-main);
    line-height: 1;
}

.metric-lab {
    font-size: 0.875rem;
    color: var(--text-muted);
    margin: 8px 0;
}

.metric-trend {
    font-size: 0.875rem;
    font-weight: 600;
}

/* Tab Styling - Modern SaaS Underline */
.stTabs [data-baseweb="tab-list"] {
    gap: 32px;
    border-bottom: 1px solid var(--border);
    background: transparent;
}

.stTabs [data-baseweb="tab"] {
    height: 48px;
    background: transparent;
    border: none;
    color: var(--text-muted) !important;
    font-weight: 500 !important;
    padding: 0 4px;
}

.stTabs [aria-selected="true"] {
    color: var(--primary) !important;
    border-bottom: 2px solid var(--primary) !important;
}

/* Modern Card */
.content-card {
    background: #ffffff;
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 32px;
    margin: 24px 0;
}

/* Score Badges Tooltip Style */
.badge {
    padding: 2px 8px;
    border-radius: 6px;
    font-size: 0.75rem;
    font-weight: 600;
}

.badge-blue { background: #dbeafe; color: #1e40af; }
.badge-green { background: #dcfce7; color: #166534; }

/* Table Overhaul */
.search-table {
    width: 100%;
    border-collapse: collapse;
}

.search-table th {
    text-align: left;
    padding: 12px 16px;
    font-size: 0.75rem;
    color: var(--text-muted);
    font-weight: 600;
    text-transform: uppercase;
    border-bottom: 1px solid var(--border);
}

.search-row td {
    padding: 20px 16px;
    border-bottom: 1px solid #f1f5f9;
}

.search-row:hover { background: #f8fafc; }

/* Inputs styling */
.stTextArea textarea, .stTextInput input {
    background: #ffffff !important;
    border: 1px solid var(--border) !important;
    color: var(--text-main) !important;
    border-radius: 8px !important;
}

/* Sidebar Info Box */
.sidebar-info {
    background: var(--primary-light);
    border-radius: 12px;
    padding: 16px;
    margin: 16px;
    color: #1e40af;
    font-size: 0.85rem;
}

.premium-header {
    font-family: 'Inter', sans-serif;
    font-weight: 700;
    font-size: 1.25rem;
    color: var(--text-main);
    margin: 2.5rem 0 1.25rem 0;
    display: flex;
    align-items: center;
    gap: 0.75rem;
}

/* Strategic Analysis Card */
.strategic-card {
    background: #fdfdfd;
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1.5rem;
    margin-bottom: 2rem;
    border-left: 5px solid var(--primary);
}

.strategic-summary {
    font-size: 1.1rem;
    font-weight: 600;
    color: var(--text-main);
    margin-bottom: 1rem;
}

.improvement-item {
    display: flex;
    align-items: center;
    gap: 12px;
    margin: 12px 0;
    font-size: 0.95rem;
    color: #1e293b;
    background: #f8fafc;
    padding: 10px 14px;
    border-radius: 8px;
    border: 1px solid #e2e8f0;
}

.improvement-item span {
    font-size: 1.2rem;
}
</style>
""", unsafe_allow_html=True)


# Initialize session state
if 'results' not in st.session_state:
    st.session_state.results = None

# Bootstrap LLM analyzer from OPENAI_API_KEY in .env on first load
if 'llm_analyzer' not in st.session_state:
    st.session_state.llm_analyzer = get_analyzer_from_env()  # None if key not set

# ── Top bar (Custom SaaS Layout) ─────────────────────────────────────────────
st.markdown(f"""
<div style="display: flex; justify-content: space-between; align-items: center; padding: 12px 24px; border-bottom: 1px solid #e2e8f0; margin-bottom: 32px; background: white; margin-top: -6rem; margin-left: -5rem; margin-right: -5rem;">
    <div style="font-size: 0.875rem; color: #64748b; font-weight: 500;">
        Recruitment / <span style="color: #1e293b; font-weight: 700;">{st.session_state.get('current_job_title', 'New Job')}</span>
    </div>
    <div style="display: flex; gap: 16px; align-items: center;">
        <span class="badge" style="background: #eff6ff; color: #2563eb; font-weight: 600;">v2.0</span>
        <button style="background: white; border: 1px solid #e2e8f0; padding: 6px 16px; border-radius: 6px; font-size: 0.875rem; font-weight: 600; cursor: pointer;">Export</button>
        <button style="background: white; border: 1px solid #e2e8f0; padding: 6px 16px; border-radius: 6px; font-size: 0.875rem; font-weight: 600; cursor: pointer;">+ New Job</button>
    </div>
</div>
""", unsafe_allow_html=True)

from embedding import SemanticMatcher
matcher = EnhancedMatcher(SemanticMatcher())

# ── Sidebar Navigation ───────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class="sidebar-header">
        <div style="width: 32px; height: 32px; background: #2563eb; border-radius: 8px; display: flex; align-items: center; justify-content: center; color: white; font-weight: 800;">🧭</div>
        <div>
            <div style="font-weight: 700; color: #1e293b; font-size: 1.1rem; line-height: 1;">HR Compass</div>
            <div style="font-size: 0.7rem; color: #64748b; font-weight: 500;">AI Talent Navigation</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="nav-label">WORKSPACE</div>', unsafe_allow_html=True)
    st.markdown('<div class="nav-item active">🟦 Job Setup</div>', unsafe_allow_html=True)
    st.markdown('<div class="nav-item">📁 Candidate Pool</div>', unsafe_allow_html=True)
    st.markdown('<div class="nav-item">📊 Analytics</div>', unsafe_allow_html=True)
    st.markdown('<div class="nav-item">📄 Reports</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="nav-label">SETTINGS</div>', unsafe_allow_html=True)
    st.markdown('<div class="nav-item">⚙️ Preferences</div>', unsafe_allow_html=True)
    st.markdown('<div class="nav-item">👥 Team</div>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="sidebar-info">
        <div style="font-weight: 700; margin-bottom: 4px;">Quick start</div>
        Enter job details, upload CVs, then click Analyze to begin AI screening.
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div style="display: flex; gap: 8px; margin: 16px;">
        <div style="background: #f1f5f9; padding: 12px; border-radius: 8px; flex: 1; text-align: center;">
            <div style="font-size: 1.1rem; font-weight: 700; color: #1e293b;">0</div>
            <div style="font-size: 0.65rem; color: #64748b; font-weight: 700; text-transform: uppercase;">CVs loaded</div>
        </div>
        <div style="background: #f1f5f9; padding: 12px; border-radius: 8px; flex: 1; text-align: center;">
            <div style="font-size: 1.1rem; font-weight: 700; color: #1e293b;">—</div>
            <div style="font-size: 0.65rem; color: #64748b; font-weight: 700; text-transform: uppercase;">Last run</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# Main app tabs
tab_job, tab_pool, tab_analytics, tab_settings = st.tabs(["Job Setup", "Candidate Pool", "Analytics", "Settings"])

with tab_job:
        st.session_state.selected_sidebar_tab = "Job Setup"
        predefined_roles = [
            "Senior Python Developer",
            "Data Scientist",
            "Product Manager",
            "DevOps Engineer",
            "HR Analyst",
            "AI/ML Engineer",
            "Backend Engineer",
            "Frontend Engineer",
            "QA Engineer",
            "Business Analyst"
        ]

        saved_roles = load_saved_job_titles()
        all_roles = sorted(set(predefined_roles + saved_roles), key=str.lower)

        role_descriptions = {
            "Senior Python Developer": "Build and maintain scalable backend services, strong experience in Python, REST APIs, and cloud deployment.",
            "Data Scientist": "Design models, perform data analysis, and build data-driven products using Python, SQL, and ML frameworks.",
            "Product Manager": "Lead product lifecycle from ideation to launch with cross-functional alignment and metrics-driven roadmap.",
            "DevOps Engineer": "Automate deployment pipelines, manage infrastructure as code, and ensure system reliability.",
            "HR Analyst": "Analyze hiring metrics, build dashboards, and support workforce planning with data insights.",
            "AI/ML Engineer": "Develop ML models, optimize algorithms, and deploy scalable AI solutions in production.",
            "Backend Engineer": "Design robust server-side systems, database schemas, and API endpoints for high-performance apps.",
            "Frontend Engineer": "Implement responsive UI components and optimize user experience with modern web frameworks.",
            "QA Engineer": "Build test automation, run end-to-end tests, and ensure quality across release cycles.",
            "Business Analyst": "Gather requirements, define workflow processes, and translate business needs into technical specs."
        }

        selected_role = st.selectbox(
            "🏷️ Select Job Title (or choose Other)",
            options=all_roles + ["Other"],
            index=0,
            key="job_title_dropdown"
        )

        if selected_role == "Other":
            job_title = st.text_input(
                "✏️ Enter custom job title:",
                placeholder="e.g., Machine Learning Operations Lead",
                key="job_title_custom"
            )
            if job_title and job_title.strip():
                job_title = job_title.strip()
                if job_title not in all_roles:
                    all_roles.append(job_title)
                    save_job_titles(all_roles)
        else:
            job_title = selected_role

        # Initialize or update job description in session state
        if 'job_desc' not in st.session_state:
            st.session_state.job_desc = role_descriptions.get(selected_role, '') if selected_role != 'Other' else ''
            st.session_state.last_selected_role = selected_role

        if selected_role != 'Other' and st.session_state.get('last_selected_role') != selected_role:
            st.session_state.job_desc = role_descriptions.get(selected_role, '')
            st.session_state.last_selected_role = selected_role

        if selected_role == 'Other' and st.session_state.get('last_selected_role') != 'Other':
            st.session_state.job_desc = ''
            st.session_state.last_selected_role = 'Other'

        job_description = st.text_area(
            "📝 Job Description:",
            height=150,
            value=st.session_state.job_desc,
            key="job_desc"
        )
        
        uploaded_files = st.file_uploader(
            "📤 Upload CVs (PDF)",
            type="pdf",
            accept_multiple_files=True
        )
        
        process_button = st.button("🚀 Analyze Candidates", type="primary", use_container_width=True)
    
with tab_analytics:
    st.markdown("""
        ### 🎯 About This System
        
        **Features:**
        - ✅ Multi-CV ranking
        - ✅ Explainable scoring
        - ✅ Skill gap analysis
        - ✅ Bias detection
        - ✅ Proficiency estimation
        - ✅ Learning recommendations
        - ✅ Longlist/Shortlist
        - ✅ PDF Reports
        - ✅ Email Templates (BCC Ready)
        - ✅ Batch Processing
        
        **Scoring Formula:**
        ```
        35% Semantic Match
        25% Skills Match
        15% Experience
        15% Keyword Density
        5% Culture Fit
        5% Seniority
        ```
        
        ### 📦 Batch Import Capabilities
        
        **File Limits:**
        - 📄 **Per File:** Up to 50 MB per PDF
        - 📤 **Per Upload:** Streamlit default 200 MB total
        - 🔢 **Candidate Limit:** Up to 500+ CVs recommended
        
        **Processing Performance:**
        - ⚡ ~1-2 seconds per candidate
        - 📊 50 candidates: 1-2 minutes
        - 📊 100 candidates: 2-4 minutes
        - 📊 500 candidates: 10-15 minutes
        
        **How to Import Large Batches:**
        1. 📋 Select all CVs using Ctrl+A in file picker
        2. 🚀 Click "Analyze Candidates"
        3. ⏳ Monitor progress in the interface
        4. 📊 Export results once complete
        
        **Limitations:**
        - For 1000+ candidates, consider splitting imports
        - Streamlit may timeout on very large batches (>1000)
        - Maximum session memory: ~2GB
        
        **Tips for Large Batches:**
        - ✓ Ensure PDFs are text-based (not scanned images)
        - ✓ Use consistent naming for easier tracking
        - ✓ Split batches by role/department if needed
        - ✓ Use CSV export for further processing
        """)

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
        
    else:  # Threshold-based
        st.info("🎯 Categorize candidates by minimum score (%) and limit counts")
        
        shortlist_threshold = st.slider(
            "🎯 Shortlist Threshold (%)",
            min_value=0,
            max_value=100,
            value=70,
            step=5,
            help="Minimum score to be shortlisted"
        )
        
        longlist_threshold = st.slider(
            "📋 Longlist Threshold (%)",
            min_value=0,
            max_value=100,
            value=50,
            step=5,
            help="Minimum score to be longlisted (must be less than shortlist)"
        )
        
        if shortlist_threshold <= longlist_threshold:
            st.error("⚠️ Shortlist threshold must be higher than longlist threshold!")
        
        # Add count limits for threshold mode
        max_candidates = len(st.session_state.results) if st.session_state.results else 500
        
        shortlist_count = st.slider(
            "🎯 Max Shortlist Size",
            min_value=1,
            max_value=max(max_candidates, 50),
            value=min(20, max_candidates),
            help="Maximum number of candidates to shortlist (from those meeting threshold)"
        )
        
        longlist_count = st.slider(
            "📋 Max Longlist Size",
            min_value=1,
            max_value=max(max_candidates, 200),
            value=min(200, max_candidates),
            help="Maximum number of candidates to longlist (from those meeting threshold)"
        )
        
        st.session_state.use_thresholds = True
        st.session_state.shortlist_threshold = shortlist_threshold
        st.session_state.longlist_threshold = longlist_threshold
        st.session_state.longlist_count = longlist_count
        st.session_state.shortlist_count = shortlist_count
    
    st.divider()
    st.caption(f"📊 Longlist: Top {longlist_count} candidates")
    st.caption(f"🎯 Shortlist: Top {shortlist_count} candidates")

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
                                        'Candidate': c['filename'],
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
                        'Candidate': c['filename'],
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
    
    results = []
    
    for idx, uploaded_file in enumerate(uploaded_files):
        status_text.text(f"Processing {idx + 1}/{len(uploaded_files)}: {uploaded_file.name}")
        progress_bar.progress((idx + 1) / len(uploaded_files))
        
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
            tmp_file.write(uploaded_file.getbuffer())
            temp_path = tmp_file.name
        
        try:
            cv_name = Path(uploaded_file.name).stem
            result = matcher.match_cv_to_job(temp_path, job_description, cv_name)
            result['filename'] = uploaded_file.name

            # ── Phase 2: Claude LLM deep analysis (if API key configured) ──
            llm = st.session_state.get('llm_analyzer')
            if llm is not None:
                status_text.text(
                    f"Processing {idx + 1}/{len(uploaded_files)}: {uploaded_file.name} — running Claude AI analysis..."
                )
                llm_result = llm.analyze_candidate(
                    result.get('cv_text', ''),
                    job_description,
                    result.get('pre_analysis', {}),
                )
                result['llm_analysis'] = llm_result  # None if API call failed

            results.append(result)
        except Exception as e:
            st.error(f"Error processing {uploaded_file.name}: {str(e)}")
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
    
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
    
    # Auto-assign candidates to pools based on thresholds
    shortlist_threshold = st.session_state.get('shortlist_threshold', 70)
    longlist_threshold = st.session_state.get('longlist_threshold', 50)
    
    job_id, assigned = pool.auto_assign_candidates(
        results, job_title, job_description, 
        shortlist_threshold, longlist_threshold
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

    # ── Ranking Table ──────────────────────────────────────────────────────────
    rows_html = ""
    for idx, r in enumerate(results_sorted, 1):
        score = r['final_score']
        badge_class = "badge-excellent" if score >= 85 else "badge-good" if score >= 70 else "badge-mid" if score >= 40 else "badge-low"
        
        # Clean up filename for display
        display_name = r['filename'].replace('.pdf', '').replace('.txt', '').replace('.docx', '')
        
        rows_html += f"""<tr class="search-row">
            <td class="search-cell" style="font-weight: 700; color: #020617;">#{idx}</td>
            <td class="search-cell">
                <div style="font-weight: 700; color: #020617; font-size: 0.95rem;">{display_name}</div>
                <div style="font-size: 0.75rem; color: #475569; margin-top: 2px;">{r['cv_seniority'].title()} Level</div>
            </td>
            <td class="search-cell">
                <span class="score-badge {badge_class}">{score}% Match</span>
            </td>
            <td class="search-cell" style="color: #64748b;">{len(r['matched_skills'])} matched</td>
            <td class="search-cell" style="text-align: right;">
                <span style="color: #0891b2; font-size: 0.8rem; font-weight: 600;">AI EVALUATED</span>
            </td>
        </tr>"""

    st.markdown(f"""
    <div style="overflow-x: auto;">
        <table class="search-table">
            <thead>
                <tr>
                    <th>RANK</th>
                    <th>CANDIDATE</th>
                    <th>AI SCORE</th>
                    <th>SKILLS</th>
                    <th style="text-align: right;">STATUS</th>
                </tr>
            </thead>
            <tbody>
                {rows_html}
            </tbody>
        </table>
    </div>
    """, unsafe_allow_html=True)
    
    st.divider()
    
    # === DETAILED ANALYSIS ===
    st.markdown('<div style="font-weight: 700; font-size: 1.25rem; color: var(--text-main); margin: 2rem 0 1rem 0;">📊 Detailed Candidate Analysis</div>', unsafe_allow_html=True)
    
    for idx, result in enumerate(results_sorted, 1):
        with st.expander(f"#{idx} - {result['filename']} ({result.get('confidence_level', 'Evaluated')}) 👤", expanded=(idx == 1)):
            
            # 1. Executive Summary — LLM version takes priority, keyword fallback otherwise
            llm = result.get('llm_analysis')
            if llm and llm.get('executive_summary'):
                # ── Claude-generated executive summary ──
                rec = llm.get('interview_recommendation', 'Consider')
                rec_color = '#166534' if rec == 'Shortlist' else '#92400e' if rec == 'Consider' else '#991b1b'
                rec_bg = '#f0fdf4' if rec == 'Shortlist' else '#fefce8' if rec == 'Consider' else '#fef2f2'
                strengths_html = "".join(
                    f'<li style="margin:4px 0;">{s}</li>'
                    for s in llm.get('key_strengths', [])
                )
                st.markdown(f"""
                <div style="background:#f8faff;border:1px solid #c7d7fe;border-left:5px solid #4f46e5;
                            padding:20px;border-radius:12px;margin-bottom:20px;">
                    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
                        <h3 style="margin:0;color:#1e1b4b;font-size:1.15rem;">
                            🤖 GPT — Executive Summary
                        </h3>
                        <span style="background:{rec_bg};color:{rec_color};font-weight:700;
                                     padding:4px 12px;border-radius:20px;font-size:0.8rem;">
                            {rec}
                        </span>
                    </div>
                    <p style="color:#3730a3;font-size:1rem;line-height:1.65;margin:0 0 12px 0;">
                        {llm['executive_summary']}
                    </p>
                    <div style="font-size:0.85rem;font-weight:700;color:#4338ca;margin-bottom:4px;">
                        Key Strengths
                    </div>
                    <ul style="margin:0;padding-left:18px;color:#374151;font-size:0.9rem;">
                        {strengths_html}
                    </ul>
                </div>
                """, unsafe_allow_html=True)
            elif result.get('strategic_summary'):
                # ── Keyword-based fallback summary ──
                st.markdown(f"""
                <div style="background: #fdfcfe; border: 1px solid #e1e7ff; border-left: 5px solid #6366f1; padding: 20px; border-radius: 12px; margin-bottom: 25px;">
                    <h3 style="margin-top: 0; color: #1e1b4b; display: flex; align-items: center; gap: 8px; font-size: 1.25rem;">
                        <span>📊</span> Match Rationale & Executive Summary
                    </h3>
                    <div style="color: #3730a3; font-size: 1.05rem; line-height: 1.6;">
                        {result['strategic_summary']}
                    </div>
                </div>
                """, unsafe_allow_html=True)

            # 2. Performance Metrics
            final_score = result['final_score']
            badge_class = "badge-excellent" if final_score >= 85 else "badge-good" if final_score >= 70 else "badge-mid" if final_score >= 40 else "badge-low"
            
            col_a, col_b = st.columns([1, 2])
            with col_a:
                st.markdown(f"""
                <div style="text-align: center; padding: 1.5rem; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px;">
                    <div style="font-size: 2rem; font-weight: 800; color: #0f172a;">{final_score}%</div>
                    <div style="font-size: 0.8rem; text-transform: uppercase; color: #64748b; font-weight: 700; margin-top: 4px;">Match Score</div>
                    <div class="score-badge {badge_class}" style="margin-top: 10px; display: inline-block;">{result.get('confidence_level', 'Evaluated')}</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col_b:
                st.markdown("**📈 Scoring Breakdown**")
                scores = result.get('score_breakdown', {})
                breakdown_html = '<div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px;">'
                for lab, val in [("Semantic", scores.get('semantic_similarity', 0)), 
                                ("Skills", scores.get('skills_match', 0)), 
                                ("Exp.", scores.get('experience_relevance', 0)),
                                ("Keywords", scores.get('keyword_density', 0)),
                                ("Culture", scores.get('culture_fit', 0)),
                                ("Seniority", scores.get('seniority_alignment', 0))]:
                    breakdown_html += f'<div style="background: #fff; padding: 6px; border: 1px solid #f1f5f9; border-radius: 6px; text-align: center;"><div style="font-size: 0.65rem; color: #64748b; font-weight: 700;">{lab}</div><div style="font-size: 0.9rem; font-weight: 700; color: #334155;">{val:.0f}%</div></div>'
                breakdown_html += "</div>"
                st.markdown(breakdown_html, unsafe_allow_html=True)

            st.divider()

            # 3. Gap Analysis & Roadmap
            if result.get('improvement_areas'):
                st.markdown("### 🛠️ Strategic Gap Analysis")
                for area in result['improvement_areas']:
                    if len(area) > 10: # Ensure it's a real sentence
                        st.markdown(f"""
                        <div style="background: #fff; border: 1px solid #e2e8f0; border-left: 5px solid #f43f5e; padding: 12px 16px; border-radius: 8px; margin-bottom: 10px; box-shadow: 0 1px 2px rgba(0,0,0,0.05);">
                            {area}
                        </div>
                        """, unsafe_allow_html=True)

            st.divider()

            # 4. Verified Skills (Clean Native Layout)
            st.markdown("### 🎯 Verified Technical Expertise")
            valid_skills = [s.strip() for s in result.get('matched_skills', []) if len(s.strip()) > 1]
            
            if valid_skills:
                # Use columns for skills to ensure perfect rendering without HTML leaks
                skill_cols = st.columns(3)
                for i, skill in enumerate(valid_skills):
                    proficiency = result.get('skill_proficiency', {}).get(skill, 'Verified')
                    with skill_cols[i % 3]:
                        st.markdown(f"**✓ {skill.title()}** ({proficiency})")
            else:
                st.info("🔍 No specific technical skill matches identified.")

            # 5. Missing Skills (Bulleted Roadmap with Explanations)
            st.markdown("### 📈 Priority Development Areas")
            
            # Filter and sanitize
            blacklist_categories = ['languages', 'skills', 'tools', 'technologies', 'experience', 'development', 'management']
            valid_recommendations = [
                rec for rec in result.get('recommendations', []) 
                if len(rec.get('skill', '').strip()) > 1 
                and rec.get('skill', '').lower() not in blacklist_categories
            ]
            
            if valid_recommendations:
                for rec in valid_recommendations[:6]: # Show top 6 priorities
                    skill_name = rec.get('skill', 'Technology').upper()
                    impact = rec.get('impact', 'Technical Debt')
                    suggestion = rec.get('suggestion', 'Review documentation')
                    
                    st.markdown(f"""
                    *   **{skill_name}**: {suggestion}
                        *   *Impact*: {impact} | *Effort*: {rec.get('effort', 2)}/4
                    """)
            else:
                st.success("✨ Critical JD skills appear to be well-aligned.")

            # 6. Detailed Learning Roadmap
            if result.get('recommendations'):
                with st.expander("📚 View Detailed Professional Development Roadmap"):
                    for rec in result['recommendations']:
                        priority_icon = "🚀" if rec.get('effort', 2) > 3 else "📚"
                        st.markdown(f"""
                        <div style="background: #ffffff; border: 1px solid #e2e8f0; border-left: 5px solid {'#e11d48' if rec.get('effort', 2) > 3 else '#f59e0b'}; padding: 16px; border-radius: 12px; margin-bottom: 12px;">
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                                <strong style="font-size: 1rem; color: #0f172a;">{priority_icon} {rec.get('skill', 'Technology').title()}</strong>
                                <span style="background: #f1f5f9; color: #475569; padding: 2px 10px; border-radius: 6px; font-size: 0.75rem; font-weight: 700;">{rec.get('time', '2 Weeks')} Effort</span>
                            </div>
                            <div style="font-size: 0.95rem; color: #334155; line-height: 1.5;">{rec.get('suggestion')}</div>
                            <div style="margin-top: 8px; font-size: 0.8rem; color: #64748b; font-style: italic;">Impact: {rec.get('impact', 'Career Growth')}</div>
                        </div>
                        """, unsafe_allow_html=True)

            # 7. Career Advice (keyword-based, always shown)
            if result.get('career_advice'):
                st.info(f"💡 **Strategic Career Guidance:** {result['career_advice']}")

            # 8. Claude AI — Deep Skill Gap Analysis & Interview Prep
            if llm:
                st.divider()
                st.markdown("### 🤖 GPT — Deep Analysis")

                # Critical gaps with learning paths
                gaps = llm.get('critical_gaps', [])
                if gaps:
                    st.markdown("**🔍 Critical Gaps (AI-identified)**")
                    for gap in gaps:
                        priority = gap.get('priority', 'medium')
                        border_color = '#dc2626' if priority == 'high' else '#d97706' if priority == 'medium' else '#16a34a'
                        st.markdown(f"""
                        <div style="background:#fff;border:1px solid #e2e8f0;border-left:5px solid {border_color};
                                    padding:14px 16px;border-radius:8px;margin-bottom:10px;">
                            <div style="display:flex;justify-content:space-between;align-items:center;">
                                <strong style="color:#0f172a;font-size:0.95rem;">{gap.get('skill','').title()}</strong>
                                <span style="font-size:0.75rem;color:#64748b;font-weight:600;">
                                    {gap.get('estimated_time','—')} · {priority.upper()} priority
                                </span>
                            </div>
                            <div style="color:#475569;font-size:0.88rem;margin-top:6px;">
                                <em>{gap.get('importance','')}</em>
                            </div>
                            <div style="color:#1e293b;font-size:0.9rem;margin-top:6px;">
                                📚 {gap.get('learning_path','')}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.success("✅ No critical skill gaps identified by Claude AI.")

                # Interview focus areas
                focus_areas = llm.get('interview_focus_areas', [])
                if focus_areas:
                    st.markdown("**🎤 Interview Focus Areas (AI-recommended)**")
                    for area in focus_areas:
                        st.markdown(f"- {area}")

                # Career fit narrative
                narrative = llm.get('career_fit_narrative', '')
                if narrative:
                    st.markdown(f"**🧭 Long-term Career Fit:** {narrative}")

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
    
    # === COMPARATIVE ANALYSIS ===
    if len(results_sorted) > 1:
        st.divider()
        st.markdown('<div class="premium-header">📈 Comparative Analysis</div>', unsafe_allow_html=True)
        
        comparison_df = pd.DataFrame({
            'Candidate': [r['filename'] for r in results_sorted],
            'Final Score': [r['final_score'] for r in results_sorted],
            'Semantic': [r['score_breakdown']['semantic_similarity'] for r in results_sorted],
            'Skills': [r['score_breakdown']['skills_match'] for r in results_sorted],
            'Experience': [r['score_breakdown']['experience_relevance'] for r in results_sorted],
            'Keywords': [r['score_breakdown']['keyword_density'] for r in results_sorted],
        })
        
        st.bar_chart(comparison_df.set_index('Candidate'), use_container_width=True)
    
    # === LONGLIST & SHORTLIST ===
    st.divider()
    st.markdown('<div class="premium-header">📋 Longlist & 🎯 Shortlist</div>', unsafe_allow_html=True)
    
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
                'Candidate': r['filename'],
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
                'Candidate': r['filename'],
                'Fit': r.get('confidence_level', 'Strong')
            } for i, r in enumerate(shortlist)])
            st.dataframe(short_df, hide_index=True, use_container_width=True)
            st.info(f"ℹ️ {len(shortlist)} selected for interview")
        else:
            st.warning("No shortlisted candidates")

    
    # === RECOMMENDATIONS ===
    st.divider()
    st.markdown('<div class="premium-header">🎯 HR Recommendations</div>', unsafe_allow_html=True)
    
    if not results_sorted:
        st.warning("⚠️ No candidates meet the minimum threshold requirements. Please adjust your settings and try again.")
    else:
        top_candidate = results_sorted[0]
        
        if top_candidate['final_score'] >= 85:
            st.success(f"""
            ### ✅ EXCELLENT MATCH
            **{top_candidate['filename']}** - {top_candidate['final_score']}%
            
            {top_candidate.get('strategic_summary', 'This candidate is highly qualified and aligns exceptionally well with requirements.')}
            
            **Key strengths:**
            {"\n".join([f'- {s.title()}' for s in top_candidate.get('matched_skills', [])[:3]])}
            
            **Recommendation:** Immediate interview - top priority candidate.
            """)
        elif top_candidate['final_score'] >= 70:
            st.info(f"""
            ### ⭐ STRONG MATCH
            **{top_candidate['filename']}** - {top_candidate['final_score']}%
            
            {top_candidate.get('strategic_summary', 'This candidate shows good alignment with role requirements.')}
            
            **Focus areas:**
            {"\n".join([f'- {area}' for area in top_candidate.get('improvement_areas', [])[:2]])}
            
            **Recommendation:** Schedule interview. Discuss learning commitment for skill gaps.
            """)
        elif top_candidate['final_score'] >= 60:
            st.warning(f"""
            ### 🟡 MODERATE MATCH
            **{top_candidate['filename']}** - {top_candidate['final_score']}%
            
            {top_candidate.get('strategic_summary', 'This candidate has potential but significant gaps exist.')}
            
            **Gap Analysis:**
            {"\n".join([f'- {area}' for area in top_candidate.get('improvement_areas', [])[:3]])}
            
            **Recommendation:** Consider for growth-focused role or with training support.
            """)
        else:
            st.error(f"""
            ### 🔴 WEAK MATCH
            **{top_candidate['filename']}** - {top_candidate['final_score']}%
            
            {top_candidate.get('strategic_summary', 'This candidate does not meet core requirements.')}
            
            **Critical Gaps:**
            {"\n".join([f'- {area}' for area in top_candidate.get('improvement_areas', [])]) or "- No critical gaps detected."}
            
            **Recommendation:** Consider for different roles or revisit later after skill development.
            """)
            
            # Export summary (only if there are candidates)
            st.divider()
            st.markdown('<div class="premium-header">📥 Export & Reports</div>', unsafe_allow_html=True)
            
            # PDF Reports Section
            st.markdown("### 📄 PDF Reports")
            pdf_col1, pdf_col2 = st.columns(2)
            
            with pdf_col1:
                st.subheader("🎯 Comprehensive PDF Report")
                try:
                    pdf_data = report_gen.generate_pdf_report(
                        results_sorted,
                        job_description,
                        st.session_state.longlist_count,
                        st.session_state.shortlist_count
                    )
                    st.download_button(
                        label="📥 Download PDF Report",
                        data=pdf_data,
                        file_name=f"ATS_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
                    st.caption("Professional PDF with all candidate rankings and scores")
                except Exception as e:
                    st.error(f"Error generating PDF: {str(e)}")
            
            with pdf_col2:
                st.subheader("📊 Candidates Summary")
                st.metric("Total Candidates", len(results_sorted))
        st.metric("Shortlist", min(st.session_state.shortlist_count, len(results_sorted)))
        st.metric("Longlist", min(st.session_state.longlist_count, len(results_sorted)))
    
    st.divider()
    
    # Email Templates Section
    st.markdown("### 📧 Email Templates (BCC Ready)")
    
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
                <td class="search-cell" style="color: white; font-weight: 600;">{r['filename']}</td>
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
    
            # === ADVANCED ENTERPRISE FEATURES ===
            st.divider()
            st.markdown('<div class="premium-header">🚀 Advanced Analytics & Features</div>', unsafe_allow_html=True)
    
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
        
        interview_candidate = st.selectbox(
            "Select candidate for interview prep:",
            options=[r['filename'] for r in results_sorted],
            key="interview_selector"
        )
        
        interview_result = next((r for r in results_sorted if r['filename'] == interview_candidate), None)
        
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
                file_name=f"Interview_Questions_{Path(interview_candidate).stem}_{datetime.now().strftime('%Y%m%d')}.txt",
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
                'Candidate': result['filename'][:30],
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
        
        pred_candidate = st.selectbox(
            "Select candidate for detailed prediction:",
            options=[r['filename'] for r in results_sorted],
            key="prediction_selector"
        )
        
        pred_result = next((r for r in results_sorted if r['filename'] == pred_candidate), None)
        
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
        
        feedback_candidate = st.selectbox(
            "Select candidate for personalized feedback:",
            options=[r['filename'] for r in results_sorted],
            key="feedback_selector"
        )
        
        feedback_result = next((r for r in results_sorted if r['filename'] == feedback_candidate), None)
        
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
            feedback_email = f"""Dear {Path(feedback_candidate).stem},

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
                file_name=f"Feedback_{Path(feedback_candidate).stem}_{datetime.now().strftime('%Y%m%d')}.txt",
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
    
    selected_candidate = st.selectbox(
        "Select candidate for detailed report:",
        options=[r['filename'] for r in results_sorted],
        key="report_selector"
    )
    
    selected_result = next((r for r in results_sorted if r['filename'] == selected_candidate), None)
    
    if selected_result:
        detailed_report_text = report_gen.generate_detailed_candidate_report(selected_result)
        
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.text_area(
                "📄 Detailed Report Preview:",
                value=detailed_report_text,
                height=400,
                disabled=True,
                key="report_preview_area"
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
                    key="individual_pdf_download"
                )
            except Exception as e:
                st.error(f"PDF error: {str(e)[:30]}")
            
            st.download_button(
                label=f"📝 Text",
                data=detailed_report_text,
                file_name=f"ATS_Detailed_{Path(selected_result['filename']).stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain",
                use_container_width=True,
                key="individual_txt_download"
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
