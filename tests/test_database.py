"""
Unit tests for Database Manager & MongoDB Data Persistence.
"""

import unittest
from src.database.db_manager import DatabaseManager


class TestDatabase(unittest.TestCase):

    def setUp(self):
        self.db = DatabaseManager()

    def test_seed_users(self):
        admin = self.db.get_user("admin")
        self.assertIsNotNone(admin)
        self.assertEqual(admin["role"].lower(), "admin")

    def test_user_authentication(self):
        auth_user = self.db.verify_user_credentials("admin", "admin123")
        self.assertIsNotNone(auth_user)
        self.assertIsNone(self.db.verify_user_credentials("admin", "wrongpass"))

    def test_create_and_get_requisition(self):
        req_id = self.db.create_requisition("AI Engineer", "Job description text...")
        self.assertTrue(bool(req_id))

        reqs = self.db.get_requisitions()
        self.assertGreaterEqual(len(reqs), 1)

    def test_save_and_retrieve_evaluation(self):
        cand_data = {
            "candidate_name": "Test Candidate DB",
            "email": "testdb@example.com",
            "phone": "555-0192",
            "experience_years": 4.0,
            "candidate_skills": ["Python", "PyTorch"],
            "raw_text": "Sample text",
            "filename": "test.txt",
            "overall_match_score": 85.0,
            "semantic_score": 80.0,
            "skill_score": 90.0,
            "exp_score": 85.0,
            "status": "Under Review",
            "matched_skills": ["Python"],
            "missing_skills": ["PyTorch"]
        }

        cand_id = self.db.save_candidate_evaluation(cand_data)
        self.assertTrue(bool(cand_id))

        evals = self.db.get_all_evaluations()
        self.assertGreaterEqual(len(evals), 1)


if __name__ == "__main__":
    unittest.main()
