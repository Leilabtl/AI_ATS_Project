import streamlit as st
from matcher import EnhancedMatcher
from report_generator import ReportGenerator
from advanced_features import AdvancedATS
from candidate_pool import CandidatePool
import os
import tempfile
from pathlib import Path
import pandas as pd
from datetime import datetime
from io import BytesIO
import zipfile

# Page config
st.set_page_config(
    page_title="🤖 ELITE ATS - AI Resume Screening",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Modern CSS Styling
st.markdown("""
<style>
    * {font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;}
    
    .main {background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
    
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 12px;
        text-align: center;
        font-weight: bold;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }
    
    .score-excellent {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        color: white;
        padding: 30px;
        border-radius: 15px;
        text-align: center;
        font-size: 2rem;
        font-weight: bold;
        box-shadow: 0 8px 20px rgba(0,0,0,0.2);
    }
    
    .score-good {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
        padding: 30px;
        border-radius: 15px;
        text-align: center;
        font-size: 2rem;
        font-weight: bold;
        box-shadow: 0 8px 20px rgba(0,0,0,0.2);
    }
    
    .score-moderate {
        background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
        color: white;
        padding: 30px;
        border-radius: 15px;
        text-align: center;
        font-size: 2rem;
        font-weight: bold;
        box-shadow: 0 8px 20px rgba(0,0,0,0.2);
    }
    
    .score-low {
        background: linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 100%);
        color: white;
        padding: 30px;
        border-radius: 15px;
        text-align: center;
        font-size: 2rem;
        font-weight: bold;
        box-shadow: 0 8px 20px rgba(0,0,0,0.2);
    }
    
    .skill-match {
        background: #e8f5e9;
        border-left: 4px solid #4caf50;
        padding: 12px;
        margin: 8px 0;
        border-radius: 6px;
    }
    
    .skill-missing {
        background: #ffebee;
        border-left: 4px solid #f44336;
        padding: 12px;
        margin: 8px 0;
        border-radius: 6px;
    }
    
    .recommendation-box {
        background: #e3f2fd;
        border-left: 4px solid #2196f3;
        padding: 14px;
        margin: 10px 0;
        border-radius: 6px;
    }
    
    .bias-alert {
        background: #fff3e0;
        border-left: 4px solid #ff9800;
        padding: 14px;
        margin: 10px 0;
        border-radius: 6px;
    }
    
    .header-title {
        font-size: 2.8rem;
        color: #667eea;
        margin: 20px 0;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }
    
    .subheader-title {
        font-size: 1.5rem;
        color: #764ba2;
        margin: 15px 0;
    }
    
    .ranking-table {
        border-collapse: collapse;
        width: 100%;
    }
    
    .ranking-table th {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 12px;
        text-align: left;
        font-weight: bold;
    }
    
    .ranking-table tr:nth-child(even) {
        background: #f5f5f5;
    }
    
    .ranking-table td {
        padding: 12px;
        border-bottom: 1px solid #ddd;
    }
    
    .proficiency-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: bold;
        margin: 2px;
    }
    
    .expert {background: #4caf50; color: white;}
    .advanced {background: #2196f3; color: white;}
    .intermediate {background: #ff9800; color: white;}
    .junior {background: #9e9e9e; color: white;}
    
    .confidence-label {
        font-size: 1.1rem;
        font-weight: bold;
        padding: 8px 16px;
        border-radius: 6px;
    }
    
    .confidence-very-high {background: #4caf50; color: white;}
    .confidence-high {background: #8bc34a; color: white;}
    .confidence-moderate {background: #ffc107; color: white;}
    .confidence-low {background: #ff9800; color: white;}
    .confidence-very-low {background: #f44336; color: white;}
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'results' not in st.session_state:
    st.session_state.results = None

# Header
st.markdown('<div class="header-title">🤖 ELITE ATS System</div>', unsafe_allow_html=True)
st.markdown("**Advanced AI-Powered Resume Screening with Explainable Scoring**", unsafe_allow_html=True)
st.divider()

matcher = EnhancedMatcher()

# Sidebar configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    st.info("Upload job description and CVs to analyze candidate fit")
    
    tab1, tab2, tab3 = st.tabs(["📋 Input", "ℹ️ Info", "⚙️ Settings"])
    
    with tab1:
        job_description = st.text_area(
            "📝 Job Description:",
            height=150,
            placeholder="Senior Python Developer with 5+ years...",
            key="job_desc"
        )
        
        uploaded_files = st.file_uploader(
            "📤 Upload CVs (PDF)",
            type="pdf",
            accept_multiple_files=True
        )
        
        process_button = st.button("🚀 Analyze Candidates", type="primary", use_container_width=True)
    
    with tab2:
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
    
    with tab3:
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
            st.info("🎯 Categorize candidates by minimum score (%)")
            
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
            
            st.session_state.use_thresholds = True
            st.session_state.shortlist_threshold = shortlist_threshold
            st.session_state.longlist_threshold = longlist_threshold
            st.session_state.longlist_count = 500
            st.session_state.shortlist_count = 500
            
            # For threshold mode, update display values
            longlist_count = 500
            shortlist_count = 500
        
        st.divider()
        st.caption(f"📊 Longlist: Top {longlist_count} candidates")
        st.caption(f"🎯 Shortlist: Top {shortlist_count} candidates")
    
    # Candidate Pool Management Tab
    tab4 = st.tabs(["🌐 Candidate Pool"])[0]
    
    with tab4:
        st.subheader("🌐 Candidate Pool Manager")
        st.info("Manage candidates across multiple job openings")
        
        # Initialize candidate pool
        if 'candidate_pool' not in st.session_state:
            st.session_state.candidate_pool = CandidatePool()
        
        pool = st.session_state.candidate_pool
        
        # Pool Statistics
        stats = pool.get_pool_statistics()
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Candidates", stats['total_candidates'])
        with col2:
            st.metric("Total Jobs", stats['total_jobs'])
        with col3:
            st.metric("Avg Score", f"{stats['average_score']:.1f}%")
        
        st.divider()
        
        # Pool actions
        pool_action = st.radio("Choose action:", options=["View Pool", "Export Pool", "Clear Pool"])
        
        if pool_action == "View Pool":
            candidates = pool.get_all_candidates()
            if candidates:
                pool_df = pd.DataFrame([{
                    'Candidate': c['filename'],
                    'Email': c['email'],
                    'Job': c['job_title'],
                    'Score': f"{c['final_score']}%",
                    'Seniority': c['cv_seniority'].title(),
                    'Added': c['added_date'][:10]
                } for c in candidates])
                st.dataframe(pool_df, use_container_width=True, hide_index=True)
            else:
                st.info("No candidates in pool yet")
        
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
if process_button and job_description and uploaded_files:
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
            results.append(result)
        except Exception as e:
            st.error(f"Error processing {uploaded_file.name}: {str(e)}")
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
    
    status_text.empty()
    progress_bar.empty()
    
    st.session_state.results = results
    st.success(f"✅ Analysis complete! {len(results)} candidate(s) processed")

# Display results
if st.session_state.results:
    results = st.session_state.results
    
    # Initialize report generator early
    report_gen = ReportGenerator()
    
    # Apply filtering based on selection mode
    if st.session_state.get('use_thresholds', False):
        # Threshold-based categorization
        categorized = report_gen.categorize_by_thresholds(
            results,
            shortlist_threshold=st.session_state.shortlist_threshold,
            longlist_threshold=st.session_state.longlist_threshold
        )
        categorized = report_gen.categorize_by_thresholds(
            results,
            shortlist_threshold=st.session_state.shortlist_threshold,
            longlist_threshold=st.session_state.longlist_threshold
        )
        
        # Only show candidates above minimum threshold
        results_sorted = categorized['shortlist'] + categorized['longlist']
        results_sorted = sorted(results_sorted, key=lambda x: x['final_score'], reverse=True)
        rejected_candidates = categorized['rejected']
        
        st.info(f"""
        📊 **Threshold-Based Selection Results:**
        - 🎯 Shortlist: {len(categorized['shortlist'])} candidates (≥{st.session_state.shortlist_threshold}%)
        - 📋 Longlist: {len(categorized['longlist'])} candidates (≥{st.session_state.longlist_threshold}%)
        - ❌ Rejected: {len(categorized['rejected'])} candidates (below {st.session_state.longlist_threshold}%)
        """)
    else:
        # Ranking-based (original behavior)
        results_sorted = sorted(results, key=lambda x: x['final_score'], reverse=True)
        rejected_candidates = []
    
    # === RANKING DASHBOARD ===
    st.markdown('<div class="subheader-title">🏆 Candidate Ranking</div>', unsafe_allow_html=True)
    
    ranking_data = []
    for idx, result in enumerate(results_sorted, 1):
        ranking_data.append({
            'Rank': idx,
            'Candidate': result['filename'],
            'Score': f"{result['final_score']}%",
            'Confidence': result['confidence_level'],
            'Matched': f"{len(result['matched_skills'])}",
            'Missing': f"{len(result['missing_skills'])}",
            'Seniority': result['cv_seniority'].title(),
        })
    
    ranking_df = pd.DataFrame(ranking_data)
    st.dataframe(ranking_df, use_container_width=True, hide_index=True)
    
    st.divider()
    
    # === DETAILED ANALYSIS ===
    st.markdown('<div class="subheader-title">📊 Detailed Candidate Analysis</div>', unsafe_allow_html=True)
    
    for idx, result in enumerate(results_sorted, 1):
        with st.expander(f"#{idx} - {result['filename']} ({result['confidence_level']}) 👤", expanded=(idx == 1)):
            
            # Score visualization
            final_score = result['final_score']
            if final_score >= 85:
                score_class = "score-excellent"
            elif final_score >= 70:
                score_class = "score-good"
            elif final_score >= 60:
                score_class = "score-moderate"
            else:
                score_class = "score-low"
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown(f"<div class='{score_class}'>{result['confidence_emoji']} {final_score}% Match</div>", unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"<div class='confidence-label confidence-{result['confidence_level'].lower().replace(' ', '-')}'>{result['confidence_level']}</div>", unsafe_allow_html=True)
            
            # Score breakdown in 3 rows
            st.markdown("**📈 Scoring Breakdown:**")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Semantic Match", f"{result['score_breakdown']['semantic_similarity']:.1f}%")
            with col2:
                st.metric("Skills Match", f"{result['score_breakdown']['skills_match']:.1f}%")
            with col3:
                st.metric("Experience", f"{result['score_breakdown']['experience_relevance']:.1f}%")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Keyword Density", f"{result['score_breakdown']['keyword_density']:.1f}%")
            with col2:
                st.metric("Culture Fit", f"{result['score_breakdown']['culture_fit']:.1f}%")
            with col3:
                st.metric("Seniority Match", f"{result['score_breakdown']['seniority_alignment']:.1f}%")
            
            st.caption("Formula: 35% Semantic + 25% Skills + 15% Experience + 15% Keywords + 5% Culture + 5% Seniority")
            
            st.divider()
            
            # Seniority info
            seniority_match = "✅ Perfect alignment" if result['cv_seniority'] == result['job_seniority'] else "⚠️ Seniority mismatch"
            st.info(f"**Candidate Level:** {result['cv_seniority'].title()} | **Required:** {result['job_seniority'].title()} - {seniority_match}")
            
            st.divider()
            
            # Matched skills with proficiency
            if result['matched_skills']:
                st.markdown("**✅ Matched Skills:**")
                cols = st.columns(min(4, len(result['matched_skills'])))
                for skill_idx, skill in enumerate(result['matched_skills']):
                    with cols[skill_idx % len(cols)]:
                        proficiency = result['skill_proficiency'].get(skill, 'Missing Information')
                        badge_class = proficiency.lower()
                        st.markdown(f"<div class='proficiency-badge {badge_class}'>{skill.title()}<br/>{proficiency}</div>", unsafe_allow_html=True)
            else:
                st.warning("No skills matched")
            
            st.divider()
            
            # Missing skills & recommendations
            if result['missing_skills']:
                st.markdown(f"**❌ Missing Skills ({len(result['missing_skills'])}):**")
                missing_list = ", ".join([s.title() for s in result['missing_skills']])
                st.warning(missing_list)
                
                if result['recommendations']:
                    st.markdown("**💡 Learning Recommendations:**")
                    for rec in result['recommendations'][:5]:  # Top 5
                        priority_icon = "🔴" if rec['priority'] == 'high' else "🟡"
                        effort_bar = "█" * rec['effort'] + "░" * (4 - rec['effort'])
                        st.markdown(f"""
                        <div class="recommendation-box">
                        <strong>{priority_icon} {rec['skill'].title()}</strong><br/>
                        {rec['suggestion']}<br/>
                        ⏱️ {rec['time']} | Effort: {effort_bar}
                        </div>
                        """, unsafe_allow_html=True)
            
            st.divider()
            
            # Bias awareness
            if result['bias_warnings']:
                st.markdown("**⚖️ Bias Awareness Alerts:**")
                for warning_text, warning_type in result['bias_warnings']:
                    st.markdown(f"""
                    <div class="bias-alert">
                    <strong>⚠️ {warning_text}</strong>
                    </div>
                    """, unsafe_allow_html=True)
                st.caption("💡 Evaluate candidates fairly based on qualifications and merit.")
            else:
                st.success("✓ No obvious bias indicators detected")
            
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
                if st.button(f"💾 Add to Pool", use_container_width=True, key=f"add_pool_{idx}"):
                    pool = st.session_state.candidate_pool
                    job_title = st.session_state.get('current_job_title', 'Job Position')
                    pool.add_candidate(result, f"job_{idx}", job_title)
                    st.success("✓ Added to candidate pool!")
            
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
        st.markdown('<div class="subheader-title">📈 Comparative Analysis</div>', unsafe_allow_html=True)
        
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
    st.markdown('<div class="subheader-title">📋 Longlist & 🎯 Shortlist</div>', unsafe_allow_html=True)
    
    # Determine longlist and shortlist based on mode
    if st.session_state.get('use_thresholds', False):
        # Threshold-based: use categorized results
        shortlist = [r for r in results_sorted if r['final_score'] >= st.session_state.shortlist_threshold]
        longlist = [r for r in results_sorted if st.session_state.longlist_threshold <= r['final_score'] < st.session_state.shortlist_threshold]
    else:
        # Ranking-based: use top N
        longlist_count = st.session_state.longlist_count
        shortlist_count = st.session_state.shortlist_count
        longlist = results_sorted[:longlist_count]
        shortlist = results_sorted[:shortlist_count]
    
    # Longlist
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader(f"📋 LONGLIST ({len(longlist)})")
        
        longlist_data = []
        for idx, result in enumerate(longlist, 1):
            longlist_data.append({
                'Position': idx,
                'Name': result['filename'],
                'Score': f"{result['final_score']}%",
                'Level': result['cv_seniority'].title(),
                'Matched Skills': len(result['matched_skills']),
                'Status': '✅ LONGLIST'
            })
        
        if longlist_data:
            longlist_df = pd.DataFrame(longlist_data)
            st.dataframe(longlist_df, use_container_width=True, hide_index=True)
            st.success(f"✓ {len(longlist)} candidate(s) selected for longlist")
        else:
            st.warning("No candidates meet the longlist criteria")
    
    # Shortlist
    with col2:
        st.subheader(f"🎯 SHORTLIST ({len(shortlist)})")
        
        shortlist_data = []
        for idx, result in enumerate(shortlist, 1):
            shortlist_data.append({
                'Position': idx,
                'Name': result['filename'],
                'Score': f"{result['final_score']}%",
                'Confidence': result['confidence_level'],
                'Fit': f"{result['score_breakdown']['semantic_similarity']:.0f}%",
                'Status': '🎯 SHORTLIST'
            })
        
        if shortlist_data:
            shortlist_df = pd.DataFrame(shortlist_data)
            st.dataframe(shortlist_df, use_container_width=True, hide_index=True)
            st.info(f"ℹ️ {len(shortlist)} candidate(s) selected for interviews")
        else:
            st.warning("No candidates meet the shortlist criteria")
    
    # === RECOMMENDATIONS ===
    st.divider()
    st.markdown('<div class="subheader-title">🎯 HR Recommendations</div>', unsafe_allow_html=True)
    
    if not results_sorted:
        st.warning("⚠️ No candidates meet the minimum threshold requirements. Please adjust your settings and try again.")
    else:
        top_candidate = results_sorted[0]
        
        if top_candidate['final_score'] >= 85:
            st.success(f"""
            ### ✅ EXCELLENT MATCH
            **{top_candidate['filename']}** - {top_candidate['final_score']}%
            
            This candidate is **highly qualified** and aligns exceptionally well with requirements.
            - ✓ Strong skill alignment
            - ✓ Relevant experience
            - ✓ High semantic match
            
            **Recommendation:** Immediate interview - top priority candidate.
            """)
        elif top_candidate['final_score'] >= 70:
            st.info(f"""
            ### ⭐ STRONG MATCH
            **{top_candidate['filename']}** - {top_candidate['final_score']}%
            
            This candidate shows **good alignment** with role requirements.
            - ✓ Most required skills present
            - ✓ Relevant background
            - ⚠️ Some minor skill gaps
            
            **Recommendation:** Schedule interview. Discuss learning commitment for skill gaps.
            """)
        elif top_candidate['final_score'] >= 60:
            st.warning(f"""
            ### 🟡 MODERATE MATCH
            **{top_candidate['filename']}** - {top_candidate['final_score']}%
            
            This candidate has **potential** but significant gaps exist.
            - ⚠️ Multiple skill gaps
            - ⚠️ Partial experience match
            - ⚠️ Needs development in key areas
            
            **Recommendation:** Consider for growth-focused role or with training support.
            """)
        else:
            st.error(f"""
            ### 🔴 WEAK MATCH
            **{top_candidate['filename']}** - {top_candidate['final_score']}%
            
            This candidate **does not meet** core requirements.
            - ✗ Major skill gaps
            - ✗ Limited experience alignment
            - ✗ Significant development needed
            
            **Recommendation:** Consider for different roles or revisit later after skill development.
            """)
            
            # Export summary (only if there are candidates)
            st.divider()
            st.markdown('<div class="subheader-title">📥 Export & Reports</div>', unsafe_allow_html=True)
            
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
        st.markdown('<div class="subheader-title">❌ Rejected Candidates (Below Minimum Threshold)</div>', unsafe_allow_html=True)
        
        rejected_df = pd.DataFrame([{
            'Candidate': c['filename'],
            'Score': f"{c['final_score']}%",
            'Email': c.get('candidate_email', 'N/A'),
            'Confidence': c['confidence_level'],
            'Matched Skills': len(c['matched_skills']),
            'Missing Skills': len(c['missing_skills']),
            'Seniority': c['cv_seniority'].title(),
        } for c in rejected_candidates])
        
        st.dataframe(rejected_df, use_container_width=True, hide_index=True)
        
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
            st.markdown('<div class="subheader-title">🚀 Advanced Analytics & Features</div>', unsafe_allow_html=True)
    
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
    if not job_description and not uploaded_files:
        st.info("👈 **Step 1:** Enter job description in the sidebar")
        st.info("👈 **Step 2:** Upload CVs in the sidebar")
        st.info("👈 **Step 3:** Click 'Analyze Candidates'")
