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
            'java': ['java', 'spring', 'maven', 'junit', 'gradle', 'hibernate'],
            'sql': ['sql', 'mysql', 'postgresql', 'tsql', 'oracle', 'database', 'db', 'nosql', 'mongodb'],
            'javascript': ['javascript', 'js', 'react', 'nodejs', 'typescript', 'ts', 'vue', 'angular'],
            'docker': ['docker', 'kubernetes', 'container', 'k8s', 'podman', 'compose'],
            'aws': ['aws', 'amazon', 'ec2', 's3', 'lambda', 'rds', 'sqs'],
            'cloud': ['cloud', 'azure', 'gcp', 'google cloud', 'heroku', 'cloudflare'],
            'machine learning': ['ml', 'machine learning', 'deep learning', 'neural', 'tensorflow', 'scikit', 'pytorch', 'ai', 'artificial intelligence'],
            'data analysis': ['data analysis', 'analytics', 'excel', 'tableau', 'powerbi', 'looker', 'data viz'],
            'api': ['api', 'rest', 'graphql', 'microservice', 'soap', 'grpc'],
            'ci/cd': ['ci/cd', 'jenkins', 'gitlab', 'github actions', 'devops', 'circleci', 'travis'],
            'frontend': ['html', 'css', 'frontend', 'ui/ux', 'responsive', 'sass', 'bootstrap'],
            'backend': ['backend', 'server', 'database', 'api', 'microservice', 'rest'],
            'testing': ['testing', 'pytest', 'jest', 'unittest', 'tdd', 'qa', 'selenium'],
            'git': ['git', 'github', 'gitlab', 'bitbucket', 'version control', 'scm'],
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