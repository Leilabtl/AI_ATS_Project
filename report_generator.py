"""
Generate comprehensive ATS reports with PDF, CSV, and Email support.
"""
import pandas as pd
from datetime import datetime
import json
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from io import BytesIO

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
                result['filename'][:20],
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
        """Generate detailed PDF report for a single candidate."""
        
        pdf_buffer = BytesIO()
        doc = SimpleDocTemplate(pdf_buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
        
        story = []
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#667eea'),
            spaceAfter=6,
            alignment=0
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=12,
            textColor=colors.HexColor('#764ba2'),
            spaceAfter=8,
            spaceBefore=8
        )
        
        # Title with candidate name
        story.append(Paragraph(f"CANDIDATE DETAILED REPORT: {result['filename']}", title_style))
        story.append(Paragraph(f"Generated: {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
        story.append(Spacer(1, 0.15*inch))
        
        # Overall Score Section
        story.append(Paragraph("OVERALL ASSESSMENT", heading_style))
        score_data = [
            ['Final Score', f"{result['final_score']}%"],
            ['Confidence Level', result['confidence_level']],
            ['Recommendation', self._get_recommendation(result['final_score'])],
        ]
        score_table = Table(score_data, colWidths=[2*inch, 2.5*inch])
        score_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e8eaf6')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ]))
        story.append(score_table)
        story.append(Spacer(1, 0.15*inch))
        
        # Strategic Assessment
        story.append(Paragraph("STRATEGIC ASSESSMENT", heading_style))
        story.append(Paragraph(f"<b>Summary:</b> {result.get('strategic_summary', 'N/A')}", styles['Normal']))
        story.append(Spacer(1, 0.1*inch))
        
        if result.get('improvement_areas'):
            story.append(Paragraph("AREAS FOR IMPROVEMENT", heading_style))
            for area in result['improvement_areas']:
                story.append(Paragraph(f"• {area}", styles['Normal']))
            story.append(Spacer(1, 0.1*inch))
            
        story.append(Spacer(1, 0.15*inch))

        # Score Breakdown
        story.append(Paragraph("SCORING BREAKDOWN", heading_style))
        breakdown_data = [
            ['Factor', 'Score', 'Weight'],
            ['Semantic Matching', f"{result['score_breakdown']['semantic_similarity']:.1f}%", '35%'],
            ['Skills Matching', f"{result['score_breakdown']['skills_match']:.1f}%", '25%'],
            ['Experience Relevance', f"{result['score_breakdown']['experience_relevance']:.1f}%", '15%'],
            ['Keyword Density', f"{result['score_breakdown']['keyword_density']:.1f}%", '15%'],
            ['Culture Fit', f"{result['score_breakdown']['culture_fit']:.1f}%", '5%'],
            ['Seniority Alignment', f"{result['score_breakdown']['seniority_alignment']:.1f}%", '5%'],
        ]
        breakdown_table = Table(breakdown_data, colWidths=[2*inch, 1.5*inch, 1*inch])
        breakdown_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
        ]))
        story.append(breakdown_table)
        story.append(Spacer(1, 0.15*inch))
        
        # Skills Analysis
        story.append(Paragraph("SKILLS ANALYSIS", heading_style))
        skills_text = f"Matched: {len(result['matched_skills'])} skills | Missing: {len(result['missing_skills'])} skills\n"
        if result['matched_skills']:
            matched_list = ", ".join([s.title() for s in result['matched_skills'][:10]])
            skills_text += f"✓ {matched_list}"
            if len(result['matched_skills']) > 10:
                skills_text += f" +{len(result['matched_skills']) - 10} more"
        story.append(Paragraph(skills_text.replace("\n", "<br/>"), styles['Normal']))
        story.append(Spacer(1, 0.1*inch))
        
        # Seniority
        story.append(Paragraph("SENIORITY & EXPERIENCE", heading_style))
        seniority_text = f"Candidate Level: <b>{result['cv_seniority'].upper()}</b><br/>Required Level: <b>{result['job_seniority'].upper()}</b>"
        story.append(Paragraph(seniority_text, styles['Normal']))
        story.append(Spacer(1, 0.15*inch))
        
        # Recommendations
        if result['recommendations']:
            story.append(Paragraph("LEARNING RECOMMENDATIONS", heading_style))
            for idx, rec in enumerate(result.get('recommendations', [])[:5], 1):
                effort = rec.get('effort', 2)
                time_est = rec.get('time', '1-2 weeks')
                skill_name = rec.get('skill', 'Technology').upper()
                suggestion = rec.get('suggestion', 'Review technical documentation.')
                impact = rec.get('impact', 'Career Growth')
                
                rec_text = f"<b>{idx}. {skill_name}</b><br/>Suggestion: {suggestion}<br/>Impact: {impact}<br/>Effort: {effort}/4 | Time: {time_est}"
                story.append(Paragraph(rec_text, styles['Normal']))
                story.append(Spacer(1, 0.08*inch))
        
        # Build PDF
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
    
    def generate_comprehensive_csv(self, results, job_description, longlist_count=None, shortlist_count=None):
        """Generate comprehensive CSV with all candidate details."""
        
        data = []
        
        for idx, result in enumerate(results, 1):
            candidate_data = {
                # Basic Info
                'Rank': idx,
                'Candidate_Name': result['filename'],
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
                'name': result['filename'],
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
        bcc_list = ", ".join([c['email'] for c in group_data])
        
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
        report.append(f"\nCandidate: {result['filename']}")
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
            report.append(f"{idx}. {result['filename']:<40} Score: {result['final_score']:>5.1f}% ({result['confidence_level']})")
        
        # Shortlist
        if shortlist_count > 0:
            report.append(f"\n🎯 SHORTLIST ({min(shortlist_count, len(sorted_results))}/{len(sorted_results)}) candidates)")
            report.append("-" * 80)
            
            shortlist = sorted_results[:shortlist_count]
            for idx, result in enumerate(shortlist, 1):
                skills = len(result['matched_skills'])
                missing = len(result['missing_skills'])
                report.append(f"{idx}. {result['filename']:<30} Score: {result['final_score']:>5.1f}% | Skills: {skills} matched, {missing} missing")
        
        report.append("\n" + "=" * 80)
        
        return "\n".join(report)
