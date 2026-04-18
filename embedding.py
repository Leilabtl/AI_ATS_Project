"""
Enhanced embedding and scoring system for ATS.
Provides semantic similarity with sophisticated analytics.
"""
from collections import Counter
import math
import re

class SemanticMatcher:
    """Enhanced semantic matching with explainability."""
    
    def __init__(self):
        self.skill_keywords = {
            'python': ['python', 'py', 'django', 'flask', 'fastapi', 'numpy', 'pandas', 'scikit-learn'],
            'java': ['java', 'spring', 'maven', 'hibernate'],
            'sql': ['sql', 'mysql', 'postgresql', 'tsql', 'oracle', 'mongodb', 'redis'],
            'javascript': ['javascript', 'js', 'react', 'nodejs', 'typescript', 'ts', 'vue', 'angular'],
            'docker': ['docker', 'kubernetes', 'container', 'k8s', 'helm'],
            'aws': ['aws', 'amazon', 'ec2', 's3', 'lambda', 'rds', 'dynamodb'],
            'azure': ['azure', 'microsoft cloud'],
            'gcp': ['gcp', 'google cloud'],
            'machine learning': ['ml', 'machine learning', 'deep learning', 'tensorflow', 'pytorch', 'nlp'],
            'computer vision': ['cv', 'computer vision', 'opencv'],
            'data analysis': ['data analysis', 'excel', 'tableau', 'powerbi', 'statistics'],
            'api design': ['api', 'rest', 'graphql', 'microservice', 'grpc'],
            'ci/cd': ['ci/cd', 'jenkins', 'devops', 'terraform', 'ansible'],
            'git': ['git', 'github', 'gitlab', 'version control'],
            'mobile dev': ['flutter', 'react native', 'swift', 'ios', 'android', 'kotlin'],
            'data engineering': ['spark', 'hadoop', 'kafka', 'airflow', 'etl', 'snowflake'],
            'cybersecurity': ['security', 'cybersecurity', 'encryption', 'pentest', 'firewall'],
            'c++': ['c++', 'cpp'],
            'c#': ['c#', 'csharp', '.net'],
            'golang': ['golang', 'go language'],
            'rust': ['rust', 'rustlang'],
            'php': ['php', 'laravel'],
            'ruby': ['ruby', 'rails'],
            'scala': ['scala'],
            'r language': ['r language', 'r stats'],
            'linux': ['linux', 'bash', 'shell', 'ubuntu'],
            'project management': ['leadership', 'agile', 'scrum', 'project management'],
            'ui/ux': ['ui/ux', 'figma', 'responsive design'],
        }
        
        self.seniority_levels = {
            'junior': ['junior', 'entry', 'newcomer', 'trainee', 'intern', '0-2 years'],
            'mid': ['mid', 'intermediate', '3-5 years', 'professional'],
            'senior': ['senior', 'lead', 'principal', '5-10 years', 'architect', 'expert'],
            'executive': ['director', 'vp', 'cto', 'ceo', '10+ years', 'executive'],
        }
    
    def extract_seniority_level(self, text):
        """Detect candidate seniority level."""
        text_lower = text.lower()
        
        for level, keywords in self.seniority_levels.items():
            if any(keyword in text_lower for keyword in keywords):
                return level
        return 'unspecified'
    
    def extract_skills_with_weight(self, text):
        """Extract skills with confidence scores."""
        text_lower = text.lower()
        skill_scores = {}
        
        for skill, keywords in self.skill_keywords.items():
            score = 0
            for keyword in keywords:
                if keyword in text_lower:
                    # Multi-word phrases get higher weight
                    if keyword.count(' ') > 0 or keyword.count('-') > 0:
                        score += 3
                    else:
                        score += 1
            
            if score > 0:
                skill_scores[skill] = min(score, 5)
        
        # Dynamic extraction for potential skills (capitalized words in text)
        potential_skills = re.findall(r'\b[A-Z][a-zA-Z0-9+#]{2,}(?:\s[A-Z][a-zA-Z0-9+#]{2,})*\b', text)
        for ps in potential_skills:
            ps_lower = ps.lower()
            # Ignore if too short or a common generic word
            if len(ps_lower) > 2 and ps_lower not in skill_scores:
                # Blacklist certain generic terms that often get capitalized
                blacklist = [
                    'the', 'this', 'that', 'with', 'from', 'using', 'work', 'experience',
                    'candidate', 'team', 'company', 'industry', 'years', 'development',
                    'engineer', 'developer', 'management', 'project', 'languages', 'skills'
                ]
                if ps_lower not in blacklist and not ps_lower.isdigit():
                    skill_scores[ps_lower] = 1
        
        # Clean up: If we have specific skills, remove the generic categories
        if any(s in skill_scores for s in ['python', 'java', 'c++', 'c#', 'golang']):
            if 'languages' in skill_scores:
                del skill_scores['languages']
        
        if any(s in skill_scores for s in ['react', 'angular', 'vue', 'django', 'flask']):
            if 'web' in skill_scores:
                del skill_scores['web']
                
        return skill_scores
    
    def compute_similarity(self, cv_text, job_text):
        """Compute similarity using Jaccard index."""
        cv_words = set(re.findall(r'\b\w+\b', cv_text.lower()))
        job_words = set(re.findall(r'\b\w+\b', job_text.lower()))
        
        if not cv_words or not job_words:
            return 0.0
        
        intersection = len(cv_words & job_words)
        union = len(cv_words | job_words)
        
        if union == 0:
            return 0.0
        
        return min(intersection / union, 1.0)
    
    def calculate_keyword_density(self, text, keywords):
        """Calculate how concentrated keywords are in text."""
        if not text:
            return 0.0
        
        text_lower = text.lower()
        total_words = len(text_lower.split())
        
        keyword_hits = sum(text_lower.count(kw) for kw in keywords)
        
        if total_words == 0:
            return 0.0
        
        return min((keyword_hits / total_words) * 100, 100)
    
    def get_detailed_analysis(self, cv_text, job_text):
        """Get detailed analysis with comprehensive breakdown."""
        # Extract skills from both
        cv_skills = self.extract_skills_with_weight(cv_text)
        job_skills = self.extract_skills_with_weight(job_text)
        
        # Seniority detection
        cv_seniority = self.extract_seniority_level(cv_text)
        job_seniority = self.extract_seniority_level(job_text)
        
        # Find matched and missing skills
        matched_skills = {}
        missing_skills = {}
        
        for skill, weight in job_skills.items():
            if skill in cv_skills:
                matched_skills[skill] = cv_skills[skill]
            else:
                missing_skills[skill] = weight
        
        # Calculate skills match percentage
        if job_skills:
            skills_match = len(matched_skills) / len(job_skills) * 100
        else:
            skills_match = 50  # No skills mentioned
        
        # Calculate semantic similarity
        semantic_score = self.compute_similarity(cv_text, job_text) * 100
        
        # Experience relevance
        experience_keywords = ['year', 'experience', 'expert', 'senior', 'lead', 'managed', 'developed', 'architected']
        exp_count = sum(1 for keyword in experience_keywords if keyword in cv_text.lower())
        experience_relevance = min(exp_count * 15, 100)
        
        # Keyword density (how focused is the CV on job requirements)
        job_key_terms = re.findall(r'\b\w+\b', job_text.lower())
        keyword_density = self.calculate_keyword_density(cv_text, job_key_terms)
        
        # Culture fit (soft skills indicators)
        culture_keywords = ['team', 'collaboration', 'communication', 'problem solving', 'passionate', 'driven', 'innovative']
        culture_score = min(sum(1 for kw in culture_keywords if kw in cv_text.lower()) * 12, 100)
        
        # Seniority alignment (0-100 points)
        seniority_match = 100 if cv_seniority == job_seniority else 70 if cv_seniority != 'unspecified' else 50
        
        return {
            'skills_match': round(skills_match, 1),
            'semantic_similarity': round(semantic_score, 1),
            'experience_relevance': round(experience_relevance, 1),
            'keyword_density': round(keyword_density, 1),
            'culture_fit': round(culture_score, 1),
            'seniority_alignment': round(seniority_match, 1),
            'matched_skills': matched_skills,
            'missing_skills': missing_skills,
            'cv_skills': cv_skills,
            'job_skills': job_skills,
            'cv_seniority': cv_seniority,
            'job_seniority': job_seniority,
        }


def compute_similarity(cv_text, job_text):
    """Legacy function for compatibility."""
    matcher = SemanticMatcher()
    return matcher.compute_similarity(cv_text, job_text)