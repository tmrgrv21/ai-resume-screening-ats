"""
Notification Service Module
Manages platform activity alerts, resume analysis completion notices, interview reminders,
and security notifications in MongoDB notifications collection.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime


class NotificationService:
    """
    MongoDB Real-Time Notification Center Service.
    """

    def __init__(self, db_manager: Any):
        self.db = db_manager

    def create_notification(self, username: str, title: str, message: str, category: str = "info", link: str = "") -> Dict[str, Any]:
        """Creates a new user notification document in MongoDB."""
        col = self.db.get_collection("notifications")
        doc = {
            "username": username,
            "title": title,
            "message": message,
            "category": category,  # info, success, warning, error
            "link": link,
            "is_read": False,
            "created_at": datetime.now()
        }
        res = col.insert_one(doc)
        doc["_id"] = str(res.inserted_id)
        return doc

    def get_notifications_for_user(self, username: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Retrieves user notifications sorted by created_at descending."""
        col = self.db.get_collection("notifications")
        notes = list(col.find({"$or": [{"username": username}, {"username": "all"}]}))
        notes.sort(key=lambda x: x.get("created_at", datetime.now()), reverse=True)
        return notes[:limit]

    def mark_all_as_read(self, username: str) -> bool:
        """Marks all notifications as read for specified user."""
        col = self.db.get_collection("notifications")
        col.update_one({"$or": [{"username": username}, {"username": "all"}]}, {"$set": {"is_read": True}})
        return True
