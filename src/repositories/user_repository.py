"""
User Repository Module
Encapsulates MongoDB document persistence for users collection.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from src.security.password import hash_password, verify_password


class UserRepository:
    """
    MongoDB User Repository.
    """

    def __init__(self, db_manager: Any):
        self.db = db_manager

    def find_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        col = self.db.get_collection("users")
        return col.find_one({"username": username})

    def find_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        col = self.db.get_collection("users")
        return col.find_one({"email": email.strip().lower()})

    def find_by_username_or_email(self, identifier: str) -> Optional[Dict[str, Any]]:
        col = self.db.get_collection("users")
        cleaned = identifier.strip().lower()
        user = col.find_one({"username": identifier})
        if not user:
            user = col.find_one({"email": cleaned})
        return user

    def create(self, username: str, email: str, password: str, role: str = "recruiter", full_name: str = "", organization: str = "") -> Optional[Dict[str, Any]]:
        col = self.db.get_collection("users")
        cleaned_email = email.strip().lower()

        if self.find_by_username(username) or self.find_by_email(cleaned_email):
            return None

        pwd_hash = hash_password(password)
        doc = {
            "username": username,
            "full_name": full_name or username.title(),
            "email": cleaned_email,
            "password_hash": pwd_hash,
            "role": role.lower(),
            "status": "active",
            "email_verified": True,
            "organization": organization,
            "failed_login_attempts": 0,
            "locked_until": None,
            "last_login_at": None,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        res = col.insert_one(doc)
        doc["_id"] = res.inserted_id
        self.db.log_audit(username, "USER_REGISTER", "User", username, f"Created account ({role})")
        return doc

    def authenticate(self, identifier: str, password: str) -> Optional[Dict[str, Any]]:
        user = self.find_by_username_or_email(identifier)
        if user and verify_password(password, user["password_hash"]):
            col = self.db.get_collection("users")
            col.update_one({"_id": user["_id"]}, {"$set": {"last_login_at": datetime.now(), "failed_login_attempts": 0}})
            return user
        return None

    def get_user_preferences(self, username: str) -> Dict[str, Any]:
        """Retrieves persistent user theme and UI preferences from MongoDB."""
        col = self.db.get_collection("user_preferences")
        prefs = col.find_one({"username": username})
        if not prefs:
            return {
                "username": username,
                "theme": "dark",
                "accent_color": "indigo",
                "high_contrast": False,
                "dashboard_layout": {}
            }
        return prefs

    def save_user_preferences(self, username: str, theme: str = "dark", accent_color: str = "indigo", high_contrast: bool = False) -> bool:
        """Saves user theme and accent preferences in MongoDB."""
        col = self.db.get_collection("user_preferences")
        existing = col.find_one({"username": username})
        doc = {
            "username": username,
            "theme": theme.lower(),
            "accent_color": accent_color.lower(),
            "high_contrast": high_contrast,
            "updated_at": datetime.now()
        }
        if existing:
            col.update_one({"username": username}, {"$set": doc})
        else:
            col.insert_one(doc)
        return True
