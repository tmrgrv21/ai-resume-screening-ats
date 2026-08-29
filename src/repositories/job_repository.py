"""
Job Repository Module
Encapsulates MongoDB document persistence for open job requisitions, required/preferred skills,
salary ranges, and job status management.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from bson import ObjectId


class JobRepository:
    """
    MongoDB Job Requisition Repository.
    """

    def __init__(self, db_manager: Any):
        self.db = db_manager

    def create_job(
        self,
        title: str,
        description: str,
        department: str = "Engineering",
        location: str = "Remote",
        employment_type: str = "Full-time",
        required_experience: float = 3.0,
        required_skills: Optional[List[str]] = None,
        preferred_skills: Optional[List[str]] = None,
        salary_range: str = "$100k - $140k",
        created_by: str = "admin"
    ) -> Dict[str, Any]:
        """Creates a new job opening record in MongoDB."""
        col = self.db.get_collection("job_requisitions")
        doc = {
            "title": title,
            "description": description,
            "department": department,
            "location": location,
            "employment_type": employment_type,
            "required_experience": required_experience,
            "required_skills": required_skills or [],
            "preferred_skills": preferred_skills or [],
            "salary_range": salary_range,
            "status": "Open",  # Draft, Open, Paused, Closed, Archived
            "created_by": created_by,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        res = col.insert_one(doc)
        doc["_id"] = str(res.inserted_id)
        doc["job_id"] = doc["_id"]
        self.db.log_audit(created_by, "CREATE_JOB", "JobRequisition", doc["_id"], f"Created job opening: '{title}' ({department})")
        return doc

    def get_all_jobs(self, status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieves all jobs from MongoDB."""
        col = self.db.get_collection("job_requisitions")
        filter_dict = {}
        if status_filter and status_filter != "All":
            filter_dict["status"] = status_filter

        jobs = list(col.find(filter_dict))
        for j in jobs:
            j["job_id"] = str(j.get("_id", j.get("job_id", "")))
        jobs.sort(key=lambda x: x.get("created_at", datetime.now()), reverse=True)
        return jobs

    def get_job_by_id(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves job by ID."""
        col = self.db.get_collection("job_requisitions")
        try:
            query = {"$or": [{"_id": str(job_id)}, {"_id": ObjectId(str(job_id))}, {"job_id": str(job_id)}]}
        except Exception:
            query = {"$or": [{"_id": str(job_id)}, {"job_id": str(job_id)}]}

        job = col.find_one(query)
        if job:
            job["job_id"] = str(job.get("_id", job_id))
        return job

    def update_job_status(self, job_id: str, new_status: str, user_username: str = "admin") -> bool:
        """Updates job status (Open, Paused, Closed, Archived)."""
        col = self.db.get_collection("job_requisitions")
        try:
            query = {"$or": [{"_id": str(job_id)}, {"_id": ObjectId(str(job_id))}, {"job_id": str(job_id)}]}
        except Exception:
            query = {"$or": [{"_id": str(job_id)}, {"job_id": str(job_id)}]}

        col.update_one(query, {"$set": {"status": new_status, "updated_at": datetime.now()}})
        self.db.log_audit(user_username, "UPDATE_JOB_STATUS", "JobRequisition", str(job_id), f"Updated job status to '{new_status}'")
        return True
