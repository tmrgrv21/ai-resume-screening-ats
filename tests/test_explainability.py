"""
Unit tests for Explainability Engine & Interview Question Generator.
"""

import unittest
from src.explainability import ExplainabilityEngine


class TestExplainability(unittest.TestCase):

    def test_explainability_generation(self):
        cand = {
            "overall_match_score": 88.5,
            "matched_skills": ["Python", "PyTorch", "Docker"],
            "missing_skills": ["Kubernetes"],
            "experience_years": 5.0
        }

        explanation = ExplainabilityEngine.generate_match_explanation(cand)
        self.assertIn("Exceptional candidate match", explanation["headline"])
        self.assertGreater(len(explanation["key_strengths"]), 0)

    def test_interview_question_generator(self):
        cand = {
            "matched_skills": ["Python", "PyTorch"],
            "missing_skills": ["Docker", "AWS"]
        }

        questions = ExplainabilityEngine.generate_interview_questions(cand)
        self.assertGreater(len(questions), 0)
        self.assertTrue(any("Python" in q["question"] or "PyTorch" in q["question"] for q in questions))


if __name__ == "__main__":
    unittest.main()
