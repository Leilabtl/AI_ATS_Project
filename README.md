# 🧭 HR Compass - AI Talent Navigation

An advanced, explainable AI-powered Applicant Tracking System (ATS) designed to streamline recruitment, rank candidates with semantic intelligence, and generate professional PDF reports.

## ✨ Project Overview
HR Compass is a state-of-the-art recruitment tool built for the **AI In Practice** course at **XAMK**. It leverages modern NLP techniques to bridge the gap between job requirements and candidate potential.

---

## 🎯 Key Features List

### 1. 🧠 Intelligent Candidate Matching
- **Semantic Scoring:** Goes beyond keywords to understand the meaning behind experience.
- **Explainable AI:** Provides a breakdown of why a candidate scored a certain way.
- **Bias Detection:** Alerts recruiters to potential biases in selection.
- **Skill Gap Analysis:** Automatically identifies missing skills and recommends learning paths.

### 2. 📄 Professional Reporting
- **PDF Report Generation:** One-click generation of beautifully formatted candidate summaries.
- **Color-Coded Rankings:** Visual indicators for Shortlist (🎯), Longlist (📋), and Rejected candidates.
- **Export Formats:** Full support for PDF, CSV, and TXT data exports.

### 3. 📧 Communication Suite (BCC Ready)
- **Email Templates:** Professionally crafted templates for invitations, status updates, and rejections.
- **BCC Batching:** Generate recipient lists ready for your email client's BCC field to maintain privacy.
- **Employer Branding:** Ensures consistent and high-quality communication with every applicant.

### 4. 🌐 Candidate Pool Management
The system includes a persistent pool to manage candidates across different job openings and timeframes.
- **Cross-Job Storage:** Candidates are stored and categorized globally, allowing for easy re-matching when new roles open.
- **Job Recommendations:** Automatically suggests other open roles for candidates based on their specific skill sets.
- **Statistics & Insights:** Real-time analytics on average scores, seniority distribution, and pool growth.
- **Folder Organization:** Automatically creates structured folders (`candidate_pools/`) to keep candidate data organized by job title.
- **Persistent Data:** All pool data is saved locally in `candidate_pool.json`, ensuring no data loss between sessions.

### 5. 📦 High-Scale Batch Processing
- **Multi-CV Upload:** Support for uploading 50-500+ resumes simultaneously.
- **Fast Analysis:** Processing speeds of ~1-2 seconds per candidate.
- **Memory Optimization:** Built to handle large datasets efficiently within browser environments.

### 6. 🛠️ Advanced Tools
- **Proactive Tagging:** Automatic tagging of candidates based on detected expertise levels.
- **Role Dictionary:** Pre-configured and customizable job titles for quick setup.
- **Explainable Analytics:** Detailed breakdown of match scores.

---

## 🚀 Technical Stack
- **Frontend/Backend:** [Streamlit](https://streamlit.io/) (Python-based Web Framework)
- **Intelligence Engine:** Python NLP libraries & Custom Matching Algorithms
- **Data Handling:** JSON & Pandas
- **Document Engine:** ReportLab (for PDF generation)
- **Styling:** Custom CSS for a premium, corporate dark-mode experience

---

## 💻 Local Setup & Installation

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/Leilabtl/AI_ATS_Project.git
   cd AI_ATS_Project
   ```

2. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the Application:**
   ```bash
   streamlit run streamlit_app.py
   ```
   *The app will typically be available at `http://localhost:8501`*

---

## 🌐 Deployment
This project is optimized for deployment on **Streamlit Community Cloud**. To deploy:
1. Push the latest code to your GitHub `main` branch.
2. Connect your repository to [share.streamlit.io](https://share.streamlit.io).
3. The app will be live at a custom `*.streamlit.app` URL.

---

## 🎓 Academic Context
- **Assignment:** Assignment Spring 2026
- **Course:** AI In Practice
- **Institution:** Kaakkois-Suomen ammattikorkeakoulu Oy (XAMK)
- **Developer:** Leila Baratlou

---

**Status:** ✅ Fully Operational | **Version:** 2.1
