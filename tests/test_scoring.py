"""
Unit tests for Candidate Ranker and Scoring Engine.
"""

import unittest
from src.scoring import ScoringEngine
from src.candidate_ranker import CandidateRanker


class TestScoringAndRanking(unittest.TestCase):

    def setUp(self):
        self.scoring = ScoringEngine(semantic_weight=0.6, skill_weight=0.3, exp_weight=0.1)

    def test_composite_score(self):
        job_text = "Senior AI Engineer (5+ years experience required)"
        sem_score = 80.0
        skill_comp = {"skill_match_score": 100.0}
        cand_exp = 6.0

        res = self.scoring.compute_match(job_text, sem_score, skill_comp, cand_exp)

        # 0.6*80 + 0.3*100 + 0.1*100 = 48 + 30 + 10 = 88.0
        self.assertEqual(res["overall_match_score"], 88.0)
        self.assertEqual(res["status"], "Strong Match")

    def test_candidate_ranker_pipeline(self):
        job_text = "Looking for Python and ML Engineer with PyTorch experience."

        resumes = [
            {
                "filename": "cand1.txt",
                "content": "Alex Rivera. 6+ years experience in Python, PyTorch, ML, Docker, SQL, NLP."
            },
            {
                "filename": "cand2.txt",
                "content": "Michael Scott. 4 years experience in React, JavaScript, HTML, CSS, Node.js."
            }
        ]

        ranker = CandidateRanker()
        out = ranker.process_candidates(job_text, resumes)

        candidates = out["candidates"]
        self.assertEqual(len(candidates), 2)
        self.assertEqual(candidates[0]["filename"], "cand1.txt")
        self.assertEqual(candidates[0]["rank"], 1)
        self.assertGreater(candidates[0]["overall_match_score"], candidates[1]["overall_match_score"])


if __name__ == "__main__":
    unittest.main()
