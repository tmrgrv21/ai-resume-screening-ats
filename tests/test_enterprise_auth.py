"""
Unit tests for Enterprise Authentication, Password Security, Account Lockout, and Session Management.
"""

import unittest
from src.database.mongo_manager import MongoManager
from src.auth import AuthManager
from src.security.password import hash_password, verify_password, validate_password_strength
from src.security.rate_limiter import RateLimiter
from src.services.session_service import SessionService
from src.services.security_service import SecurityService


class TestEnterpriseAuth(unittest.TestCase):

    def setUp(self):
        self.db = MongoManager(db_name="test_ai_screening_auth")
        self.auth = AuthManager(self.db)

    def test_bcrypt_hashing_and_verification(self):
        pwd = "SecurePassword123!"
        hashed = hash_password(pwd)
        self.assertNotEqual(pwd, hashed)
        self.assertTrue(verify_password(pwd, hashed))
        self.assertFalse(verify_password("WrongPassword123!", hashed))

    def test_password_strength_validation(self):
        weak = validate_password_strength("12345")
        self.assertFalse(weak["is_valid"])
        self.assertEqual(weak["rating"], "Weak")

        strong = validate_password_strength("ComplexPass123!")
        self.assertTrue(strong["is_valid"])
        self.assertIn(strong["rating"], ["Good", "Strong"])

    def test_account_lockout_after_failed_logins(self):
        identifier = "brute_force_user"
        limiter = RateLimiter(self.db)

        # 5 consecutive failed attempts
        for _ in range(5):
            limiter.record_attempt(identifier, success=False)

        is_locked, msg = limiter.is_locked_out(identifier)
        self.assertTrue(is_locked)
        self.assertIn("temporarily locked", msg)

    def test_session_creation_and_revocation(self):
        session_svc = SessionService(self.db)
        session = session_svc.create_session("user_100", "testuser", "Chrome Browser", "192.168.1.1")
        self.assertIsNotNone(session["raw_token"])

        is_valid, doc, err = session_svc.validate_session(session["raw_token"])
        self.assertTrue(is_valid)

        revoked = session_svc.revoke_session(session["raw_token"])
        self.assertTrue(revoked)

        is_valid_after, _, _ = session_svc.validate_session(session["raw_token"])
        self.assertFalse(is_valid_after)

    def test_password_reset_token_flow(self):
        import uuid
        uid = uuid.uuid4().hex[:6]
        sec_svc = SecurityService(self.db)
        email = f"user_reset_{uid}@company.com"
        username = f"user_reset_{uid}"
        self.db.get_collection("users").insert_one({
            "username": username,
            "email": email,
            "password_hash": hash_password("OldPassword123!"),
            "role": "recruiter"
        })

        success, msg, raw_token = sec_svc.create_password_reset_token(email)
        self.assertTrue(success)
        self.assertIsNotNone(raw_token)

        # Perform password reset
        res_ok, res_msg = sec_svc.reset_password_with_token(raw_token, "NewSecurePass123!")
        self.assertTrue(res_ok)

        # Single-use check (second reset should fail)
        res_again, _ = sec_svc.reset_password_with_token(raw_token, "AnotherPass123!")
        self.assertFalse(res_again)


if __name__ == "__main__":
    unittest.main()
