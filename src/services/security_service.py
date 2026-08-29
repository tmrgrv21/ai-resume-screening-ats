"""
Security Service Module
Handles single-use Password Reset Token generation & validation, Email Verification tokens,
and 2FA TOTP / Email OTP verification flow.
"""

import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, Tuple, Optional

# Token Expiration Configs
PASSWORD_RESET_EXPIRY_MINUTES = 60
EMAIL_VERIFICATION_EXPIRY_HOURS = 24


def hash_token(token: str) -> str:
    """Hashes token for secure database storage."""
    return hashlib.sha256(token.encode('utf-8')).hexdigest()


class SecurityService:
    """
    Security Service for Password Reset, Email Verification, and 2FA.
    """

    def __init__(self, db_manager: Any):
        self.db = db_manager

    # --------------------------------------------------
    # FORGOT / RESET PASSWORD TOKENS
    # --------------------------------------------------
    def create_password_reset_token(self, email: str) -> Tuple[bool, str, str]:
        """
        Creates single-use password reset token for given email.
        Always returns generic success indicator for security (no email enumeration).
        Returns (success: bool, generic_message: str, raw_token_for_dev_mode: str)
        """
        email = email.strip().lower()
        users_col = self.db.get_collection("users")
        user = users_col.find_one({"email": email})

        raw_token = secrets.token_urlsafe(32)
        token_hash = hash_token(raw_token)
        now = datetime.now()
        expires_at = now + timedelta(minutes=PASSWORD_RESET_EXPIRY_MINUTES)

        resets_col = self.db.get_collection("password_resets")

        if user:
            # Invalidate any existing unused reset tokens for this email
            resets_col.delete_many({"email": email, "is_used": False})

            resets_col.insert_one({
                "email": email,
                "token_hash": token_hash,
                "created_at": now,
                "expires_at": expires_at,
                "is_used": False
            })

            self.db.log_audit(user.get("username", email), "PASSWORD_RESET_REQUESTED", "User", email, "Generated single-use password reset token")

        # Always return generic message to prevent email enumeration attacks
        msg = "If an account exists for this email address, password-reset instructions will be provided."
        return True, msg, raw_token

    def reset_password_with_token(self, raw_token: str, new_password: str) -> Tuple[bool, str]:
        """
        Validates reset token and updates user password securely.
        """
        if not raw_token or not new_password:
            return False, "Invalid parameters."

        from src.security.password import validate_password_strength, hash_password

        # Check password strength
        strength = validate_password_strength(new_password)
        if not strength["is_valid"]:
            return False, "Password does not meet strength requirements (Minimum 8 chars, 1 uppercase, 1 lowercase, 1 number)."

        token_hash = hash_token(raw_token)
        resets_col = self.db.get_collection("password_resets")
        reset_doc = resets_col.find_one({"token_hash": token_hash, "is_used": False})

        if not reset_doc:
            return False, "Password reset token is invalid or has already been used."

        now = datetime.now()
        expires_at = reset_doc.get("expires_at")
        if isinstance(expires_at, str):
            try:
                expires_at = datetime.fromisoformat(expires_at)
            except Exception:
                expires_at = now

        if expires_at and now > expires_at:
            return False, "Password reset token has expired. Please request a new password reset."

        # Mark token as used
        resets_col.update_one({"token_hash": token_hash}, {"$set": {"is_used": True, "used_at": now}})

        # Update User Password
        email = reset_doc.get("email")
        users_col = self.db.get_collection("users")
        new_hash = hash_password(new_password)

        users_col.update_one({"email": email}, {"$set": {"password_hash": new_hash, "updated_at": now}})

        self.db.log_audit(email, "PASSWORD_RESET_COMPLETED", "User", email, "Successfully reset password via single-use reset token")
        return True, "Password has been successfully updated! You can now sign in with your new password."

    # --------------------------------------------------
    # EMAIL VERIFICATION ARCHITECTURE
    # --------------------------------------------------
    def create_email_verification_token(self, username: str, email: str) -> str:
        """Generates email verification token for new accounts."""
        raw_token = secrets.token_urlsafe(32)
        token_hash = hash_token(raw_token)
        now = datetime.now()
        expires_at = now + timedelta(hours=EMAIL_VERIFICATION_EXPIRY_HOURS)

        verif_col = self.db.get_collection("email_verifications")
        verif_col.delete_many({"email": email})

        verif_col.insert_one({
            "username": username,
            "email": email,
            "token_hash": token_hash,
            "created_at": now,
            "expires_at": expires_at,
            "is_verified": False
        })
        return raw_token

    def verify_email_token(self, raw_token: str) -> Tuple[bool, str]:
        """Verifies email verification token."""
        token_hash = hash_token(raw_token)
        verif_col = self.db.get_collection("email_verifications")
        doc = verif_col.find_one({"token_hash": token_hash, "is_verified": False})

        if not doc:
            return False, "Verification token is invalid or has already been used."

        now = datetime.now()
        verif_col.update_one({"token_hash": token_hash}, {"$set": {"is_verified": True, "verified_at": now}})

        users_col = self.db.get_collection("users")
        users_col.update_one({"username": doc["username"]}, {"$set": {"email_verified": True}})

        self.db.log_audit(doc["username"], "EMAIL_VERIFIED", "User", doc["username"], "Verified email address successfully")
        return True, "Email address verified successfully!"
