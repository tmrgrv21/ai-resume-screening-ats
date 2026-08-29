"""
Unit tests for Workflow Engine & Human Overrides.
"""

import unittest
import os
from src.database.db_manager import DatabaseManager
from src.workflow import WorkflowEngine


class TestWorkflow(unittest.TestCase):

    def setUp(self):
        import uuid
        self.test_db_path = os.path.join(os.path.dirname(__file__), f"test_wf_db_{uuid.uuid4().hex[:8]}.db")
        self.db = DatabaseManager(db_path=self.test_db_path)
        self.wf = WorkflowEngine(self.db)

        cand_data = {
            "candidate_name": "Jane Doe",
            "email": "jane@example.com",
            "phone": "555-0101",
            "experience_years": 5.0,
            "overall_match_score": 88.0,
            "semantic_score": 85.0,
            "skill_score": 90.0,
            "exp_score": 95.0,
            "status": "Under Review"
        }
        self.cand_id = self.db.save_candidate_evaluation(cand_data)

    def tearDown(self):
        try:
            if hasattr(self, 'db') and self.db:
                del self.db
            if os.path.exists(self.test_db_path):
                os.remove(self.test_db_path)
        except Exception:
            pass

    def test_status_update(self):
        eval_id = str(self.cand_id)

        res = self.wf.update_status(eval_id, "Shortlisted", notes="Strong candidate performance", user_username="recruiter")
        self.assertTrue(res["success"])

        updated_evals = self.db.get_all_evaluations()
        jane_updated = next(e for e in updated_evals if str(e.get("_id", e.get("eval_id"))) == eval_id)
        self.assertEqual(jane_updated["status"], "Shortlisted")
        self.assertEqual(jane_updated["reviewer_notes"], "Strong candidate performance")

    def test_invalid_status_rejection(self):
        with self.assertRaises(ValueError):
            self.wf.update_status(1, "InvalidStatusName")


if __name__ == "__main__":
    unittest.main()
