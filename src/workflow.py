"""
Workflow & Governance Engine
Manages candidate evaluation state transitions, recruiter feedback logging,
and human-in-the-loop review overrides.
"""

from typing import List, Dict, Any, Optional
from src.database.db_manager import DatabaseManager

VALID_STATUSES = [
    "Under Review",
    "Shortlisted",
    "Interview Scheduled",
    "Hired",
    "Rejected",
    "Archived"
]


class WorkflowEngine:
    """
    Candidate Evaluation State Machine and Human Decision Manager.
    """

    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        self.db = db_manager or DatabaseManager()

    def update_status(self, eval_id: int, new_status: str, notes: str = "", user_username: str = "admin") -> Dict[str, Any]:
        """
        Updates evaluation status with state transition validation and audit logging.
        """
        if new_status not in VALID_STATUSES:
            raise ValueError(f"Invalid status '{new_status}'. Allowed statuses: {VALID_STATUSES}")

        success = self.db.update_evaluation_status(eval_id, new_status, notes, user_username)
        return {
            "eval_id": eval_id,
            "status": new_status,
            "notes": notes,
            "updated_by": user_username,
            "success": success
        }

    def get_evaluations_by_status(self, status: str) -> List[Dict[str, Any]]:
        """Filters stored candidate evaluations by workflow status."""
        all_evals = self.db.get_all_evaluations()
        return [e for e in all_evals if e.get("status") == status]
