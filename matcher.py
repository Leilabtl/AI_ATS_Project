from parser import extract_text_from_pdf, extract_email_from_pdf
from preprocessing import clean_text
from embedding import SemanticMatcher
from skills import extract_skills
import re

class EnhancedMatcher:
    """Enhanced ATS matcher with explainability and bias detection."""
    
    def __init__(self, matcher):
        self.matcher = matcher
        self.skill_intel = {
            'python': {
                'importance': 'Foundational for modern backend and data systems.',
                'roadmap': 'Focus on Advanced Python (Decorators, Generators), AsyncIO for performance, and Packaging (Poetry/Pipenv). Study Django or FastAPI for rest services.',
                'impact': 'Critical for backend stability and automation.'
            },
            'machine learning': {
                'importance': 'Core for intelligent features and predictive analytics.',
                'roadmap': 'Learn Scikit-Learn pipelines, Deep Learning with PyTorch or TensorFlow, and MLOps principles (model monitoring, versioning with DVC).',
                'impact': 'High value for predictive business logic.'
            },
            'sql': {
                'importance': 'Essential for data persistence and complex querying.',
                'roadmap': 'Master Window Functions, Query Optimization (EXPLAIN ANALYZE), and Database Schema Design (Normalization vs Denormalization).',
                'impact': 'Vital for data integrity and accurate reporting.'
            },
            'aws': {
                'importance': 'Primary infrastructure for scalable deployments.',
                'roadmap': 'Get certified as AWS Solutions Architect. Focus on Lambda (Serverless), S3, RDS, and IAM security policies.',
                'impact': 'Essential for cloud scalability and security.'
            },
            'docker': {
                'importance': 'Standard for environment consistency and CI/CD.',
                'roadmap': 'Learn Multi-stage builds, Docker Compose for local dev, and Container Security (scanning for vulnerabilities).',
                'impact': 'Critical for deployment reliability.'
            },
            'kubernetes': {
                'importance': 'Orchestration for large-scale microservices.',
                'roadmap': 'Study Pod lifecycle, Services, Ingress Controllers, and Helm Charts for deployment automation.',
                'impact': 'High impact on system orchestration.'
            },
            'ci/cd': {
                'importance': 'Enables fast and reliable software delivery.',
                'roadmap': 'Learn to build pipelines in GitHub Actions or GitLab CI. Focus on automated testing, linting, and blue-green deployments.',
                'impact': 'Vital for engineering velocity.'
            },
            'javascript': {
                'importance': 'Critical for building interactive user interfaces.',
                'roadmap': 'Master ES6+ features, React (Hooks/Context), and State Management (Redux/Zustand).',
                'impact': 'Primary for modern web user experience.'
            },
            'c++': {
                'importance': 'Required for high-performance systems and low-level optimization.',
                'roadmap': 'Study Modern C++ (C++17/20), Memory Management (Smart Pointers), and STL containers optimization.',
                'impact': 'Critical for performance-sensitive tasks.'
            },
            'golang': {
                'importance': 'Preferred for high-concurrency microservices.',
                'roadmap': 'Learn Goroutines and Channels, Interface-based design, and standard library net/http for APIs.',
                'impact': 'Essential for high-scale microservices.'
            },
            'rust': {
                'importance': 'Ensures memory safety and performance.',
                'roadmap': 'Master Ownership and Borrowing rules, Error handling (Result/Option), and the Cargo ecosystem.',
                'impact': 'High value for secure, fast systems.'
            },
            'data engineering': {
                'importance': 'Vital for building reliable data pipelines.',
                'roadmap': 'Study Apache Spark for big data, Airflow for orchestration, and Snowflake for cloud warehousing.',
                'impact': 'Fundamental for data-driven decisions.'
            }
        }
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
        """Generate detailed, actionable learning roadmap for gaps."""
        recommendations = []
        
        # Determine priority based on JD importance
        for skill in missing_skills:
            if len(skill) < 2: continue # Extra safety against single-letter garbage
            
            intel = self.skill_intel.get(skill.lower(), {
                'importance': f'Specific technical requirement for {skill}.',
                'roadmap': f'Acquire hands-on experience by building a small project using {skill}. Focus on core concepts and integration patterns.',
                'impact': 'Technical alignment'
            })
            
            # Simple heuristic for effort: 4 for complex, 2 for tools, 3 for languages
            effort = 3
            if skill.lower() in ['python', 'java', 'c++', 'c#', 'rust', 'machine learning', 'pytorch', 'tensorflow']:
                effort = 4
            elif skill.lower() in ['git', 'docker', 'jira', 'confluence', 'vba']:
                effort = 2
            
            recommendations.append({
                'skill': skill,
                'priority': 'high',  # Since it's a missing skill from JD
                'suggestion': f"{intel.get('importance', 'Core proficiency')} {intel.get('roadmap', 'Focus on project-based learning.')}",
                'impact': intel.get('impact', 'Career alignment'),
                'effort': effort,
                'time': '2-4 weeks' if effort > 2 else '1 week'
            })
        
        return sorted(recommendations, key=lambda x: x['effort'], reverse=True)
    
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
            'career_advice': self.generate_career_advice(analysis, final_score),
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
            summary += f"The candidate shows mastery in {matched_str}, which are the cornerstone requirements for this position. "
            summary += f"They perfectly match the {analysis['job_seniority']} seniority profile and demonstrate high cultural alignment ({analysis['culture_fit']}%)."
            return summary
        elif score >= 70:
            summary = f"**Strong potential candidate** ({score}%). "
            summary += f"Key areas of strength include {matched_str}, aligning well with our primary technical stack. "
            if missing_str:
                summary += f"While technical gaps exist in {missing_str}, their strong foundation suggests they can bridge these quickly. "
            summary += f"Reflects solid industry relevance ({analysis['experience_relevance']}%)."
            return summary
        elif score >= 50:
            summary = f"**Moderate match candidate** ({score}%). "
            summary += f"Foundational experience identified in {matched_str or 'relevant technical areas'}, but significant alignment is missing in core requirements. "
            if missing_str:
                summary += f"Critical missing requirements: {missing_str}. These are essential for day-one performance. "
            summary += "Consider for a more junior role or an internship if the budget allows for mentoring."
            return summary
        else:
             summary = f"**Low alignment** ({score}%). Technical match is only {analysis['skills_match']}%. "
             summary += f"Mismatch found in both technical stack ({missing_str or 'core skills'}) and seniority requirements. "
             summary += "Candidate may be better suited for a different career path or a fundamental training program."
             return summary

    def generate_improvement_areas(self, analysis):
        """Synthesize specific, actionable areas for candidate improvement."""
        areas = []
        if analysis['missing_skills']:
            skills = list(analysis['missing_skills'].keys())[:3]
            mastery_text = "**Technical Mastery Required:** "
            for s in skills:
                intel = self.skill_intel.get(s.lower(), {})
                roadmap = intel.get('roadmap', f"Study fundamentals of {s.title()}.")
                mastery_text += f"\n- **{s.title()}**: {roadmap}"
            areas.append(mastery_text)
        
        if analysis['seniority_alignment'] < 80:
            areas.append(f"**Experience Gap:** The role requires {analysis['job_seniority']} level independent decision-making, while the resume indicates a {analysis['cv_seniority']} profile. Focus on demonstrating leadership in past projects.")
            
        if analysis['culture_fit'] < 60:
            areas.append("**Soft Skills & Values:** Missing indicators for collaborative workflows or specific values (e.g., 'Innovation', 'Mentorship') highlighted in the JD. Consider highlighting team-based achievements.")
            
        if analysis['experience_relevance'] < 60:
            areas.append("**Domain Knowledge:** Professional history lacks depth in this specific industry sector compared to standard benchmarks. Consider adding certifications or projects related to this domain.")
            
        return areas

    def generate_career_advice(self, analysis, score):
        """Provide specific career guidance and role suggestions."""
        if score < 60:
            if 'python' in analysis['matched_skills'] or 'sql' in analysis['matched_skills']:
                return "Suggested Alternative Role: Data Analyst or Junior Software Support Engineer, where core logic can be applied without the specialized ML/Cloud overhead."
            else:
                return "Suggested Alternative Role: Technical Support or QA Specialist, to build foundational industry experience before reapplying for developer positions."
        return "Recommendation: Proceed with interview. Focus on evaluating their speed of learning and adaptability to our specific stack."


def match_cv_to_job(cv_path, job_description):
    """Legacy function for compatibility."""
    from embedding import SemanticMatcher
    enhanced = EnhancedMatcher(SemanticMatcher())
    return enhanced.match_cv_to_job(cv_path, job_description)