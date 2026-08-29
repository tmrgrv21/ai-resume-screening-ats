"""
Database Manager Module (MongoDB Migration Wrapper)
Provides complete backward compatibility layer delegating all database persistence
and retrieval calls to MongoDB collections (src.database.mongo_manager.MongoManager).
"""

from typing import Dict, Any, List, Optional
from src.database.mongo_manager import MongoManager
from src.security.password import hash_password, verify_password


class DatabaseManager:
    """
    Database Manager delegating all persistence operations to MongoDB collections.
    """

    def __init__(self, db_path: Optional[str] = None):
        self.mongo = MongoManager()
        self.db_path = "MongoDB:ai_resume_screening"

    def get_collection(self, collection_name: str):
        return self.mongo.get_collection(collection_name)

    # --------------------------------------------------
    # USERS OPERATIONS
    # --------------------------------------------------
    def get_user(self, username: str) -> Optional[Dict[str, Any]]:
        users_col = self.get_collection("users")
        return users_col.find_one({"username": username})

    def create_user(self, username: str, email: str, password: str, role: str = "recruiter") -> bool:
        users_col = self.get_collection("users")
        if users_col.find_one({"username": username}):
            return False
        pwd_hash = hash_password(password)
        users_col.insert_one({
            "username": username,
            "email": email.strip().lower(),
            "password_hash": pwd_hash,
            "role": role.lower(),
            "status": "active",
            "email_verified": True
        })
        self.log_audit(username, "USER_REGISTER", "User", username, f"Registered new account ({role})")
        return True

    def verify_user_credentials(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        user = self.get_user(username)
        if user and verify_password(password, user["password_hash"]):
            return user
        return None

    # --------------------------------------------------
    # REQUISITION OPERATIONS
    # --------------------------------------------------
    def create_requisition(self, title: str, description: str, department: str = "Engineering", location: str = "Remote", req_exp: float = 3.0, created_by: str = "admin") -> str:
        reqs_col = self.get_collection("job_requisitions")
        doc = {
            "title": title,
            "department": department,
            "location": location,
            "description": description,
            "required_experience": req_exp,
            "status": "Active",
            "created_by": created_by
        }
        res = reqs_col.insert_one(doc)
        req_id = str(res.inserted_id)
        self.log_audit(created_by, "CREATE_REQUISITION", "JobRequisition", req_id, f"Created job req: {title}")
        return req_id

    def get_requisitions(self) -> List[Dict[str, Any]]:
        reqs_col = self.get_collection("job_requisitions")
        return list(reqs_col.find())

    # --------------------------------------------------
    # CANDIDATES & EVALUATIONS OPERATIONS
    # --------------------------------------------------
    def save_candidate_evaluation(self, candidate_data: Dict[str, Any], requisition_id: Optional[str] = None, user_username: str = "system") -> str:
        cand_col = self.get_collection("candidates")
        eval_col = self.get_collection("evaluations")

        cand_doc = {
            "candidate_name": candidate_data.get("candidate_name", "Unknown"),
            "email": candidate_data.get("email", "Not detected"),
            "phone": candidate_data.get("phone", "Not detected"),
            "experience_years": candidate_data.get("experience_years", 0.0),
            "skills": candidate_data.get("candidate_skills", []),
            "raw_text": candidate_data.get("raw_text", ""),
            "filename": candidate_data.get("filename", "resume.txt")
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
            "candidate_skills": candidate_data.get("candidate_skills", []),
            "reviewer_notes": ""
        }
        eval_res = eval_col.insert_one(eval_doc)
        eval_id = str(eval_res.inserted_id)
        eval_doc["eval_id"] = eval_id

        self.log_audit(user_username, "EVALUATE_CANDIDATE", "Evaluation", eval_id, f"Evaluated candidate {cand_doc['candidate_name']} - Score: {eval_doc['overall_score']}%")
        return eval_id

    def get_all_evaluations(self) -> List[Dict[str, Any]]:
        eval_col = self.get_collection("evaluations")
        evals = list(eval_col.find())
        for e in evals:
            e["eval_id"] = str(e.get("_id", e.get("eval_id", "")))
        evals.sort(key=lambda x: x.get("overall_score", 0.0), reverse=True)
        return evals

    def update_evaluation_status(self, eval_id: str, new_status: str, notes: str = "", user_username: str = "admin") -> bool:
        eval_col = self.get_collection("evaluations")
        try:
            from bson import ObjectId
            query = {"$or": [{"_id": str(eval_id)}, {"_id": ObjectId(str(eval_id))}, {"eval_id": str(eval_id)}]}
        except Exception:
            query = {"$or": [{"_id": str(eval_id)}, {"eval_id": str(eval_id)}]}

        eval_col.update_one(
            query,
            {"$set": {"status": new_status, "reviewer_notes": notes}}
        )
        self.log_audit(user_username, "UPDATE_STATUS", "Evaluation", str(eval_id), f"Updated candidate status to '{new_status}' with notes: '{notes}'")
        return True

    # --------------------------------------------------
    # AUDIT LOGGING OPERATIONS
    # --------------------------------------------------
    def log_audit(self, user_username: str, action: str, resource_type: str, resource_id: str = "", details: str = "", ip_address: str = "127.0.0.1"):
        self.mongo.log_audit(user_username, action, resource_type, resource_id, details, ip_address)

    def get_audit_logs(self, limit: int = 100) -> List[Dict[str, Any]]:
        return self.mongo.get_audit_logs(limit=limit)
