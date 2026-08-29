"""
Unit tests for MongoDB Database Manager and Repositories Layer.
"""

import unittest
from src.database.mongo_manager import MongoManager
from src.repositories.user_repository import UserRepository
from src.repositories.candidate_repository import CandidateRepository


class TestMongoPersistence(unittest.TestCase):

    def setUp(self):
        self.mongo = MongoManager(db_name="test_ai_screening")
        self.user_repo = UserRepository(self.mongo)
        self.cand_repo = CandidateRepository(self.mongo)

    def test_mongo_initialization(self):
        self.assertIsNotNone(self.mongo)

    def test_user_creation_and_lookup(self):
        import uuid
        uid = uuid.uuid4().hex[:6]
        username = f"test_engineer_{uid}"
        email = f"test_{uid}@company.com"
        user = self.user_repo.create(username, email, "TestPass123!", role="recruiter")
        self.assertIsNotNone(user)
        self.assertEqual(user["username"], username)

        found = self.user_repo.find_by_username(username)
        self.assertIsNotNone(found)
        self.assertEqual(found["email"], email)

    def test_candidate_evaluation_storage(self):
        cand_data = {
            "candidate_name": "Test Candidate Alpha",
            "email": "alpha@test.com",
            "experience_years": 5.5,
            "overall_match_score": 88.5,
            "semantic_score": 90.0,
            "skill_score": 85.0,
            "exp_score": 90.0,
            "status": "Under Review",
            "matched_skills": ["Python", "Machine Learning"],
            "missing_skills": ["Docker"]
        }
        eval_doc = self.cand_repo.save_candidate_evaluation(cand_data, user_username="test_recruiter")
        self.assertIsNotNone(eval_doc)
        self.assertEqual(eval_doc["candidate_name"], "Test Candidate Alpha")

        evals = self.cand_repo.get_all_evaluations()
        self.assertGreaterEqual(len(evals), 1)


if __name__ == "__main__":
    unittest.main()
