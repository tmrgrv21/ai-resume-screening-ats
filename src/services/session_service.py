"""
Session Service Module
Handles persistent multi-device user sessions, token generation, device/browser metadata parsing,
idle & absolute timeout validation, and active session revocation.
"""

import os
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple

# Configurable Timeouts
IDLE_TIMEOUT_MINUTES = int(os.getenv("IDLE_TIMEOUT_MINUTES", 30))
ABSOLUTE_TIMEOUT_HOURS = int(os.getenv("ABSOLUTE_TIMEOUT_HOURS", 8))


def hash_token(token: str) -> str:
    """Hashes session token for secure storage."""
    return hashlib.sha256(token.encode('utf-8')).hexdigest()


def parse_device_info(user_agent: str) -> Dict[str, str]:
    """Parses user agent string into browser and OS labels."""
    ua_lower = user_agent.lower()

    if "chrome" in ua_lower and "edg" not in ua_lower:
        browser = "Google Chrome"
    elif "edg" in ua_lower:
        browser = "Microsoft Edge"
    elif "firefox" in ua_lower:
        browser = "Mozilla Firefox"
    elif "safari" in ua_lower and "chrome" not in ua_lower:
        browser = "Apple Safari"
    else:
        browser = "Standard Browser"

    if "windows" in ua_lower:
        os_name = "Windows OS"
    elif "mac" in ua_lower or "darwin" in ua_lower:
        os_name = "macOS"
    elif "linux" in ua_lower:
        os_name = "Linux OS"
    elif "android" in ua_lower:
        os_name = "Android"
    elif "iphone" in ua_lower or "ipad" in ua_lower:
        os_name = "iOS"
    else:
        os_name = "Desktop/Mobile"

    return {
        "browser": browser,
        "operating_system": os_name,
        "device_name": f"{browser} on {os_name}"
    }


class SessionService:
    """
    Persistent Session Management Service.
    """

    def __init__(self, db_manager: Any):
        self.db = db_manager

    def create_session(self, user_id: str, username: str, user_agent: str = "Streamlit Session", ip_address: str = "127.0.0.1") -> Dict[str, Any]:
        """
        Creates a new persistent session token and saves session document to MongoDB.
        """
        raw_token = secrets.token_urlsafe(32)
        token_hash = hash_token(raw_token)
        now = datetime.now()
        expires_at = now + timedelta(hours=ABSOLUTE_TIMEOUT_HOURS)

        device_meta = parse_device_info(user_agent)

        session_doc = {
            "user_id": str(user_id),
            "username": username,
            "session_token_hash": token_hash,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "browser": device_meta["browser"],
            "operating_system": device_meta["operating_system"],
            "device_name": device_meta["device_name"],
            "created_at": now,
            "last_activity_at": now,
            "expires_at": expires_at,
            "is_active": True,
            "revoked_at": None
        }

        sessions_col = self.db.get_collection("sessions")
        sessions_col.insert_one(session_doc)
        self.db.log_audit(username, "SESSION_CREATED", "Session", username, f"Created new session ({device_meta['device_name']})", ip_address)

        session_doc["raw_token"] = raw_token
        return session_doc

    def validate_session(self, raw_token: str) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """
        Validates raw session token against expiration and idle timeout.
        Returns (is_valid: bool, session_doc: Optional[Dict], reason: Optional[str])
        """
        if not raw_token:
            return False, None, "No session token provided."

        token_hash = hash_token(raw_token)
        sessions_col = self.db.get_collection("sessions")
        session = sessions_col.find_one({"session_token_hash": token_hash, "is_active": True})

        if not session:
            return False, None, "Session token is invalid or has been revoked."

        now = datetime.now()

        # Check Absolute Expiry
        expires_at = session.get("expires_at")
        if isinstance(expires_at, str):
            try:
                expires_at = datetime.fromisoformat(expires_at)
            except Exception:
                expires_at = now + timedelta(hours=1)

        if expires_at and now > expires_at:
            self.revoke_session(raw_token, reason="Absolute Expiry")
            return False, None, "Session has reached its absolute expiration time (8 hours). Please sign in again."

        # Check Idle Timeout
        last_act = session.get("last_activity_at", now)
        if isinstance(last_act, str):
            try:
                last_act = datetime.fromisoformat(last_act)
            except Exception:
                last_act = now

        if now - last_act > timedelta(minutes=IDLE_TIMEOUT_MINUTES):
            self.revoke_session(raw_token, reason="Idle Timeout")
            return False, None, f"Session timed out due to {IDLE_TIMEOUT_MINUTES} minutes of inactivity. Please sign in again."

        # Update last activity timestamp
        sessions_col.update_one(
            {"session_token_hash": token_hash},
            {"$set": {"last_activity_at": now}}
        )
        session["last_activity_at"] = now
        return True, session, None

    def revoke_session(self, raw_token: str, reason: str = "User Logout") -> bool:
        """Revokes a specific session by token."""
        token_hash = hash_token(raw_token)
        sessions_col = self.db.get_collection("sessions")
        session = sessions_col.find_one({"session_token_hash": token_hash})
        if session:
            sessions_col.update_one(
                {"session_token_hash": token_hash},
                {"$set": {"is_active": False, "revoked_at": datetime.now()}}
            )
            self.db.log_audit(session.get("username", "user"), "SESSION_REVOKED", "Session", session.get("username", ""), f"Revoked session ({reason})")
            return True
        return False

    def revoke_all_other_sessions(self, user_id: str, current_raw_token: str) -> int:
        """Revokes all active sessions for user except current session."""
        current_hash = hash_token(current_raw_token)
        sessions_col = self.db.get_collection("sessions")
        all_user_sessions = sessions_col.find({"user_id": str(user_id), "is_active": True})

        revoked_count = 0
        for s in all_user_sessions:
            if s.get("session_token_hash") != current_hash:
                sessions_col.update_one(
                    {"_id": s["_id"]},
                    {"$set": {"is_active": False, "revoked_at": datetime.now()}}
                )
                revoked_count += 1

        self.db.log_audit(str(user_id), "REVOKE_OTHER_SESSIONS", "Session", str(user_id), f"Revoked {revoked_count} other active device sessions")
        return revoked_count

    def get_active_sessions_for_user(self, user_id: str) -> List[Dict[str, Any]]:
        """Returns list of active sessions for user."""
        sessions_col = self.db.get_collection("sessions")
        sessions = sessions_col.find({"user_id": str(user_id), "is_active": True})
        return list(sessions)
