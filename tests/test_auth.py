"""
Unit tests for AuthManager & RBAC Permissions.
"""

import unittest
from src.database.db_manager import DatabaseManager
from src.auth import AuthManager


class TestAuth(unittest.TestCase):

    def setUp(self):
        self.db = DatabaseManager()
        self.auth = AuthManager(self.db)

    def test_admin_permissions(self):
        success, user, _ = self.auth.login("admin", "admin123")
        self.assertTrue(success)
        self.assertIsNotNone(user)
        self.assertTrue(self.auth.check_permission(user, "can_manage_system"))
        self.assertTrue(self.auth.check_permission(user, "can_view_audit_logs"))

    def test_recruiter_permissions(self):
        success, user, _ = self.auth.login("recruiter", "recruiter123")
        self.assertTrue(success)
        self.assertIsNotNone(user)
        self.assertTrue(self.auth.check_permission(user, "can_run_screening"))
        self.assertFalse(self.auth.check_permission(user, "can_view_audit_logs"))

    def test_viewer_permissions(self):
        success, user, _ = self.auth.login("viewer", "viewer123")
        self.assertTrue(success)
        self.assertIsNotNone(user)
        self.assertFalse(self.auth.check_permission(user, "can_run_screening"))
        self.assertFalse(self.auth.check_permission(user, "can_export_reports"))


if __name__ == "__main__":
    unittest.main()
