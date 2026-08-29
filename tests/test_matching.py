"""
Unit tests for Skill Extraction and Semantic Matching modules.
"""

import unittest
from src.skill_extractor import SkillExtractor
from src.semantic_matcher import SemanticMatcher
from src.text_preprocessor import mask_demographics, clean_text


class TestMatching(unittest.TestCase):

    def setUp(self):
        self.skill_extractor = SkillExtractor()
        self.semantic_matcher = SemanticMatcher()

    def test_skill_extraction(self):
        text = "We need a Python developer experienced with PyTorch, Docker, SQL, and AWS."
        skills = self.skill_extractor.extract_skills(text)

        self.assertIn("Python", skills)
        self.assertIn("PyTorch", skills)
        self.assertIn("Docker", skills)
        self.assertIn("SQL", skills)
        self.assertIn("AWS", skills)

    def test_skill_comparison(self):
        job_text = "Required skills: Python, Docker, Kubernetes, PyTorch"
        resume_text = "Candidate skills: Python, Docker, React, HTML"

        comp = self.skill_extractor.compare_skills(job_text, resume_text)

        self.assertIn("Python", comp["matched_skills"])
        self.assertIn("Docker", comp["matched_skills"])
        self.assertIn("Kubernetes", comp["missing_skills"])
        self.assertIn("PyTorch", comp["missing_skills"])
        self.assertEqual(comp["skill_match_score"], 50.0)

    def test_demographic_masking(self):
        raw = "Candidate is a Male, Single, Date of Birth: 01/01/1995."
        masked = mask_demographics(raw)

        self.assertNotIn("Male", masked)
        self.assertNotIn("Single", masked)
        self.assertIn("[GENDER MASKED]", masked)

    def test_semantic_similarity(self):
        job = "Seeking Senior Machine Learning Engineer for PyTorch NLP models."
        resume = "Experienced ML Lead building NLP and PyTorch transformer models."

        sim_score, method = self.semantic_matcher.compute_similarity(job, resume)

        self.assertGreater(sim_score, 0.0)
        self.assertTrue("SentenceTransformer" in method or "TF-IDF" in method)


if __name__ == "__main__":
    unittest.main()
