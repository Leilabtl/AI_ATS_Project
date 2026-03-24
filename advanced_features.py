"""
Advanced ATS Features: Interview Questions, Diversity Metrics, Skills Analytics, Predictions
"""
import json
from collections import Counter
import re
from datetime import datetime
import csv
from io import StringIO

class AdvancedATS:
    """Advanced ATS features for enterprise-grade functionality."""
    
    def __init__(self):
        self.interview_question_bank = {
            'python': [
                "Tell us about your most complex Python project and the challenges you faced.",
                "Explain decorator patterns and how you've used them.",
                "How do you optimize Python code for performance?",
                "Describe your experience with async/await and concurrency.",
                "What testing frameworks do you prefer and why?"
            ],
            'java': [
                "Explain the SOLID principles and give examples from your work.",
                "How do you handle memory management in Java?",
                "Describe your experience with Spring Boot microservices.",
                "What design patterns have you implemented?",
                "How do you approach exception handling?"
            ],
            'data_analysis': [
                "Walk us through your largest data analysis project.",
                "How do you handle missing data and outliers?",
                "What visualization tools do you prefer?",
                "Describe your SQL optimization experience.",
                "How do you validate statistical findings?"
            ],
            'machine_learning': [
                "Describe a model you built from data collection to deployment.",
                "How do you prevent overfitting in your models?",
                "What's your experience with feature engineering?",
                "How do you evaluate model performance?",
                "Tell us about a model failure and how you fixed it."
            ],
            'aws': [
                "Design a scalable architecture on AWS for a given scenario.",
                "How do you approach AWS cost optimization?",
                "Describe your experience with containerization.",
                "How do you ensure security in AWS deployments?",
                "What monitoring and logging tools do you use?"
            ],
            'communication': [
                "Describe a time you had to explain complex technical concepts to non-technical stakeholders.",
                "Tell us about a project where cross-team collaboration was critical.",
                "How do you handle constructive criticism?",
                "Describe your experience mentoring junior team members.",
                "How do you approach code review feedback?"
            ]
        }
    
    def generate_interview_questions(self, result, num_questions=5):
        """Generate tailored interview questions based on candidate profile and gaps."""
        
        questions = []
        strategy = {
            'matched_skills': [],
            'missing_skills': [],
            'general': []
        }
        
        # Add questions for matched skills
        for skill in result['matched_skills'][:2]:
            skill_lower = skill.lower()
            # Find matching question bank
            for category, q_list in self.interview_question_bank.items():
                if category in skill_lower or skill_lower in category:
                    strategy['matched_skills'].extend(q_list[:2])
                    break
        
        # Add questions for missing skills (to assess learning potential)
        for skill in result['missing_skills'][:2]:
            questions.append(f"Tell us about your interest in learning {skill.title()}. How would you approach it?")
            questions.append(f"Have you worked with similar technologies to {skill.title()}? Describe your experience.")
        
        # Add soft skills and general questions
        strategy['general'] = self.interview_question_bank['communication']
        
        # Combine all questions
        all_questions = (
            strategy['matched_skills'][:3] + 
            questions[:2] + 
            strategy['general'][:2]
        )
        
        return all_questions[:num_questions]
    
    def detect_duplicate_applications(self, results, similarity_threshold=80):
        """Identify duplicate or similar applications."""
        
        duplicates = []
        checked = set()
        
        for i, result1 in enumerate(results):
            if i in checked:
                continue
            
            for j, result2 in enumerate(results):
                if j <= i or j in checked:
                    continue
                
                # Simple similarity check based on matched skills overlap
                skills1 = set(result1['matched_skills'])
                skills2 = set(result2['matched_skills'])
                
                if len(skills1) > 0 and len(skills2) > 0:
                    overlap = len(skills1.intersection(skills2)) / len(skills1.union(skills2))
                    
                    # Check score similarity
                    score_diff = abs(result1['final_score'] - result2['final_score'])
                    
                    if overlap > (similarity_threshold / 100) and score_diff < 5:
                        duplicates.append({
                            'candidate1': result1['filename'],
                            'candidate2': result2['filename'],
                            'similarity_score': round(overlap * 100, 1),
                            'score_diff': round(score_diff, 1),
                            'shared_skills': list(skills1.intersection(skills2))
                        })
                        checked.add(j)
        
        return duplicates
    
    def calculate_diversity_metrics(self, results):
        """Calculate diversity and inclusion metrics."""
        
        total = len(results)
        high_scorers = len([r for r in results if r['final_score'] >= 70])
        mid_scorers = len([r for r in results if 50 <= r['final_score'] < 70])
        low_scorers = len([r for r in results if r['final_score'] < 50])
        
        # Seniority distribution
        seniority_dist = Counter([r['cv_seniority'] for r in results])
        
        # Skills diversity
        all_skills = []
        for r in results:
            all_skills.extend(r['matched_skills'])
        skill_diversity = len(set(all_skills))
        avg_skills_per_candidate = len(all_skills) / total if total > 0 else 0
        
        metrics = {
            'total_candidates': total,
            'acceptance_rate': {
                'high_scorers': round((high_scorers / total * 100), 1) if total > 0 else 0,
                'mid_scorers': round((mid_scorers / total * 100), 1) if total > 0 else 0,
                'low_scorers': round((low_scorers / total * 100), 1) if total > 0 else 0,
            },
            'seniority_distribution': dict(seniority_dist),
            'skill_diversity': {
                'unique_skills': skill_diversity,
                'avg_skills_per_candidate': round(avg_skills_per_candidate, 2),
                'most_common_skills': [skill for skill, _ in Counter(all_skills).most_common(5)]
            },
            'recommendations': self._generate_diversity_recommendations(seniority_dist, total)
        }
        
        return metrics
    
    def _generate_diversity_recommendations(self, seniority_dist, total):
        """Generate diversity recommendations."""
        
        recommendations = []
        
        if seniority_dist.get('junior', 0) / total > 0.7 if total > 0 else False:
            recommendations.append("Consider broadening the search to include mid-level candidates for team balance.")
        
        if seniority_dist.get('senior', 0) / total > 0.7 if total > 0 else False:
            recommendations.append("Consider including junior/mid-level candidates to build a diverse team.")
        
        if len(seniority_dist) == 1:
            recommendations.append("All candidates have the same seniority level. Consider recruiting at different levels.")
        
        if not recommendations:
            recommendations.append("Good diversity in candidate seniority levels detected.")
        
        return recommendations
    
    def generate_skills_analytics(self, results):
        """Generate comprehensive skills analytics."""
        
        all_matched = []
        all_missing = []
        proficiency_data = {}
        
        for result in results:
            all_matched.extend(result['matched_skills'])
            all_missing.extend(result['missing_skills'])
            for skill, prof in result['skill_proficiency'].items():
                if skill not in proficiency_data:
                    proficiency_data[skill] = []
                proficiency_data[skill].append(prof)
        
        matched_counter = Counter(all_matched)
        missing_counter = Counter(all_missing)
        
        analytics = {
            'top_matched_skills': [
                {'skill': skill, 'count': count, 'percentage': round(count / len(results) * 100, 1)}
                for skill, count in matched_counter.most_common(10)
            ],
            'top_missing_skills': [
                {'skill': skill, 'count': count, 'percentage': round(count / len(results) * 100, 1)}
                for skill, count in missing_counter.most_common(5)
            ],
            'skill_proficiency_distribution': {
                skill: Counter(profs)
                for skill, profs in proficiency_data.items()
            }
        }
        
        return analytics
    
    def calculate_predictive_success_score(self, result, historical_data=None):
        """Calculate predictive success score based on patterns."""
        
        # Factors that predict success
        base_score = result['final_score']
        
        # Bonus for well-rounded candidates (multiple skill areas)
        skill_diversity_bonus = min(len(result['matched_skills']) * 2, 10)
        
        # Penalty for critical missing skills
        critical_missing_penalty = len(result['missing_skills']) * 1.5
        
        # Bonus for high confidence
        confidence_map = {
            'Very High': 5,
            'High': 3,
            'Moderate': 0,
            'Low': -2,
            'Very Low': -5
        }
        confidence_bonus = confidence_map.get(result['confidence_level'], 0)
        
        # Experience alignment bonus
        exp_bonus = 5 if result['cv_seniority'] == result['job_seniority'] else -3
        
        predictive_score = base_score + skill_diversity_bonus - critical_missing_penalty + confidence_bonus + exp_bonus
        predictive_score = max(0, min(100, predictive_score))  # Clamp between 0-100
        
        success_probability = {
            'predictive_score': round(predictive_score, 1),
            'confidence_interval': {
                'low': round(max(0, predictive_score - 15), 1),
                'high': round(min(100, predictive_score + 15), 1)
            },
            'success_likelihood': self._get_success_likelihood(predictive_score),
            'key_factors': {
                'skill_diversity_bonus': skill_diversity_bonus,
                'confidence_boost': confidence_bonus,
                'experience_alignment': 'Perfect match' if result['cv_seniority'] == result['job_seniority'] else 'Mismatch',
                'missing_skills_risk': len(result['missing_skills'])
            }
        }
        
        return success_probability
    
    def _get_success_likelihood(self, score):
        """Classify success likelihood."""
        if score >= 85:
            return "🟢 Very High (85%+ chance of success)"
        elif score >= 70:
            return "🟡 High (70-85% chance)"
        elif score >= 60:
            return "🟠 Moderate (60-70% chance)"
        elif score >= 50:
            return "🔴 Low (50-60% chance)"
        else:
            return "⛔ Very Low (<50% chance)"
    
    def generate_personalized_feedback(self, result):
        """Generate personalized feedback for candidates."""
        
        feedback = {
            'strengths': [],
            'areas_for_improvement': [],
            'learning_path': []
        }
        
        # Strengths
        if result['final_score'] >= 80:
            feedback['strengths'].append("Exceptional match for the position with strong alignment across most criteria.")
        
        if len(result['matched_skills']) >= 5:
            feedback['strengths'].append(f"Well-rounded technical skillset with {len(result['matched_skills'])} relevant expertise areas.")
        
        if result['cv_seniority'] == result['job_seniority']:
            feedback['strengths'].append(f"Perfect experience level alignment - {result['cv_seniority'].title()} professional.")
        
        # Areas for improvement
        if len(result['missing_skills']) > 0:
            top_missing = result['missing_skills'][:2]
            feedback['areas_for_improvement'].append(
                f"Key skills to develop: {', '.join([s.title() for s in top_missing])}"
            )
        
        if result['final_score'] < 75 and result['confidence_level'] in ['Low', 'Very Low']:
            feedback['areas_for_improvement'].append(
                "Consider focusing on core job requirements and gaining practical experience in critical areas."
            )
        
        # Learning path
        for rec in result['recommendations'][:3]:
            feedback['learning_path'].append({
                'skill': rec['skill'].title(),
                'suggestion': rec['suggestion'],
                'estimated_time': rec['time'],
                'effort_level': f"{rec['effort']}/4"
            })
        
        return feedback
    
    def export_integration_format(self, results, format_type='json'):
        """Export results in formats compatible with other HR systems."""
        
        if format_type == 'json':
            export_data = {
                'export_timestamp': str(datetime.now()),
                'total_candidates': len(results),
                'candidates': []
            }
            
            for result in results:
                export_data['candidates'].append({
                    'name': result['filename'],
                    'score': result['final_score'],
                    'confidence': result['confidence_level'],
                    'skills': result['matched_skills'],
                    'missing_skills': result['missing_skills'],
                    'seniority': result['cv_seniority'],
                    'recommendation': 'Interview' if result['final_score'] >= 70 else 'Consider' if result['final_score'] >= 50 else 'Reject'
                })
            
            return json.dumps(export_data, indent=2)
        
        elif format_type == 'csv':
            output = StringIO()
            writer = csv.DictWriter(output, fieldnames=[
                'Candidate', 'Score', 'Confidence', 'Matched_Skills_Count', 
                'Missing_Skills_Count', 'Seniority', 'Recommendation'
            ])
            writer.writeheader()
            
            for result in results:
                writer.writerow({
                    'Candidate': result['filename'],
                    'Score': result['final_score'],
                    'Confidence': result['confidence_level'],
                    'Matched_Skills_Count': len(result['matched_skills']),
                    'Missing_Skills_Count': len(result['missing_skills']),
                    'Seniority': result['cv_seniority'],
                    'Recommendation': 'Interview' if result['final_score'] >= 70 else 'Consider' if result['final_score'] >= 50 else 'Reject'
                })
            
            return output.getvalue()
