from parser import extract_text_from_pdf, extract_email_from_pdf
from preprocessing import clean_text
from embedding import SemanticMatcher
from skills import extract_skills
import re

class EnhancedMatcher:
    """Enhanced ATS matcher with explainability and bias detection."""
    
    def __init__(self):
        self.matcher = SemanticMatcher()
        self.male_names = ['john', 'michael', 'david', 'james', 'robert', 'ali', 'ahmed', 'carlos', 'sergei', 'wei']
        self.female_names = ['sara', 'maria', 'emma', 'jessica', 'lisa', 'fatima', 'aisha', 'chen', 'priya', 'yuki']
    
    def calculate_final_score(self, analysis):
        """
        Calculate final weighted score with 6 factors:
        Formula: 0.35 * semantic + 0.25 * skills_match + 0.15 * experience + 
                 0.15 * keyword_density + 0.05 * culture_fit + 0.05 * seniority
        """
        scores = {
            'semantic': analysis['semantic_similarity'],
            'skills': analysis['skills_match'],
            'experience': analysis['experience_relevance'],
            'keyword': analysis['keyword_density'],
            'culture': analysis['culture_fit'],
            'seniority': analysis['seniority_alignment'],
        }
        
        final_score = (
            (0.35 * scores['semantic']) +
            (0.25 * scores['skills']) +
            (0.15 * scores['experience']) +
            (0.15 * scores['keyword']) +
            (0.05 * scores['culture']) +
            (0.05 * scores['seniority'])
        )
        
        return round(min(final_score, 100), 1), scores
    
    def get_confidence_level(self, final_score):
        """Get confidence level based on score."""
        if final_score >= 85:
            return 'Very High', '🟢'
        elif final_score >= 70:
            return 'High', '🟢'
        elif final_score >= 60:
            return 'Moderate', '🟡'
        elif final_score >= 50:
            return 'Low', '🟡'
        else:
            return 'Very Low', '🔴'
    
    def detect_bias(self, cv_text, cv_name=""):
        """Detect potential bias indicators."""
        bias_indicators = []
        cv_lower = cv_text.lower()
        
        if cv_name:
            cv_name_lower = cv_name.lower()
            if any(name in cv_name_lower for name in self.male_names):
                bias_indicators.append(("Male-coded name", "name"))
            elif any(name in cv_name_lower for name in self.female_names):
                bias_indicators.append(("Female-coded name", "name"))
        
        age_keywords = ['graduated', 'since', 'year', 'veteran', 'senior', 'born', 'age']
        if sum(1 for kw in age_keywords if kw in cv_lower) > 3:
            bias_indicators.append(("Age-related keywords", "age"))
        
        gender_pronouns = ['he ', 'she ', 'her ', 'his ', 'him ']
        if any(pronoun in ' ' + cv_lower for pronoun in gender_pronouns):
            bias_indicators.append(("Gender pronouns detected", "gender"))
        
        return bias_indicators
    
    def get_skill_gap_recommendations(self, missing_skills, matched_skills, analysis):
        """Generate learning recommendations based on skill gaps."""
        recommendations = []
        
        skill_learning_paths = {
            'docker': ('Learn containerization basics', 2, '2-3 weeks', 'high'),
            'kubernetes': ('After Docker, learn orchestration', 3, '4 weeks', 'high'),
            'aws': ('Cloud fundamentals course', 2, '3-4 weeks', 'high'),
            'azure': ('Microsoft cloud platform', 2, '3-4 weeks', 'medium'),
            'gcp': ('Google cloud platform', 2, '3-4 weeks', 'medium'),
            'ci/cd': ('DevOps fundamentals', 2, '2-3 weeks', 'high'),
            'machine learning': ('ML basics course', 4, '8-12 weeks', 'medium'),
            'sql': ('Database fundamentals', 1, '2-3 weeks', 'high'),
            'javascript': ('Frontend basics', 3, '4-6 weeks', 'medium'),
            'api': ('API design course', 1, '2-3 weeks', 'medium'),
            'testing': ('Test automation framework', 2, '3-4 weeks', 'medium'),
            'git': ('Version control mastery', 1, '1-2 weeks', 'low'),
        }
        
        for skill in missing_skills:
            if skill in skill_learning_paths:
                name, effort, time, priority = skill_learning_paths[skill]
                recommendations.append({
                    'skill': skill,
                    'suggestion': name,
                    'effort': effort,  # 1-4: Low to Very High
                    'time': time,
                    'priority': priority,
                    'impact': 'high' if skill in matched_skills else 'medium'
                })
        
        return sorted(recommendations, key=lambda x: x['priority'] == 'high', reverse=True)
    
    def estimate_skill_proficiency(self, cv_text, skill_name):
        """Estimate candidate's proficiency level in a skill."""
        skill_indicators = {
            'expert': ['architect', 'lead', 'expert', 'advanced', 'mastered', 'principal'],
            'advanced': ['senior', 'specialized', 'deep', 'complex systems'],
            'intermediate': ['professional', 'solid', 'strong', 'competent'],
            'junior': ['learning', 'basic', 'junior', 'entry'],
        }
        
        cv_lower = cv_text.lower()
        skill_lower = skill_name.lower()
        
        # Create context around skill mention
        skill_pattern = rf'\b{re.escape(skill_lower)}\b'
        matches = re.finditer(skill_pattern, cv_lower)
        
        proficiency_scores = {'expert': 0, 'advanced': 0, 'intermediate': 0, 'junior': 0}
        
        for match in matches:
            start = max(0, match.start() - 200)
            end = min(len(cv_lower), match.end() + 200)
            context = cv_lower[start:end]
            
            for level, keywords in skill_indicators.items():
                if any(kw in context for kw in keywords):
                    proficiency_scores[level] += 1
        
        # Determine based on counts
        if proficiency_scores['expert'] > 0:
            return 'Expert'
        elif proficiency_scores['advanced'] > proficiency_scores['intermediate']:
            return 'Advanced'
        elif proficiency_scores['intermediate'] > 0:
            return 'Intermediate'
        elif proficiency_scores['junior'] > 0:
            return 'Junior'
        else:
            # Fallback to general seniority if specified
            return self.matcher.extract_seniority_level(cv_text).title() if self.matcher.extract_seniority_level(cv_text) != 'unspecified' else 'Not Determined'
    
    def match_cv_to_job(self, cv_path, job_description, cv_name=""):
        """Enhanced matching with detailed analysis."""
        cv_text = extract_text_from_pdf(cv_path)
        cv_text_clean = clean_text(cv_text)
        job_text_clean = clean_text(job_description)
        
        # Extract email from CV
        candidate_email = extract_email_from_pdf(cv_path)
        
        # Get detailed analysis
        analysis = self.matcher.get_detailed_analysis(cv_text_clean, job_description)
        
        # Calculate final score with breakdown
        final_score, score_breakdown = self.calculate_final_score(analysis)
        
        # Get confidence level
        confidence_level, confidence_emoji = self.get_confidence_level(final_score)
        
        # Get skill gap recommendations
        recommendations = self.get_skill_gap_recommendations(
            analysis['missing_skills'],
            analysis['matched_skills'],
            analysis
        )
        
        # Detect potential bias
        bias_warnings = self.detect_bias(cv_text, cv_name)
        
        # Estimate proficiency for matched skills
        skill_proficiency = {}
        for skill in analysis['matched_skills'].keys():
            skill_proficiency[skill] = self.estimate_skill_proficiency(cv_text, skill)
        
        return {
            'final_score': final_score,
            'confidence_level': confidence_level,
            'confidence_emoji': confidence_emoji,
            'score_breakdown': {
                'semantic_similarity': analysis['semantic_similarity'],
                'skills_match': analysis['skills_match'],
                'experience_relevance': analysis['experience_relevance'],
                'keyword_density': analysis['keyword_density'],
                'culture_fit': analysis['culture_fit'],
                'seniority_alignment': analysis['seniority_alignment'],
            },
            'weighted_breakdown': score_breakdown,
            'matched_skills': list(analysis['matched_skills'].keys()),
            'missing_skills': list(analysis['missing_skills'].keys()),
            'skill_proficiency': skill_proficiency,
            'recommendations': recommendations,
            'bias_warnings': bias_warnings,
            'all_cv_skills': analysis['cv_skills'],
            'all_job_skills': analysis['job_skills'],
            'cv_seniority': analysis['cv_seniority'],
            'job_seniority': analysis['job_seniority'],
            'candidate_email': candidate_email,
            'strategic_summary': self.generate_strategic_summary(analysis, final_score),
            'improvement_areas': self.generate_improvement_areas(analysis)
        }

    def generate_strategic_summary(self, analysis, score):
        """Generate a detailed, nuanced summary of the match."""
        matched_str = ', '.join(list(analysis['matched_skills'].keys())[:3])
        missing_str = ', '.join(list(analysis['missing_skills'].keys())[:2])
        
        if score >= 85:
            summary = f"**Exceptional candidate** with {score}% alignment. "
            summary += f"Strong mastery of core skills: {matched_str}. "
            summary += f"Demonstrates {analysis['culture_fit']}% culture alignment and matches the required {analysis['job_seniority']} seniority profile."
            return summary
        elif score >= 70:
            summary = f"**Strong potential candidate** ({score}%). "
            summary += f"Excellent fit in {matched_str}. "
            if missing_str:
                summary += f"Consider discussing {missing_str} during the interview. "
            summary += f"Strong semantic relevance ({analysis['semantic_similarity']}%)."
            return summary
        elif score >= 50:
            summary = f"**Moderate match candidate** ({score}%). "
            summary += f"Has foundational knowledge in {matched_str or 'relevant areas'}. "
            if missing_str:
                summary += f"Significant technical gaps identified in {missing_str}. "
            summary += "May requires more intensive onboarding or mentorship."
            return summary
        else:
            return f"**Low alignment** ({score}%). Significant mismatch in core technical requirements ({analysis['skills_match']}% skill match) and experience profile."

    def generate_improvement_areas(self, analysis):
        """Synthesize specific, actionable areas for candidate improvement."""
        areas = []
        if analysis['missing_skills']:
            skills = list(analysis['missing_skills'].keys())[:3]
            areas.append(f"Critical Technical Gap: Missing key JD requirements: {', '.join(skills)}")
        
        if analysis['seniority_alignment'] < 80:
            areas.append(f"Seniority Imbalance: Candidate ({analysis['cv_seniority']}) vs Requirement ({analysis['job_seniority']})")
            
        if analysis['culture_fit'] < 60:
            areas.append("Soft Skill Alignment: Resume lacks indicators for key collaborative or leadership behaviors mentioned in JD.")
            
        if analysis['experience_relevance'] < 60:
            areas.append("Experience Depth: Industry-specific professional experience markers appear limited for this role level.")
            
        if analysis['semantic_similarity'] < 40:
            areas.append("Contextual Alignment: Low semantic overlap suggests the resume may be too general or focused on a different domain.")
            
        return areas


def match_cv_to_job(cv_path, job_description):
    """Legacy function for compatibility."""
    enhanced = EnhancedMatcher()
    return enhanced.match_cv_to_job(cv_path, job_description)