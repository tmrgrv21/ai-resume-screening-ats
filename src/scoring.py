"""
Scoring Module
Calculates transparent weighted composite match scores for candidate screening.
"""

from typing import Dict, Any, Tuple


class ScoringEngine:
    """
    Computes weighted multi-factor match scores combining:
    1. Semantic Similarity Score (NLP Embeddings)
    2. Skill Match Score (Keyword & Taxonomy Coverage)
    3. Experience Relevance Score (Years & Seniority Alignment)
    """

    def __init__(self, semantic_weight: float = 0.60, skill_weight: float = 0.30, exp_weight: float = 0.10):
        total_w = semantic_weight + skill_weight + exp_weight
        if total_w <= 0:
            total_w = 1.0

        # Normalize weights to ensure they sum to 1.0
        self.w_semantic = semantic_weight / total_w
        self.w_skill = skill_weight / total_w
        self.w_exp = exp_weight / total_w

    def calculate_experience_score(self, job_text: str, candidate_exp_years: float) -> float:
        """
        Calculates experience relevance score based on candidate experience vs job requirement heuristics.
        """
        # Heuristic target experience years from job text
        import re
        req_years = 0.0
        matches = re.findall(r'(\d{1,2})\+?\s*(?:-\s*\d{1,2}\s*)?years?\s*(?:of\s*)?experience', job_text, flags=re.IGNORECASE)
        if matches:
            try:
                req_years = max([float(m) for m in matches])
            except ValueError:
                req_years = 3.0
        else:
            # Check for seniority keywords
            lower_job = job_text.lower()
            if any(k in lower_job for k in ['senior', 'lead', 'principal', 'staff', 'head']):
                req_years = 5.0
            elif any(k in lower_job for k in ['junior', 'entry', 'intern', 'associate']):
                req_years = 1.0
            else:
                req_years = 3.0  # Mid-level default

        if candidate_exp_years >= req_years:
            return 100.0
        elif candidate_exp_years > 0 and req_years > 0:
            return round((candidate_exp_years / req_years) * 100.0, 2)
        else:
            return 50.0  # Neutral baseline if experience text is unparseable

    def compute_match(
        self,
        job_text: str,
        semantic_score: float,
        skill_comparison: Dict[str, Any],
        candidate_exp_years: float
    ) -> Dict[str, Any]:
        """
        Computes overall weighted match score and detailed breakdown.
        """
        skill_score = float(skill_comparison.get("skill_match_score", 0.0))
        exp_score = self.calculate_experience_score(job_text, candidate_exp_years)

        overall_score = (
            (self.w_semantic * semantic_score) +
            (self.w_skill * skill_score) +
            (self.w_exp * exp_score)
        )

        overall_score = round(min(100.0, max(0.0, overall_score)), 1)

        # Categorize status tag
        if overall_score >= 85.0:
            status = "Strong Match"
            badge_color = "#10B981"  # Emerald Green
        elif overall_score >= 70.0:
            status = "Good Match"
            badge_color = "#3B82F6"  # Royal Blue
        elif overall_score >= 50.0:
            status = "Potential Match"
            badge_color = "#F59E0B"  # Amber
        else:
            status = "Low Match"
            badge_color = "#EF4444"  # Coral Red

        return {
            "overall_match_score": overall_score,
            "semantic_score": round(semantic_score, 1),
            "skill_score": round(skill_score, 1),
            "exp_score": round(exp_score, 1),
            "status": status,
            "badge_color": badge_color,
            "weights_used": {
                "semantic": round(self.w_semantic * 100, 1),
                "skill": round(self.w_skill * 100, 1),
                "experience": round(self.w_exp * 100, 1)
            }
        }
