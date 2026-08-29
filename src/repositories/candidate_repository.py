"""
Candidate & Evaluation Repositories Module
Encapsulates MongoDB document persistence for candidates and evaluations collections.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime


class CandidateRepository:
    """
    MongoDB Candidate Repository.
    """

    def __init__(self, db_manager: Any):
        self.db = db_manager

    def save_candidate_evaluation(self, candidate_data: Dict[str, Any], requisition_id: Optional[str] = None, user_username: str = "system") -> Dict[str, Any]:
        """
        Saves candidate document and evaluation entry into MongoDB collections.
        """
        cand_col = self.db.get_collection("candidates")
        eval_col = self.db.get_collection("evaluations")

        cand_doc = {
            "candidate_name": candidate_data.get("candidate_name", "Unknown"),
            "email": candidate_data.get("email", "Not detected"),
            "phone": candidate_data.get("phone", "Not detected"),
            "experience_years": candidate_data.get("experience_years", 0.0),
            "skills": candidate_data.get("candidate_skills", candidate_data.get("skills", [])),
            "raw_text": candidate_data.get("raw_text", ""),
            "filename": candidate_data.get("filename", "resume.txt"),
            "created_at": datetime.now()
        }
        cand_res = cand_col.insert_one(cand_doc)
        cand_id = str(cand_res.inserted_id)

        eval_doc = {
            "candidate_id": cand_id,
            "candidate_name": cand_doc["candidate_name"],
            "email": cand_doc["email"],
            "phone": cand_doc["phone"],
            "experience_years": cand_doc["experience_years"],
            "filename": cand_doc["filename"],
            "raw_text": cand_doc["raw_text"],
            "requisition_id": str(requisition_id) if requisition_id else None,
            "overall_score": candidate_data.get("overall_match_score", 0.0),
            "semantic_score": candidate_data.get("semantic_score", 0.0),
            "skill_score": candidate_data.get("skill_score", 0.0),
            "exp_score": candidate_data.get("exp_score", 0.0),
            "status": candidate_data.get("status", "Under Review"),
            "matched_skills": candidate_data.get("matched_skills", []),
            "missing_skills": candidate_data.get("missing_skills", []),
            "candidate_skills": candidate_data.get("candidate_skills", candidate_data.get("skills", [])),
            "reviewer_notes": "",
            "evaluated_at": datetime.now()
        }
        eval_res = eval_col.insert_one(eval_doc)
        eval_doc["_id"] = str(eval_res.inserted_id)
        eval_doc["eval_id"] = eval_doc["_id"]

        self.db.log_audit(user_username, "EVALUATE_CANDIDATE", "Evaluation", eval_doc["_id"], f"Evaluated candidate {cand_doc['candidate_name']} - Score: {eval_doc['overall_score']}%")
        return eval_doc

    def get_all_evaluations(self) -> List[Dict[str, Any]]:
        """Retrieves all candidate evaluations from MongoDB, sorted by overall_score descending."""
        eval_col = self.db.get_collection("evaluations")
        evals = list(eval_col.find())
        for e in evals:
            e["eval_id"] = str(e.get("_id", e.get("eval_id", "")))
            if "matched_skills_json" in e and not e.get("matched_skills"):
                import json
                e["matched_skills"] = json.loads(e["matched_skills_json"])
            if "missing_skills_json" in e and not e.get("missing_skills"):
                import json
                e["missing_skills"] = json.loads(e["missing_skills_json"])
        evals.sort(key=lambda x: x.get("overall_score", 0.0), reverse=True)
        return evals

    def update_evaluation_status(self, eval_id: str, new_status: str, notes: str = "", user_username: str = "admin") -> bool:
        """Updates evaluation workflow status and reviewer notes."""
        eval_col = self.db.get_collection("evaluations")
        eval_col.update_one(
            {"_id": eval_id},
            {"$set": {"status": new_status, "reviewer_notes": notes, "updated_at": datetime.now()}}
        )
        self.db.log_audit(user_username, "UPDATE_STATUS", "Evaluation", str(eval_id), f"Updated candidate status to '{new_status}' with notes: '{notes}'")
        return True
