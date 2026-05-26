"""
Generate comprehensive ATS reports with PDF, CSV, and Email support.
"""
import re
import pandas as pd
from datetime import datetime
import json
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from io import BytesIO
from ui_components import candidate_name as _candidate_name

# What each curated skill enables in a role — shown in the Role Requirements Coverage section
_SKILL_INTEL = {
    'python':           'Automates data workflows, scripting, and back-end service development.',
    'java':             'Enterprise back-end systems, APIs, and high-throughput services.',
    'sql':              'Querying databases, generating structured reports, and data extraction.',
    'javascript':       'Interactive front-end experiences and web application development.',
    'docker':           'Consistent deployment environments and CI/CD pipeline support.',
    'aws':              'Cloud infrastructure for scalable deployments, storage, and compute.',
    'azure':            'Microsoft cloud: infrastructure, AI services, and enterprise integration.',
    'gcp':              'Google cloud for data analytics, ML pipelines, and scalable compute.',
    'machine learning': 'Predictive analytics, intelligent recommendations, and pattern recognition.',
    'computer vision':  'Image and video analysis for recognition, detection, and automation.',
    'data analysis':    'Translates raw data into insights through metrics, trends, and reporting.',
    'api design':       'Structures interfaces between services for integration and interoperability.',
    'ci/cd':            'Automates build, test, and deploy pipelines for fast, reliable releases.',
    'git':              'Version control, collaboration, and code-change tracking across teams.',
    'mobile dev':       'Native or cross-platform mobile apps for iOS and Android.',
    'data engineering': 'Reliable pipelines to move and transform data at scale for analytics.',
    'cybersecurity':    'Safeguards systems, data, and infrastructure against threats.',
    'c++':              'High-performance systems, embedded software, and latency-critical apps.',
    'c#':               'Microsoft ecosystem: enterprise apps, Unity games, and Azure services.',
    'golang':           'High-concurrency microservices and efficient back-end APIs.',
    'rust':             'Memory-safe, high-performance system-level programming.',
    'php':              'Web application back-ends and CMS platforms (WordPress, Laravel).',
    'ruby':             'Rapid web development with Rails; common in SaaS products.',
    'scala':            'Functional programming for big data processing (especially Apache Spark).',
    'r language':       'Statistical analysis and data visualisation for research and analytics.',
    'linux':            'Server administration, scripting, and working in cloud environments.',
    'project management': 'Coordinates delivery, timelines, stakeholder communication, and cross-team execution.',
    'ui/ux':            'User-centred design that improves engagement and product usability.',
    'kubernetes':       'Orchestrates containerised workloads with self-healing and auto-scaling.',
    # ── HR / Business domain ──────────────────────────────────────────────────
    'hris':                'Manages employee records, payroll, and HR workflows through platform systems like Workday or ADP.',
    'hr analytics':        'Drives data-driven HR decisions through workforce metrics, attrition analysis, and headcount planning.',
    'talent management':   'Covers the full recruitment lifecycle — sourcing, assessment, onboarding, and retention.',
    'compensation':        'Structures pay, benefits, and total-rewards packages to attract and retain talent fairly.',
    'compliance':          'Ensures the organisation meets labour law, data privacy, and regulatory obligations.',
    'finance':             'Supports budgeting, forecasting, P&L analysis, and financial reporting for business decisions.',
    'erp':                 'Manages core business processes (finance, procurement, inventory) through integrated ERP platforms.',
    'crm':                 'Tracks customer relationships, pipeline, and sales performance through CRM platforms.',
    'business intelligence': 'Converts operational data into dashboards and reports that inform executive decisions.',
    'embedded systems':      'Develops low-level firmware and drivers for microcontrollers and real-time hardware.',
    'embedded protocols':    'Implements hardware communication interfaces (UART, SPI, I2C, CAN) for device integration.',
    'project tools':         'Plans and tracks project delivery through tools like Jira, Asana, Smartsheet, or MS Project.',
    'ux research':           'Validates design decisions through user interviews, usability tests, wireframes, and prototypes.',
    'marketing tools':       'Executes and measures campaigns using Google Ads, SEMrush, HubSpot, GA4, and similar platforms.',
}

