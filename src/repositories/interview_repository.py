"""
Interview Repository Module
Encapsulates MongoDB document persistence for interview scheduling, interviewer assignments,
meeting links, and qualitative evaluation scorecards.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from bson import ObjectId


class InterviewRepository:
    """
    MongoDB Interview Scheduling & Scorecard Repository.
    """

    def __init__(self, db_manager: Any):
        self.db = db_manager

    def schedule_interview(
        self,
        candidate_name: str,
        candidate_id: str,
        job_title: str,
        interviewer: str,
        interview_type: str = "Technical Interview",
        scheduled_date: str = "",
        scheduled_time: str = "",
        meeting_link: str = "",
        notes: str = "",
        scheduled_by: str = "recruiter"
    ) -> Dict[str, Any]:
        """Schedules a new candidate interview."""
        col = self.db.get_collection("interviews")
        doc = {
            "candidate_name": candidate_name,
            "candidate_id": str(candidate_id),
            "job_title": job_title,
            "interviewer": interviewer,
            "interview_type": interview_type,  # HR, Technical, Manager, Final
            "scheduled_date": scheduled_date or str(datetime.now().date()),
            "scheduled_time": scheduled_time or "10:00 AM",
            "meeting_link": meeting_link or "https://meet.google.com/xyz-abc-123",
            "notes": notes,
            "status": "Scheduled",  # Scheduled, Completed, Cancelled
            "scorecard": None,
            "scheduled_by": scheduled_by,
            "created_at": datetime.now()
        }
        res = col.insert_one(doc)
        doc["_id"] = str(res.inserted_id)
        doc["interview_id"] = doc["_id"]

        # Also update candidate status to Interview Scheduled
        self.db.update_evaluation_status(candidate_id, "Interview Scheduled", f"Scheduled {interview_type} with {interviewer}", scheduled_by)
        self.db.log_audit(scheduled_by, "SCHEDULE_INTERVIEW", "Interview", doc["_id"], f"Scheduled {interview_type} for {candidate_name}")
        return doc

    def get_all_interviews(self) -> List[Dict[str, Any]]:
        """Retrieves all scheduled interviews from MongoDB."""
        col = self.db.get_collection("interviews")
        interviews = list(col.find())
        for i in interviews:
            i["interview_id"] = str(i.get("_id", i.get("interview_id", "")))
        interviews.sort(key=lambda x: x.get("created_at", datetime.now()), reverse=True)
        return interviews

    def save_scorecard(
        self,
        interview_id: str,
        tech_score: int,
        comm_score: int,
        problem_score: int,
        culture_score: int,
        leadership_score: int,
        recommendation: str = "Hire",
        feedback_notes: str = "",
        evaluated_by: str = "hiring_manager"
    ) -> bool:
        """Saves interview scorecard and overall hiring recommendation."""
        col = self.db.get_collection("interviews")
        try:
            query = {"$or": [{"_id": str(interview_id)}, {"_id": ObjectId(str(interview_id))}, {"interview_id": str(interview_id)}]}
        except Exception:
            query = {"$or": [{"_id": str(interview_id)}, {"interview_id": str(interview_id)}]}

        scorecard = {
            "tech_score": tech_score,
            "comm_score": comm_score,
            "problem_score": problem_score,
            "culture_score": culture_score,
            "leadership_score": leadership_score,
            "recommendation": recommendation,  # Strong Hire, Hire, Neutral, No Hire, Strong No Hire
            "feedback_notes": feedback_notes,
            "evaluated_by": evaluated_by,
            "submitted_at": datetime.now()
        }

        col.update_one(query, {"$set": {"scorecard": scorecard, "status": "Completed"}})
        self.db.log_audit(evaluated_by, "SUBMIT_SCORECARD", "Interview", str(interview_id), f"Submitted scorecard with recommendation: {recommendation}")
        return True
