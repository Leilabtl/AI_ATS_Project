"""
Candidate Pool Management - Store and categorize candidates across multiple job openings
"""
import json
from datetime import datetime
from pathlib import Path
import os

class CandidatePool:
    """Manage candidate pool across multiple jobs with recommendations."""
    
    def __init__(self, pool_file="candidate_pool.json"):
        self.pool_file = pool_file
        self.pool = self._load_pool()
    
    def _load_pool(self):
        """Load existing candidate pool from file."""
        if os.path.exists(self.pool_file):
            try:
                with open(self.pool_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {'candidates': [], 'jobs': []}
        return {'candidates': [], 'jobs': []}
    
    def _save_pool(self):
        """Save candidate pool to file."""
        with open(self.pool_file, 'w', encoding='utf-8') as f:
            json.dump(self.pool, f, indent=2, ensure_ascii=False)
    
    def add_job(self, job_title, job_description, min_score=50):
        """Add a new job opening to the pool."""
        job_id = f"job_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        job_entry = {
            'job_id': job_id,
            'title': job_title,
            'description': job_description,
            'min_score': min_score,
            'created_date': datetime.now().isoformat(),
            'candidate_count': 0
        }
        self.pool['jobs'].append(job_entry)
        self._save_pool()
        return job_id
    
    def add_candidate(self, result, job_id, job_title):
        """Add a candidate result to the pool for a specific job."""
        candidate_entry = {
            'candidate_id': f"cand_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{result.get('filename', 'unknown')[:20]}",
            'filename': result.get('filename', 'Unknown'),
            'email': result.get('candidate_email', 'Not provided'),
            'final_score': result.get('final_score', 0),
            'job_id': job_id,
            'job_title': job_title,
            'cv_seniority': result.get('cv_seniority', 'unspecified'),
            'matched_skills': result.get('matched_skills', []),
            'missing_skills': result.get('missing_skills', []),
            'confidence_level': result.get('confidence_level', 'Unknown'),
            'added_date': datetime.now().isoformat(),
            'skill_proficiency': result.get('skill_proficiency', {}),
            'score_breakdown': result.get('score_breakdown', {}),
        }
        self.pool['candidates'].append(candidate_entry)
        self._save_pool()
        return candidate_entry
    
    def get_job_recommendations(self, result, all_jobs):
        """Get job recommendations for a candidate based on their skills and seniority."""
        recommendations = []
        candidate_skills = set(result.get('matched_skills', []))
        candidate_score = result.get('final_score', 0)
        
        for job in all_jobs:
            # Simple scoring: check skill match with job
            job_keywords = set(job.get('description', '').lower().split())
            skill_match = len(candidate_skills & job_keywords)
            
            # Estimate fit score based on candidate's overall score
            fit_score = min(candidate_score + (skill_match * 5), 100)
            
            if fit_score >= job.get('min_score', 50):
                recommendations.append({
                    'job_title': job.get('title', 'Unknown Job'),
                    'job_id': job.get('job_id'),
                    'fit_score': fit_score,
                    'reason': f"Candidate has {len(candidate_skills)} relevant skills and {result.get('cv_seniority', 'unspecified').title()} level experience"
                })
        
        # Sort by fit score
        recommendations.sort(key=lambda x: x['fit_score'], reverse=True)
        return recommendations[:3]  # Top 3 recommendations
    
    def get_candidates_by_job(self, job_id):
        """Get all candidates for a specific job."""
        return [c for c in self.pool['candidates'] if c['job_id'] == job_id]
    
    def get_all_candidates(self):
        """Get all candidates in the pool."""
        return self.pool['candidates']
    
    def get_all_jobs(self):
        """Get all jobs in the pool."""
        return self.pool['jobs']
    
    def search_candidates(self, query, field='filename'):
        """Search candidates by filename or other fields."""
        query_lower = query.lower()
        return [c for c in self.pool['candidates'] if query_lower in str(c.get(field, '')).lower()]
    
    def get_pool_statistics(self):
        """Get statistics about the candidate pool."""
        stats = {
            'total_candidates': len(self.pool['candidates']),
            'total_jobs': len(self.pool['jobs']),
            'average_score': 0,
            'candidates_by_seniority': {},
            'candidates_by_job': {}
        }
        
        if self.pool['candidates']:
            scores = [c['final_score'] for c in self.pool['candidates'] if c.get('final_score')]
            stats['average_score'] = sum(scores) / len(scores) if scores else 0
            
            for candidate in self.pool['candidates']:
                seniority = candidate.get('cv_seniority', 'unspecified')
                if seniority not in stats['candidates_by_seniority']:
                    stats['candidates_by_seniority'][seniority] = 0
                stats['candidates_by_seniority'][seniority] += 1
                
                job_id = candidate.get('job_id', 'unassigned')
                if job_id not in stats['candidates_by_job']:
                    stats['candidates_by_job'][job_id] = 0
                stats['candidates_by_job'][job_id] += 1
        
        return stats
    
    def export_candidates_csv(self):
        """Export all candidates as CSV format."""
        import csv
        from io import StringIO
        
        output = StringIO()
        candidates = self.pool['candidates']
        
        if not candidates:
            return ""
        
        fieldnames = ['Candidate', 'Email', 'Job Title', 'Score', 'Seniority', 'Matched Skills', 'Confidence', 'Added Date']
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        
        for cand in candidates:
            writer.writerow({
                'Candidate': cand.get('filename', 'Unknown'),
                'Email': cand.get('email', 'N/A'),
                'Job Title': cand.get('job_title', 'Unknown'),
                'Score': f"{cand.get('final_score', 0)}%",
                'Seniority': cand.get('cv_seniority', 'unspecified').title(),
                'Matched Skills': ', '.join(cand.get('matched_skills', [])),
                'Confidence': cand.get('confidence_level', 'Unknown'),
                'Added Date': cand.get('added_date', 'Unknown')[:10],
            })
        
        return output.getvalue()
    
    def clear_pool(self):
        """Clear all candidates and jobs from the pool."""
        self.pool = {'candidates': [], 'jobs': []}
        self._save_pool()
