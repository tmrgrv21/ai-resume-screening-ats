"""
AuthManager Module
Handles enterprise authentication, RBAC authorization, password security,
account lockout rate limiting, persistent session management, and password reset architecture.
"""

from typing import Dict, Any, Optional, Tuple, List
from src.security.password import hash_password, verify_password, validate_password_strength
from src.security.rate_limiter import RateLimiter
from src.services.session_service import SessionService
from src.services.security_service import SecurityService

# Centralized Enterprise RBAC Role Permissions
ROLE_PERMISSIONS: Dict[str, Dict[str, bool]] = {
    "admin": {
        "can_create_requisition": True,
        "can_upload_resumes": True,
        "can_run_screening": True,
        "can_update_status": True,
        "can_export_reports": True,
        "can_view_audit_logs": True,
        "can_manage_system": True,
        "can_delete": True
    },
    "recruiter": {
        "can_create_requisition": True,
        "can_upload_resumes": True,
        "can_run_screening": True,
        "can_update_status": True,
        "can_export_reports": True,
        "can_view_audit_logs": False,
        "can_manage_system": False,
        "can_delete": False
    },
    "hiring_manager": {
        "can_create_requisition": False,
        "can_upload_resumes": False,
        "can_run_screening": False,
        "can_update_status": True,
        "can_export_reports": True,
        "can_view_audit_logs": False,
        "can_manage_system": False,
        "can_delete": False
    },
    "viewer": {
        "can_create_requisition": False,
        "can_upload_resumes": False,
        "can_run_screening": False,
        "can_update_status": False,
        "can_export_reports": False,
        "can_view_audit_logs": False,
        "can_manage_system": False,
        "can_delete": False
    }
}


from src.repositories.user_repository import UserRepository

class AuthManager:
    """
    Enterprise Authentication and Authorization Manager.
    """

    def __init__(self, db_manager: Any):
        self.db = db_manager
        self.user_repo = UserRepository(db_manager)
        self.rate_limiter = RateLimiter(db_manager)
        self.session_service = SessionService(db_manager)
        self.security_service = SecurityService(db_manager)

    def login(self, identifier: str, password: str, user_agent: str = "Streamlit Session", ip_address: str = "127.0.0.1") -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """
        Authenticates user with rate-limiting account lockout check and session creation.
        Returns (success: bool, user_dict_with_session: Optional[Dict], error_msg: Optional[str])
        """
        if not identifier or not password:
            return False, None, "Username/Email and Password are required."

        # Check Rate Limiting & Account Lockout
        is_locked, lock_msg = self.rate_limiter.is_locked_out(identifier)
        if is_locked:
            self.db.log_audit(identifier, "LOGIN_BLOCKED_LOCKOUT", "User", identifier, lock_msg, ip_address)
            return False, None, lock_msg

        users_col = self.db.get_collection("users")
        user = users_col.find_one({"username": identifier})
        if not user:
            user = users_col.find_one({"email": identifier.strip().lower()})

        if user and verify_password(password, user["password_hash"]):
            # Record Successful Login
            self.rate_limiter.record_attempt(identifier, success=True, ip_address=ip_address)

            role = user.get("role", "viewer").lower()
            permissions = ROLE_PERMISSIONS.get(role, ROLE_PERMISSIONS["viewer"])

            # Create Persistent Session
            session = self.session_service.create_session(
                user_id=str(user.get("_id", user.get("id", user["username"]))),
                username=user["username"],
                user_agent=user_agent,
                ip_address=ip_address
            )

            user_res = {
                "user_id": str(user.get("_id", user.get("id", user["username"]))),
                "username": user["username"],
                "email": user.get("email", ""),
                "full_name": user.get("full_name", user["username"].title()),
                "role": role.title() if role != "hiring_manager" else "HiringManager",
                "role_raw": role,
                "permissions": permissions,
                "session_token": session["raw_token"],
                "session_device": session["device_name"]
            }

            self.db.log_audit(user["username"], "USER_LOGIN", "User", user["username"], f"Logged in as {role.title()} ({session['device_name']})", ip_address)
            return True, user_res, None
        else:
            # Record Failed Attempt
            self.rate_limiter.record_attempt(identifier, success=False, ip_address=ip_address)
            self.db.log_audit(identifier, "USER_LOGIN_FAILED", "User", identifier, "Invalid credentials provided", ip_address)
            return False, None, "Invalid username/email or password."

    def register(self, username: str, email: str, password: str, role: str = "recruiter", full_name: str = "", organization: str = "") -> Tuple[bool, str]:
        """
        Registers a new user with real-time password strength validation.
        """
        if not username or not email or not password:
            return False, "All required fields must be filled out."

        # Public sign up restricts self-assigned admin roles
        clean_role = role.lower()
        if clean_role == "admin":
            return False, "Public account registration cannot assign Admin privileges."

        # Validate Password Strength
        strength = validate_password_strength(password)
        if not strength["is_valid"]:
            return False, "Password fails security criteria (Minimum 8 chars, 1 uppercase, 1 lowercase, 1 number)."

        users_col = self.db.get_collection("users")
        if users_col.find_one({"username": username}):
            return False, "Username is already taken. Please choose another username."

        if users_col.find_one({"email": email.strip().lower()}):
            return False, "An account with this email address already exists."

        pwd_hash = hash_password(password)
        user_doc = {
            "username": username,
            "email": email.strip().lower(),
            "full_name": full_name or username.title(),
            "password_hash": pwd_hash,
            "role": clean_role,
            "status": "active",
            "email_verified": True,
            "organization": organization
        }
        users_col.insert_one(user_doc)

        self.db.log_audit(username, "USER_REGISTER", "User", username, f"Registered account with role {clean_role}")
        return True, f"Account '{username}' registered successfully! You can now sign in."

    def logout(self, session_token: str) -> bool:
        """Revokes persistent user session."""
        if session_token:
            return self.session_service.revoke_session(session_token, reason="User Logout")
        return True

    def check_permission(self, user: Dict[str, Any], permission_name: str) -> bool:
        """Verifies if user profile has specified permission."""
        if not user or "permissions" not in user:
            return False
        return user["permissions"].get(permission_name, False)
