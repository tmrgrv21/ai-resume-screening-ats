"""
Unit tests for Candidate Comparison Engine.
"""

import unittest
from src.comparison import ComparisonEngine


class TestComparison(unittest.TestCase):

    def test_comparison_matrix_builder(self):
        cands = [
            {
                "candidate_name": "Alex Rivera",
                "overall_match_score": 92.0,
                "semantic_score": 90.0,
                "skill_score": 95.0,
                "exp_score": 90.0,
                "experience_years": 6.0,
                "status": "Shortlisted",
                "matched_skills": ["Python", "PyTorch", "Docker"],
                "missing_skills": ["Kubernetes"]
            },
            {
                "candidate_name": "Sarah Chen",
                "overall_match_score": 75.0,
                "semantic_score": 70.0,
                "skill_score": 80.0,
                "exp_score": 75.0,
                "experience_years": 3.0,
                "status": "Under Review",
                "matched_skills": ["Python", "SQL"],
                "missing_skills": ["Docker", "Kubernetes"]
            }
        ]

        matrix = ComparisonEngine.build_comparison_matrix(cands)
        metrics_df = matrix["metrics_df"]
        skill_df = matrix["skill_matrix_df"]

        self.assertFalse(metrics_df.empty)
        self.assertFalse(skill_df.empty)
        self.assertIn("Alex Rivera", metrics_df.columns)
        self.assertIn("Sarah Chen", metrics_df.columns)


if __name__ == "__main__":
    unittest.main()