class ReportGenerator:
    """Generate detailed reports for ATS analysis."""
    
    def __init__(self):
        self.timestamp = datetime.now()
    
    def generate_pdf_report(self, results, job_description, longlist_count=None, shortlist_count=None):
        """Generate comprehensive PDF report with all candidate details."""
        
        # Create PDF in memory
        pdf_buffer = BytesIO()
        doc = SimpleDocTemplate(pdf_buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
        
        # Container for PDF elements
        story = []
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#667eea'),
            spaceAfter=12,
            alignment=1  # Center
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#764ba2'),
            spaceAfter=10,
            spaceBefore=10
        )
        
        # Title
        story.append(Paragraph("🧭 HR Compass - COMPREHENSIVE CANDIDATE REPORT", title_style))
        story.append(Paragraph(f"Generated: {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
        story.append(Spacer(1, 0.2*inch))
        
        # Summary table
        story.append(Paragraph("SUMMARY", heading_style))
        summary_data = [
            ['Total Candidates', str(len(results))],
            ['Longlist Count', str(min(longlist_count or 200, len(results)))],
            ['Shortlist Count', str(min(shortlist_count or 20, len(results)))],
            ['Job Description Length', f"{len(job_description)} characters"],
        ]
        summary_table = Table(summary_data, colWidths=[2.5*inch, 2*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e8eaf6')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Ranking table
        story.append(Paragraph("CANDIDATE RANKING", heading_style))
        ranking_data = [['Rank', 'Candidate', 'Score', 'Confidence', 'Matched Skills', 'Status']]
        
        for idx, result in enumerate(sorted(results, key=lambda x: x['final_score'], reverse=True), 1):
            longlist_threshold = longlist_count or 200
            shortlist_threshold = shortlist_count or 20
            
            if idx <= shortlist_threshold:
                status = '🎯 SHORTLIST'
            elif idx <= longlist_threshold:
                status = '📋 LONGLIST'
            else:
                status = 'Rejected'
            
            ranking_data.append([
                str(idx),
                _candidate_name(result['filename']),
                f"{result['final_score']}%",
                result['confidence_level'],
                str(len(result['matched_skills'])),
                status
            ])
        
        ranking_table = Table(ranking_data, colWidths=[0.6*inch, 1.5*inch, 0.8*inch, 1*inch, 1.2*inch, 1*inch])
        ranking_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
        ]))
        story.append(ranking_table)
        story.append(Spacer(1, 0.2*inch))
        
        # Build PDF
        doc.build(story)
        pdf_buffer.seek(0)
        
        return pdf_buffer.getvalue()
    
    def generate_individual_pdf_report(self, result):
        """Generate a professional, HR-readable PDF report for one candidate."""

        def _strip(text):
            """Remove markdown bold markers so text reads cleanly in PDF."""
            return re.sub(r'\*\*(.+?)\*\*', r'\1', str(text)).strip()

        def _skills_list(r, key):
            v = r.get(key, [])
            return list(v.keys()) if isinstance(v, dict) else list(v)

        name        = _candidate_name(result['filename'])
        score       = result['final_score']
        confidence  = result.get('confidence_level', '')
        cv_level    = result.get('cv_seniority', 'unspecified').title()
        job_level   = result.get('job_seniority', 'unspecified').title()
        matched     = _skills_list(result, 'matched_skills')
        missing     = _skills_list(result, 'missing_skills')
        llm         = result.get('llm_analysis') or {}
        llm_rec     = llm.get('interview_recommendation', '')

        # Verdict colours
        if score >= 75:
            verdict_color = colors.HexColor('#16a34a')
            verdict_bg    = colors.HexColor('#f0fdf4')
            verdict_label = 'STRONG MATCH — RECOMMENDED FOR INTERVIEW'
        elif score >= 60:
            verdict_color = colors.HexColor('#d97706')
            verdict_bg    = colors.HexColor('#fffbeb')
            verdict_label = 'MODERATE MATCH — CONSIDER FOR INTERVIEW'
        elif score >= 45:
            verdict_color = colors.HexColor('#ea580c')
            verdict_bg    = colors.HexColor('#fff7ed')
            verdict_label = 'WEAK MATCH — FURTHER SCREENING ADVISED'
        else:
            verdict_color = colors.HexColor('#dc2626')
            verdict_bg    = colors.HexColor('#fef2f2')
            verdict_label = 'LOW MATCH — NOT RECOMMENDED AT THIS TIME'

        if llm_rec == 'Shortlist':
            verdict_label = 'AI RECOMMENDATION: SHORTLIST — INTERVIEW NOW'
            verdict_color = colors.HexColor('#16a34a')
        elif llm_rec == 'Decline':
            verdict_label = 'AI RECOMMENDATION: DECLINE'
            verdict_color = colors.HexColor('#dc2626')
        elif llm_rec == 'Consider':
            verdict_label = 'AI RECOMMENDATION: CONSIDER'
            verdict_color = colors.HexColor('#d97706')

        pdf_buffer = BytesIO()
        doc = SimpleDocTemplate(
            pdf_buffer, pagesize=letter,
            topMargin=0.6*inch, bottomMargin=0.6*inch,
            leftMargin=0.75*inch, rightMargin=0.75*inch
        )
        page_w = letter[0] - 1.5*inch  # usable width

        styles = getSampleStyleSheet()
        body_style = ParagraphStyle('Body', parent=styles['Normal'],
                                    fontSize=10, leading=15, textColor=colors.HexColor('#374151'))
        section_style = ParagraphStyle('Section', parent=styles['Normal'],
                                       fontSize=11, fontName='Helvetica-Bold',
                                       textColor=colors.HexColor('#1e293b'),
                                       spaceBefore=14, spaceAfter=6,
                                       borderPad=4)
        small_style = ParagraphStyle('Small', parent=styles['Normal'],
                                     fontSize=9, leading=13, textColor=colors.HexColor('#6b7280'))

        story = []

        # ── HEADER BAND ───────────────────────────────────────────────────────
        header_data = [[
            Paragraph(f'<font size="20"><b>{name}</b></font>', ParagraphStyle(
                'H', parent=styles['Normal'], fontSize=20, fontName='Helvetica-Bold',
                textColor=colors.HexColor('#0f172a'))),
            Paragraph(
                f'<font size="28"><b>{score:.0f}</b></font>'
                f'<font size="11" color="#6b7280"> / 100</font>',
                ParagraphStyle('Score', parent=styles['Normal'], alignment=2,
                               textColor=verdict_color))
        ]]
        header_table = Table(header_data, colWidths=[page_w * 0.65, page_w * 0.35])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('LINEBELOW', (0, 0), (-1, -1), 1.5, colors.HexColor('#e2e8f0')),
        ]))
        story.append(header_table)

        # Verdict banner
        verdict_data = [[Paragraph(
            f'<font color="{verdict_color.hexval()}" size="10"><b>{verdict_label}</b></font>',
            ParagraphStyle('V', parent=styles['Normal'], alignment=1))]]
        verdict_table = Table(verdict_data, colWidths=[page_w])
        verdict_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), verdict_bg),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('ROUNDEDCORNERS', [4]),
        ]))
        story.append(Spacer(1, 0.1*inch))
        story.append(verdict_table)

        # Meta line
        story.append(Spacer(1, 0.08*inch))
        story.append(Paragraph(
            f'Report generated {datetime.now().strftime("%d %B %Y, %H:%M")} &nbsp;·&nbsp; '
            f'Confidence: {confidence} &nbsp;·&nbsp; HR Compass ATS',
            small_style))
        story.append(Spacer(1, 0.18*inch))

        # ── SECTION 1: EXECUTIVE SUMMARY ─────────────────────────────────────
        story.append(Paragraph('1.  Executive Summary', section_style))

        if llm.get('executive_summary'):
            summary_text = _strip(llm['executive_summary'])
        elif result.get('strategic_summary'):
            summary_text = _strip(result['strategic_summary'])
        else:
            fit = 'strong' if score >= 75 else 'moderate' if score >= 55 else 'weak'
            summary_text = (
                f'{name} presents a {fit} match for this role, achieving an overall score of '
                f'{score:.0f}%. '
                f'The candidate is identified as {cv_level} level against a {job_level}-level requirement. '
            )
            if matched:
                summary_text += f'Confirmed skills include {", ".join(s.title() for s in matched[:3])}. '
            if missing:
                summary_text += f'Key gaps: {", ".join(s.title() for s in missing[:3])}.'

        story.append(Paragraph(summary_text, body_style))

        if llm.get('key_strengths'):
            story.append(Spacer(1, 0.08*inch))
            story.append(Paragraph('<b>Key strengths identified:</b>', body_style))
            for s in llm['key_strengths'][:4]:
                story.append(Paragraph(f'  ✓  {_strip(s)}', body_style))

        story.append(Spacer(1, 0.12*inch))

        # ── SECTION 2: SCORE BREAKDOWN ────────────────────────────────────────
        story.append(Paragraph('2.  Scoring Breakdown', section_style))

        sb = result.get('score_breakdown', {})
        factors = [
            ('Skills Match',    sb.get('skills_match', 0),        25,
             'How many of the JD\'s required skills appear in the CV'),
            ('Keyword Overlap', sb.get('semantic_similarity', 0), 35,
             'Word-level overlap between CV and job description'),
            ('Experience',      sb.get('experience_relevance', 0),15,
             'Evidence of seniority, tenure, and accomplishments'),
            ('Keyword Density', sb.get('keyword_density', 0),     15,
             'Concentration of JD terms throughout the CV'),
            ('Culture Fit',     sb.get('culture_fit', 0),          5,
             'Soft-skill indicators: teamwork, communication, innovation'),
            ('Seniority Fit',   sb.get('seniority_alignment', 0),  5,
             'Seniority level match between candidate and role'),
        ]
        breakdown_rows = [['Factor', 'Score', 'Weight', 'Status']]
        for label, val, weight, _ in factors:
            status = 'Strong' if val >= 75 else 'Moderate' if val >= 50 else 'Weak'
            breakdown_rows.append([label, f'{val:.0f}%', f'{weight}%', status])

        bt = Table(breakdown_rows, colWidths=[page_w*0.36, page_w*0.16, page_w*0.14, page_w*0.34])
        bt.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e293b')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (1, 0), (2, -1), 'CENTER'),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            # Colour the Status column
            *[('TEXTCOLOR', (3, i+1), (3, i+1),
               colors.HexColor('#16a34a') if factors[i][1] >= 75
               else colors.HexColor('#d97706') if factors[i][1] >= 50
               else colors.HexColor('#dc2626'))
              for i in range(len(factors))],
            *[('FONTNAME', (3, i+1), (3, i+1), 'Helvetica-Bold') for i in range(len(factors))],
        ]))
        story.append(bt)
        story.append(Spacer(1, 0.12*inch))

        # ── SECTION 3: ROLE REQUIREMENTS COVERAGE ────────────────────────────
        story.append(Paragraph('3.  Role Requirements Coverage', section_style))

        cell_style = ParagraphStyle('Cell', parent=styles['Normal'],
                                    fontSize=8, leading=11, textColor=colors.HexColor('#374151'))

        # Only include curated skills (filter out garbage from pre-fix pool records)
        curated_keys = set(_SKILL_INTEL.keys())
        matched_curated = [s for s in matched if s.lower() in curated_keys]
        missing_curated = [s for s in missing
                           if s.lower() in curated_keys and s not in matched_curated]
        all_jd_req = matched_curated + missing_curated
        total_req  = len(all_jd_req)
        covered    = len(matched_curated)

        if total_req > 0:
            cov_pct = int(covered / total_req * 100)
            cov_hex = '#16a34a' if cov_pct >= 70 else '#d97706' if cov_pct >= 40 else '#dc2626'
            story.append(Paragraph(
                f'<font color="{cov_hex}"><b>{covered} of {total_req} required capabilities '
                f'confirmed ({cov_pct}% coverage)</b></font>',
                body_style))
            story.append(Spacer(1, 0.07*inch))

            req_rows   = [['Requirement', 'Status', 'Proficiency', 'What This Enables in the Role']]
            row_bgs    = []
            status_col = []
            for i, sk in enumerate(all_jd_req[:14], 1):
                is_match  = sk in matched_curated
                status    = '✓  Confirmed' if is_match else '✗  Not found'
                prof      = result.get('skill_proficiency', {}).get(sk, '—') if is_match else '—'
                role_val  = _SKILL_INTEL.get(sk.lower(),
                                'Relevant technical capability required for this role.')
                req_rows.append([
                    Paragraph(f'<b>{sk.title()}</b>', cell_style),
                    status,
                    prof,
                    Paragraph(role_val, cell_style),
                ])
                bg = colors.HexColor('#f0fdf4') if is_match else colors.HexColor('#fef2f2')
                row_bgs.append(('BACKGROUND', (0, i), (-1, i), bg))
                sc = colors.HexColor('#16a34a') if is_match else colors.HexColor('#dc2626')
                status_col.append(('TEXTCOLOR', (1, i), (1, i), sc))
                status_col.append(('FONTNAME',  (1, i), (1, i), 'Helvetica-Bold'))

            req_table = Table(
                req_rows,
                colWidths=[page_w*0.17, page_w*0.16, page_w*0.15, page_w*0.52]
            )
            req_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e293b')),
                ('TEXTCOLOR',  (0, 0), (-1, 0), colors.white),
                ('FONTNAME',   (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE',   (0, 0), (-1, 0), 9),
                ('TOPPADDING',    (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                ('LEFTPADDING',   (0, 0), (-1, -1), 5),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                *row_bgs,
                *status_col,
            ]))
            story.append(req_table)

        else:
            # No curated tech skills detected — provide meaningful context instead
            sb_ref = result.get('score_breakdown', {})
            sem_val = sb_ref.get('semantic_similarity', 0)
            kw_val  = sb_ref.get('keyword_density', 0)

            if sb_ref.get('skills_match', 0) == 50:
                # 50 is the fallback value — means the JD had no recognizable tech-skill keywords
                note = (
                    'The technical skill taxonomy did not identify specific named technologies in '
                    'this job description. This is common for non-technical roles (HR, Finance, '
                    'Operations, Management) where requirements are expressed as domain knowledge '
                    'and competencies rather than named tools or languages.'
                )
            else:
                note = (
                    'No specific skill overlap was identified between the candidate profile and '
                    'the job description requirements.'
                )
            story.append(Paragraph(note, small_style))
            story.append(Spacer(1, 0.08*inch))

            # Show what the text-based scores tell us
            sem_hex = '#16a34a' if sem_val >= 20 else '#d97706' if sem_val >= 10 else '#dc2626'
            kw_hex  = '#16a34a' if kw_val  >= 20 else '#d97706' if kw_val  >= 10 else '#dc2626'
            story.append(Paragraph(
                f'Text overlap with job description: '
                f'<font color="{sem_hex}"><b>{sem_val:.0f}%</b></font> &nbsp;·&nbsp; '
                f'JD keyword density in CV: '
                f'<font color="{kw_hex}"><b>{kw_val:.0f}%</b></font>',
                body_style))

            # Show improvement areas as domain signals
            concerns = [_strip(a) for a in result.get('improvement_areas', [])
                        if len(a.strip()) > 15
                        and 'Study fundamentals' not in a
                        and 'Acquire hands-on' not in a]
            if concerns:
                story.append(Spacer(1, 0.06*inch))
                story.append(Paragraph('<b>Areas noted for development:</b>', body_style))
                for c in concerns[:3]:
                    story.append(Paragraph(f'  ⚠  {c}', body_style))

        story.append(Spacer(1, 0.12*inch))

        # ── SECTION 4: SENIORITY ─────────────────────────────────────────────
        story.append(Paragraph('4.  Seniority & Experience Fit', section_style))
        level_match = cv_level.lower() == job_level.lower()
        level_icon  = '✓' if level_match else '⚠'
        level_note  = (
            f'{level_icon}  Candidate is {cv_level} level — role requires {job_level} level. '
        )
        if level_match:
            level_note += 'Seniority is aligned.'
        elif cv_level.lower() in ('senior', 'executive') and job_level.lower() in ('mid', 'junior'):
            level_note += 'Candidate may be over-qualified — worth discussing expectations.'
        else:
            level_note += (
                'This gap is a risk factor. Consider whether the candidate can step up quickly, '
                'or whether a more experienced hire is appropriate.'
            )
        story.append(Paragraph(level_note, body_style))
        story.append(Spacer(1, 0.12*inch))

        # ── SECTION 5: AI DEEP ANALYSIS (if GPT ran) ─────────────────────────
        if llm.get('critical_gaps') or llm.get('interview_focus_areas'):
            story.append(Paragraph('5.  AI-Powered Gap Analysis', section_style))

            gaps = llm.get('critical_gaps', [])
            if gaps:
                story.append(Paragraph('<b>Critical skill gaps identified by AI:</b>', body_style))
                gap_rows = [['Skill', 'Why It Matters', 'Priority', 'Time to Bridge']]
                for g in gaps[:5]:
                    gap_rows.append([
                        g.get('skill', '').title(),
                        _strip(g.get('importance', ''))[:80],
                        g.get('priority', '').title(),
                        g.get('estimated_time', '—'),
                    ])
                gt = Table(gap_rows, colWidths=[page_w*0.18, page_w*0.47, page_w*0.15, page_w*0.20])
                gt.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e293b')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 8),
                    ('TOPPADDING', (0, 0), (-1, -1), 5),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
                    ('WORDWRAP', (0, 0), (-1, -1), 1),
                ]))
                story.append(Spacer(1, 0.06*inch))
                story.append(gt)

            focus = llm.get('interview_focus_areas', [])
            if focus:
                story.append(Spacer(1, 0.1*inch))
                story.append(Paragraph('<b>Recommended interview focus areas:</b>', body_style))
                for i, f in enumerate(focus[:4], 1):
                    story.append(Paragraph(f'  {i}.  {_strip(f)}', body_style))

            narrative = llm.get('career_fit_narrative', '')
            if narrative:
                story.append(Spacer(1, 0.08*inch))
                story.append(Paragraph(
                    f'<b>Long-term career fit:</b> {_strip(narrative)}', body_style))

            story.append(Spacer(1, 0.12*inch))

        # ── SECTION 6: KEY CONCERNS ───────────────────────────────────────────
        concern_areas = [
            _strip(a) for a in result.get('improvement_areas', [])
            if len(a.strip()) > 20
            and 'Study fundamentals of' not in a
            and 'Acquire hands-on experience' not in a
        ]
        if concern_areas:
            story.append(Paragraph('6.  Key Concerns for the Hiring Manager', section_style))
            for area in concern_areas[:4]:
                story.append(Paragraph(f'⚠️  {area}', body_style))
                story.append(Spacer(1, 0.04*inch))
            story.append(Spacer(1, 0.08*inch))

        # ── SECTION 7: HR RECOMMENDATION ─────────────────────────────────────
        story.append(Paragraph('7.  HR Recommendation', section_style))

        if score >= 75:
            rec_text = (
                f'<b>Invite to interview.</b> {name} demonstrates solid alignment with the role '
                f'requirements (score: {score:.0f}%). Priority candidate — schedule a technical '
                f'interview to validate depth of skills.'
            )
        elif score >= 60:
            rec_text = (
                f'<b>Consider for interview — with caveats.</b> {name} scores {score:.0f}%, '
                f'indicating a partial fit. The candidate has relevant experience but notable gaps. '
                f'A screening call to assess motivation and learning agility is advised before '
                f'committing to a full interview slot.'
            )
        elif score >= 45:
            rec_text = (
                f'<b>Further screening required.</b> {name} scores {score:.0f}%, suggesting a weak '
                f'technical match for this specific role. Consider only if the candidate pool is '
                f'thin, or if the role can accommodate a longer onboarding period.'
            )
        else:
            rec_text = (
                f'<b>Do not progress at this time.</b> {name} scores {score:.0f}%, indicating '
                f'insufficient alignment with the core requirements. The candidate may be better '
                f'suited to a different role or seniority level.'
            )

        career_advice = _strip(result.get('career_advice', ''))
        if career_advice and score < 65:
            rec_text += f'<br/><br/><i>Alternative role suggestion: {career_advice}</i>'

        rec_data = [[Paragraph(rec_text, ParagraphStyle(
            'Rec', parent=styles['Normal'], fontSize=10, leading=15,
            textColor=colors.HexColor('#1e293b')))]]
        rec_table = Table(rec_data, colWidths=[page_w])
        rec_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), verdict_bg),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('LEFTPADDING', (0, 0), (-1, -1), 14),
            ('RIGHTPADDING', (0, 0), (-1, -1), 14),
            ('BOX', (0, 0), (-1, -1), 1.5, verdict_color),
            ('ROUNDEDCORNERS', [6]),
        ]))
        story.append(rec_table)
        story.append(Spacer(1, 0.15*inch))

        # ── FOOTER ────────────────────────────────────────────────────────────
        story.append(Paragraph(
            'This report was generated by HR Compass ATS. Scores are based on keyword matching '
            'and AI semantic analysis. Use as one input among several in hiring decisions.',
            ParagraphStyle('Footer', parent=styles['Normal'], fontSize=7,
                           textColor=colors.HexColor('#9ca3af'), alignment=1)))

        doc.build(story)
        pdf_buffer.seek(0)
        return pdf_buffer.getvalue()
    
    def categorize_by_thresholds(self, results, shortlist_threshold=70, longlist_threshold=50, shortlist_count=20, longlist_count=200):
        """Categorize candidates by score thresholds and limit counts."""
        
        shortlist = []
        longlist = []
        rejected = []
        
        sorted_results = sorted(results, key=lambda x: x['final_score'], reverse=True)
        
        for result in sorted_results:
            if result['final_score'] >= shortlist_threshold and len(shortlist) < shortlist_count:
                shortlist.append(result)
            elif result['final_score'] >= longlist_threshold and len(longlist) < longlist_count:
                longlist.append(result)
            else:
                rejected.append(result)
        
        return {
            'shortlist': shortlist,
            'longlist': longlist,
            'rejected': rejected
        }
    
    def generate_comprehensive_csv(self, results, _job_description=None, _longlist_count=None, _shortlist_count=None):
        """Generate comprehensive CSV with all candidate details."""
        
        data = []
        
        for idx, result in enumerate(results, 1):
            candidate_data = {
                # Basic Info
                'Rank': idx,
                'Candidate_Name': _candidate_name(result['filename']),
                'Analysis_Date': self.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                
                # Overall Score
                'Final_Score': result['final_score'],
                'Confidence_Level': result['confidence_level'],
                
                # Score Breakdown
                'Semantic_Match_%': result['score_breakdown']['semantic_similarity'],
                'Skills_Match_%': result['score_breakdown']['skills_match'],
                'Experience_Relevance_%': result['score_breakdown']['experience_relevance'],
                'Keyword_Density_%': result['score_breakdown']['keyword_density'],
                'Culture_Fit_%': result['score_breakdown']['culture_fit'],
                'Seniority_Alignment_%': result['score_breakdown']['seniority_alignment'],
                
                # Seniority
                'Candidate_Level': result['cv_seniority'].title(),
                'Required_Level': result['job_seniority'].title(),
                
                # Skills
                'Matched_Skills_Count': len(result['matched_skills']),
                'Matched_Skills': '; '.join([s.title() for s in result['matched_skills']]),
                'Missing_Skills_Count': len(result['missing_skills']),
                'Missing_Skills': '; '.join([s.title() for s in result['missing_skills']]),
                
                # Proficiency
                'Skill_Proficiency_Details': json.dumps(result['skill_proficiency']),
                
                # Recommendations
                'Learning_Goals_Count': len(result['recommendations']),
                'Top_Learning_Goal': result['recommendations'][0]['skill'].title() if result['recommendations'] else 'None',
                
                # Bias Warnings
                'Bias_Warnings_Count': len(result['bias_warnings']),
                'Bias_Warnings': '; '.join([f"{w[0]} ({w[1]})" for w in result['bias_warnings']]) if result['bias_warnings'] else 'None',
                
                # Status
                'Recommendation': self._get_recommendation(result['final_score']),
            }
            
            data.append(candidate_data)
        
        df = pd.DataFrame(data)
        return df
    
    def generate_email_groups(self, results, longlist_count=None, shortlist_count=None):
        """Generate email groups for rejected, longlist, and shortlist candidates."""
        
        longlist_count = longlist_count or 200
        shortlist_count = shortlist_count or 20
        
        sorted_results = sorted(results, key=lambda x: x['final_score'], reverse=True)
        
        email_groups = {
            'shortlist': [],
            'longlist': [],
            'rejected': []
        }
        
        for idx, result in enumerate(sorted_results, 1):
            candidate_info = {
                'name': _candidate_name(result['filename']),
                'email': result.get('candidate_email', f"candidate{idx}@example.com"),  # Extract from CV, fallback to placeholder
                'score': result['final_score'],
                'confidence': result['confidence_level'],
            }
            
            if idx <= shortlist_count:
                email_groups['shortlist'].append(candidate_info)
            elif idx <= longlist_count:
                email_groups['longlist'].append(candidate_info)
            else:
                email_groups['rejected'].append(candidate_info)
        
        return email_groups
    
    def generate_email_template(self, group_type, results, longlist_count=None, shortlist_count=None):
        """Generate email template with BCC list for a group."""
        
        email_groups = self.generate_email_groups(results, longlist_count, shortlist_count)
        group_data = email_groups.get(group_type, [])
        
        # BCC list (comma-separated, hiding recipient from others)
        bcc_list = ", ".join([c['email'] for c in group_data if c.get('email')])
        
        if group_type == 'shortlist':
            subject = "🧭 Congratulations! You've Been Selected for Interview - HR Compass"
            body = f"""Dear Candidate,

We are pleased to inform you that you have been selected for the next round of our recruitment process!

Your Profile Score: ###SCORE###%
Confidence Level: ###CONFIDENCE###

Next Steps:
1. You will receive an interview invitation shortly
2. Please confirm your availability within 48 hours
3. The interview will be conducted via Zoom

Interview Details:
- Duration: Approximately 45 minutes
- Topics: Technical skills, experience, and cultural fit
- Please prepare any questions you may have

We look forward to learning more about your experience and potential.

Best regards,
HR Team
ELITE ATS System"""
            
        elif group_type == 'longlist':
            subject = "Application Status Update - HR Compass"
            body = f"""Dear Candidate,

Thank you for your interest in our position. Your application has been carefully reviewed by our team.

Your Profile Score: ###SCORE###%
Confidence Level: ###CONFIDENCE###

While your background and qualifications are impressive, we have selected other candidates whose profiles closely match our current requirements. 

However, we would like to keep your profile active in our system for potential future opportunities that better align with your skills and experience. We will contact you if suitable positions become available.

We appreciate your interest in our company and encourage you to apply for other open positions on our careers page.

Best regards,
HR Team
TalentScout Pro System"""
            
        else:  # rejected
            subject = "Application Status - TalentScout Pro"
            body = f"""Dear Candidate,

Thank you for your interest in our company and for taking the time to submit your application.

Your Profile Score: ###SCORE###%

After careful consideration of your qualifications and our current requirements, we have decided to move forward with other candidates at this time.

We encourage you to stay updated with our career opportunities and apply again in the future if you find positions that match your expertise.

We wish you the best in your job search.

Best regards,
HR Team
TalentScout Pro System"""
        
        return {
            'subject': subject,
            'body': body,
            'bcc_list': bcc_list,
            'recipient_count': len(group_data),
            'group_data': group_data
        }
    
    def generate_email_bcc_report(self, results, longlist_count=None, shortlist_count=None):
        """Generate a report with BCC email lists for all groups."""
        
        report = []
        report.append("=" * 90)
        report.append("EMAIL DISTRIBUTION REPORT")
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("=" * 90)
        
        # Shortlist
        shortlist_template = self.generate_email_template('shortlist', results, longlist_count, shortlist_count)
        report.append(f"\n\n📧 SHORTLIST EMAIL")
        report.append(f"{'=' * 90}")
        report.append(f"Recipients: {shortlist_template['recipient_count']}")
        report.append(f"Subject: {shortlist_template['subject']}\n")
        report.append(f"BCC List (copy all for BCC field):")
        report.append(f"{shortlist_template['bcc_list']}\n")
        report.append(f"Body:\n{shortlist_template['body']}")
        
        # Longlist
        longlist_template = self.generate_email_template('longlist', results, longlist_count, shortlist_count)
        report.append(f"\n\n\n📧 LONGLIST EMAIL")
        report.append(f"{'=' * 90}")
        report.append(f"Recipients: {longlist_template['recipient_count']}")
        report.append(f"Subject: {longlist_template['subject']}\n")
        report.append(f"BCC List (copy all for BCC field):")
        report.append(f"{longlist_template['bcc_list']}\n")
        report.append(f"Body:\n{longlist_template['body']}")
        
        # Rejected
        rejected_template = self.generate_email_template('rejected', results, longlist_count, shortlist_count)
        report.append(f"\n\n\n📧 REJECTED EMAIL")
        report.append(f"{'=' * 90}")
        report.append(f"Recipients: {rejected_template['recipient_count']}")
        report.append(f"Subject: {rejected_template['subject']}\n")
        report.append(f"BCC List (copy all for BCC field):")
        report.append(f"{rejected_template['bcc_list']}\n")
        report.append(f"Body:\n{rejected_template['body']}")
        
        report.append(f"\n\n{'=' * 90}")
        report.append("INSTRUCTIONS:")
        report.append("1. Copy the BCC list from each group above")
        report.append("2. Open your email client (Gmail, Outlook, etc.)")
        report.append("3. Click 'Compose New Email'")
        report.append("4. Paste the BCC list in the 'BCC' field")
        report.append("5. Copy and paste the subject line")
        report.append("6. Copy and paste the email body (replace ###SCORE### and ###CONFIDENCE### with individual values)")
        report.append("7. Send to all recipients at once")
        report.append("=" * 90)
        
        return "\n".join(report)
    
    def generate_detailed_candidate_report(self, result):
        """Generate a detailed text report for a single candidate."""
        
        report = []
        report.append("=" * 80)
        report.append(f"DETAILED CANDIDATE ANALYSIS REPORT")
        report.append("=" * 80)
        report.append(f"\nCandidate: {_candidate_name(result['filename'])}")
        report.append(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Generated by: HR Compass System\n")
        
        # Overall Assessment
        report.append("-" * 80)
        report.append("OVERALL ASSESSMENT")
        report.append("-" * 80)
        report.append(f"Final Match Score: {result['final_score']}%")
        report.append(f"Confidence Level: {result['confidence_level']}")
        report.append(f"Recommendation: {self._get_recommendation(result['final_score'])}\n")
        
        # Score Breakdown
        report.append("-" * 80)
        report.append("DETAILED SCORING BREAKDOWN")
        report.append("-" * 80)
        report.append(f"Semantic Matching:     {result['score_breakdown']['semantic_similarity']:>6.1f}% (35% weight)")
        report.append(f"Skills Matching:       {result['score_breakdown']['skills_match']:>6.1f}% (25% weight)")
        report.append(f"Experience Relevance:  {result['score_breakdown']['experience_relevance']:>6.1f}% (15% weight)")
        report.append(f"Keyword Density:       {result['score_breakdown']['keyword_density']:>6.1f}% (15% weight)")
        report.append(f"Culture Fit:           {result['score_breakdown']['culture_fit']:>6.1f}% (5% weight)")
        report.append(f"Seniority Alignment:   {result['score_breakdown']['seniority_alignment']:>6.1f}% (5% weight)\n")
        
        # Seniority Analysis
        report.append("-" * 80)
        report.append("SENIORITY & EXPERIENCE ANALYSIS")
        report.append("-" * 80)
        report.append(f"Candidate Level:       {result['cv_seniority'].upper()}")
        report.append(f"Position Level:        {result['job_seniority'].upper()}")
        alignment = "✓ PERFECT MATCH" if result['cv_seniority'] == result['job_seniority'] else "⚠ MISMATCH"
        report.append(f"Alignment Status:      {alignment}\n")
        
        # Skills Analysis
        report.append("-" * 80)
        report.append(f"SKILLS ANALYSIS ({len(result['matched_skills'])} matched / {len(result['missing_skills'])} missing)")
        report.append("-" * 80)
        
        if result['matched_skills']:
            report.append("\n✓ MATCHED SKILLS:")
            for skill in result['matched_skills']:
                proficiency = result['skill_proficiency'].get(skill, 'Missing Information')
                report.append(f"  • {skill.title():<30} [{proficiency}]")
        
        if result['missing_skills']:
            report.append("\n✗ MISSING SKILLS:")
            for skill in result['missing_skills']:
                report.append(f"  • {skill.title()}")
        
        report.append("")
        
        # Recommendations
        if result['recommendations']:
            report.append("-" * 80)
            report.append(f"LEARNING RECOMMENDATIONS ({len(result['recommendations'])} identified)")
            report.append("-" * 80)
            
            for idx, rec in enumerate(result.get('recommendations', []), 1):
                priority_label = "HIGH" if rec.get('priority') == 'high' else "MEDIUM"
                skill_name = rec.get('skill', 'Unknown').upper()
                effort = rec.get('effort', 'N/A')
                time_est = rec.get('time', 'N/A')
                impact = rec.get('impact', 'Technical Growth').title()
                
                report.append(f"\n{idx}. {skill_name} [{priority_label} PRIORITY]")
                report.append(f"   Suggestion: {rec.get('suggestion', 'N/A')}")
                report.append(f"   Effort Level: {effort}/4")
                report.append(f"   Estimated Time: {time_est}")
                report.append(f"   Development Impact: {impact}")
        
        # Bias Analysis
        if result['bias_warnings']:
            report.append("\n" + "-" * 80)
            report.append("BIAS AWARENESS ALERTS")
            report.append("-" * 80)
            for warning_text, warning_type in result['bias_warnings']:
                report.append(f"⚠ {warning_text} ({warning_type.upper()})")
            report.append("\n⚖ RECOMMENDATION: Evaluate candidate based on qualifications and merit only.")
        else:
            report.append("\n" + "-" * 80)
            report.append("BIAS ANALYSIS")
            report.append("-" * 80)
            report.append("✓ No significant bias indicators detected in analysis.")
        
        # Final Recommendation
        report.append("\n" + "-" * 80)
        report.append("FINAL RECOMMENDATION")
        report.append("-" * 80)
        
        if result['final_score'] >= 85:
            report.append("★★★★★ EXCELLENT MATCH - STRONGLY RECOMMENDED FOR INTERVIEW")
            report.append("\nThis candidate demonstrates exceptional alignment with position requirements.")
        elif result['final_score'] >= 70:
            report.append("★★★★☆ STRONG MATCH - RECOMMENDED FOR INTERVIEW")
            report.append("\nThis candidate shows good alignment with most requirements.")
        elif result['final_score'] >= 60:
            report.append("★★★☆☆ MODERATE MATCH - CONSIDER FOR INTERVIEW")
            report.append("\nThis candidate has potential but has some skill/experience gaps.")
        elif result['final_score'] >= 50:
            report.append("★★☆☆☆ WEAK MATCH - CONSIDER FOR DEVELOPMENT")
            report.append("\nThis candidate would require significant training/development.")
        else:
            report.append("★☆☆☆☆ POOR MATCH - NOT RECOMMENDED")
            report.append("\nThis candidate does not meet core position requirements.")
        
        report.append("\n" + "=" * 80)
        
        return "\n".join(report)
    
    def _get_recommendation(self, score):
        """Get recommendation text based on score."""
        if score >= 85:
            return "STRONG INTERVIEW - TOP PRIORITY"
        elif score >= 70:
            return "INTERVIEW - HIGH POTENTIAL"
        elif score >= 60:
            return "MODERATE - CONSIDER"
        elif score >= 50:
            return "WEAK - LOW PRIORITY"
        else:
            return "NOT RECOMMENDED"
    
    def generate_longlist_shortlist_report(self, results, longlist_count, shortlist_count):
        """Generate a summary report for longlist and shortlist."""
        
        report = []
        report.append("=" * 80)
        report.append("CANDIDATE SELECTION REPORT")
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("=" * 80)
        
        # Sort by score
        sorted_results = sorted(results, key=lambda x: x['final_score'], reverse=True)
        
        # Longlist
        report.append(f"\n📋 LONGLIST ({min(longlist_count, len(sorted_results))}/{len(sorted_results)} candidates)")
        report.append("-" * 80)
        
        longlist = sorted_results[:longlist_count]
        for idx, result in enumerate(longlist, 1):
            report.append(f"{idx}. {_candidate_name(result['filename']):<40} Score: {result['final_score']:>5.1f}% ({result['confidence_level']})")
        
        # Shortlist
        if shortlist_count > 0:
            report.append(f"\n🎯 SHORTLIST ({min(shortlist_count, len(sorted_results))}/{len(sorted_results)}) candidates)")
            report.append("-" * 80)
            
            shortlist = sorted_results[:shortlist_count]
            for idx, result in enumerate(shortlist, 1):
                skills = len(result['matched_skills'])
                missing = len(result['missing_skills'])
                report.append(f"{idx}. {_candidate_name(result['filename']):<30} Score: {result['final_score']:>5.1f}% | Skills: {skills} matched, {missing} missing")
        
        report.append("\n" + "=" * 80)
        
        return "\n".join(report)
