"""
Enhanced embedding and scoring system for ATS.
Provides semantic similarity with sophisticated analytics.

Similarity strategy (in priority order):
  1. TF-IDF cosine similarity via scikit-learn — accounts for term importance
     weighting so rare, domain-specific keywords (e.g. "Kubernetes", "GDPR")
     contribute more than common words ("the", "and", "work").
  2. Jaccard index fallback — used only when scikit-learn is unavailable.
"""
import logging
import re

logger = logging.getLogger(__name__)

# TF-IDF cosine similarity — preferred over Jaccard because it weights
# rare, domain-specific terms higher than common words.
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity as _cosine_sim
    _SKLEARN_AVAILABLE = True
    logger.debug("scikit-learn available: using TF-IDF cosine similarity")
except ImportError:
    _SKLEARN_AVAILABLE = False
    logger.warning("scikit-learn not found; falling back to Jaccard similarity")

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
            # ── HR / Business domain ──────────────────────────────────────────
            'hris': ['hris', 'workday', 'adp', 'bamboohr', 'successfactors',
                     'oracle hcm', 'sap hr', 'people soft', 'rippling', 'gusto'],
            'hr analytics': ['hr analytics', 'people analytics', 'workforce analytics',
                             'talent analytics', 'people data'],
            'talent management': ['talent acquisition', 'recruitment', 'talent management',
                                  'onboarding', 'headhunting', 'sourcing'],
            'compensation': ['compensation', 'payroll', 'benefits', 'total rewards',
                             'salary benchmarking', 'pay equity', 'remuneration'],
            'compliance': ['compliance', 'labor law', 'employment law', 'regulatory',
                           'gdpr', 'eeo', 'fmla', 'osha'],
            'finance': ['financial analysis', 'budgeting', 'forecasting', 'accounting',
                        'p&l', 'cash flow', 'gaap', 'ifrs', 'balance sheet'],
            'erp': ['erp', 'sap', 'oracle erp', 'netsuite', 'dynamics 365', 'odoo'],
            'crm': ['crm', 'salesforce', 'hubspot', 'zoho', 'dynamics crm', 'pipedrive'],
            'business intelligence': ['business intelligence', 'looker', 'qlik',
                                      'metabase', 'domo', 'microstrategy'],
            # ── Embedded / Hardware ───────────────────────────────────────────
            'embedded systems': ['embedded', 'firmware', 'rtos', 'freertos', 'zephyr',
                                 'microcontroller', 'stm32', 'arm cortex', 'esp32',
                                 'bare metal', 'hal', 'bsp', 'jtag'],
            'embedded protocols': ['uart', 'spi', 'i2c', 'can bus', 'modbus',
                                   'ble firmware', 'lorawan', 'zigbee firmware'],
            # ── Project / Design / Marketing tools ────────────────────────────
            'project tools': ['jira', 'asana', 'smartsheet', 'ms project', 'trello',
                              'basecamp', 'monday.com', 'confluence', 'notion'],
            'ux research': ['wireframing', 'wireframe', 'prototyping', 'user research',
                            'usability testing', 'design system', 'interaction design',
                            'ux research', 'information architecture', 'wcag'],
            'marketing tools': ['google ads', 'meta ads', 'facebook ads', 'semrush',
                                'ahrefs', 'hubspot', 'mailchimp', 'ga4', 'google analytics',
                                'screaming frog', 'hotjar'],
        }
        
        self.seniority_levels = {
            'junior': ['junior', 'entry', 'newcomer', 'trainee', 'intern', '0-2 years'],
            'mid': ['mid', 'intermediate', '3-5 years'],
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
                # Word-boundary match — prevents 'ts' hitting "results",
                # 'excel' hitting "excellent", 'ml' hitting "html", etc.
                pattern = r'\b' + re.escape(keyword) + r'\b'
                if re.search(pattern, text_lower):
                    score += 3 if (' ' in keyword or '-' in keyword) else 1

            if score > 0:
                skill_scores[skill] = min(score, 5)
        
        # Dynamic extraction for potential skills (capitalized words in text)
        potential_skills = re.findall(r'\b[A-Z][a-zA-Z0-9+#]{2,}(?:\s[A-Z][a-zA-Z0-9+#]{2,})*\b', text)
        for ps in potential_skills:
            ps_lower = ps.lower()
            # Ignore if too short or a common generic word
            if len(ps_lower) > 2 and ps_lower not in skill_scores:
                # Blacklist generic terms, section headers and verbs that appear capitalised in JDs
                blacklist = [
                    'the', 'this', 'that', 'with', 'from', 'using', 'work', 'experience',
                    'candidate', 'team', 'company', 'industry', 'years', 'development',
                    'engineer', 'developer', 'management', 'project', 'languages', 'skills',
                    # JD section headers often capitalised
                    'responsibilities', 'qualifications', 'requirements', 'education',
                    'collaboration', 'maintenance', 'monitoring', 'deployment', 'frameworks',
                    'algorithms', 'platforms', 'infrastructure', 'overview', 'summary',
                    'bachelor', 'master', 'degree', 'science', 'mathematics', 'related',
                    'essential', 'advanced', 'solid', 'deep', 'core', 'primary', 'functional',
                    # Common JD action verbs that get capitalised at sentence/bullet start
                    'develop', 'deploy', 'train', 'build', 'monitor', 'maintain', 'implement',
                    'design', 'create', 'manage', 'support', 'improve', 'analyse', 'analyze',
                    'evaluate', 'move', 'track', 'partner', 'construct', 'optimize', 'refine',
                    'ensure', 'deliver', 'define', 'drive', 'lead', 'establish', 'provide',
                    'identify', 'collaborate', 'coordinate', 'communicate', 'report',
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
        """Compute semantic similarity between CV and job description.

        Uses TF-IDF cosine similarity when scikit-learn is available.
        TF-IDF weights rare, domain-specific terms (e.g. "Kubernetes",
        "GDPR") higher than common words, so the score more accurately
        reflects technical alignment between CV and JD.

        Falls back to Jaccard index if scikit-learn is not installed.
        """
        if not cv_text or not job_text:
            return 0.0

        if _SKLEARN_AVAILABLE:
            return self._tfidf_cosine(cv_text, job_text)
        return self._jaccard(cv_text, job_text)

    def _tfidf_cosine(self, cv_text, job_text):
        """TF-IDF vectorisation + cosine similarity (0.0 – 1.0)."""
        try:
            vectorizer = TfidfVectorizer(
                analyzer='word',
                token_pattern=r'\b\w+\b',
                ngram_range=(1, 2),   # unigrams + bigrams capture phrases
                min_df=1,
                sublinear_tf=True,    # log-scale TF dampens repetition
            )
            tfidf = vectorizer.fit_transform([cv_text.lower(), job_text.lower()])
            score = float(_cosine_sim(tfidf[0:1], tfidf[1:2])[0][0])
            return min(max(score, 0.0), 1.0)
        except Exception as exc:
            logger.warning("TF-IDF similarity failed (%s); falling back to Jaccard", exc)
            return self._jaccard(cv_text, job_text)

    def _jaccard(self, cv_text, job_text):
        """Jaccard similarity — fallback when scikit-learn is unavailable."""
        cv_words  = set(re.findall(r'\b\w+\b', cv_text.lower()))
        job_words = set(re.findall(r'\b\w+\b', job_text.lower()))
        if not cv_words or not job_words:
            return 0.0
        union = len(cv_words | job_words)
        return min(len(cv_words & job_words) / union, 1.0) if union else 0.0
    
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
        logger.debug("get_detailed_analysis: cv_len=%d jd_len=%d", len(cv_text), len(job_text))
        cv_skills  = self.extract_skills_with_weight(cv_text)
        job_skills = self.extract_skills_with_weight(job_text)

        cv_seniority  = self.extract_seniority_level(cv_text)
        job_seniority = self.extract_seniority_level(job_text)

        # Restrict matching to curated skills only — dynamic extractions are unreliable
        # and cause false positives when the same generic word appears in both texts.
        curated_job_skills = {s: w for s, w in job_skills.items() if s in self.skill_keywords}

        matched_skills: dict = {}
        missing_skills: dict = {}
        for skill, weight in curated_job_skills.items():
            if skill in cv_skills:
                matched_skills[skill] = cv_skills[skill]
            else:
                missing_skills[skill] = weight

        # Skills match: % of JD's curated requirements found in CV
        if curated_job_skills:
            skills_match = len(matched_skills) / len(curated_job_skills) * 100
        else:
            skills_match = 50  # No recognisable tech skills in JD
        
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
        
        logger.debug(
            "analysis complete: skills_match=%.1f semantic=%.1f matched=%d missing=%d",
            skills_match, semantic_score, len(matched_skills), len(missing_skills),
        )
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
    """Module-level helper — delegates to SemanticMatcher.compute_similarity."""
    return SemanticMatcher().compute_similarity(cv_text, job_text)