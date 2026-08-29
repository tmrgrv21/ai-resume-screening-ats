"""
Rate Limiter & Account Lockout Module
Prevents brute-force credential stuffing by enforcing max failed login attempts
and temporary account lockout periods.
"""

from datetime import datetime, timedelta
from typing import Dict, Any, Tuple, Optional

# Configurable Defaults
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 15


class RateLimiter:
    """
    Manages login rate limiting and brute-force account lockout protection.
    """

    def __init__(self, db_manager: Any = None):
        self.db = db_manager
        # In-memory fallback tracking if db is offline
        self._memory_attempts = {}
        self._memory_locks = {}

    def is_locked_out(self, identifier: str) -> Tuple[bool, Optional[str]]:
        """
        Checks if specified user or IP address is currently locked out.
        Returns (is_locked: bool, unlock_time_msg: Optional[str])
        """
        identifier = identifier.strip().lower()
        now = datetime.now()

        # Check DB tracking if available
        if self.db and hasattr(self.db, 'get_collection'):
            try:
                attempts_col = self.db.get_collection("login_attempts")
                cutoff = now - timedelta(minutes=LOCKOUT_DURATION_MINUTES)
                recent_fails = list(attempts_col.find({
                    "identifier": identifier,
                    "success": False,
                    "timestamp": {"$gte": cutoff}
                }))

                if len(recent_fails) >= MAX_LOGIN_ATTEMPTS:
                    last_fail_time = recent_fails[-1].get("timestamp", now)
                    unlock_time = last_fail_time + timedelta(minutes=LOCKOUT_DURATION_MINUTES)
                    remaining_mins = max(1, int((unlock_time - now).total_seconds() / 60))
                    return True, f"Account temporarily locked due to 5 failed login attempts. Try again in {remaining_mins} minutes."
                return False, None
            except Exception:
                pass

        # Memory tracking fallback
        if identifier in self._memory_locks:
            unlock_time = self._memory_locks[identifier]
            if now < unlock_time:
                remaining_mins = max(1, int((unlock_time - now).total_seconds() / 60))
                return True, f"Account temporarily locked due to 5 failed login attempts. Try again in {remaining_mins} minutes."
            else:
                del self._memory_locks[identifier]
                self._memory_attempts[identifier] = 0

        return False, None

    def record_attempt(self, identifier: str, success: bool, ip_address: str = "127.0.0.1"):
        """
        Records a login attempt and triggers lockout if max failed attempts reached.
        """
        identifier = identifier.strip().lower()
        now = datetime.now()

        if self.db and hasattr(self.db, 'get_collection'):
            try:
                attempts_col = self.db.get_collection("login_attempts")
                attempts_col.insert_one({
                    "identifier": identifier,
                    "success": success,
                    "ip_address": ip_address,
                    "timestamp": now
                })
                if success:
                    # Clear failed attempts on successful login
                    attempts_col.delete_many({"identifier": identifier, "success": False})
                return
            except Exception:
                pass

        # Memory tracking fallback
        if success:
            self._memory_attempts[identifier] = 0
            if identifier in self._memory_locks:
                del self._memory_locks[identifier]
        else:
            self._memory_attempts[identifier] = self._memory_attempts.get(identifier, 0) + 1
            if self._memory_attempts[identifier] >= MAX_LOGIN_ATTEMPTS:
                self._memory_locks[identifier] = now + timedelta(minutes=LOCKOUT_DURATION_MINUTES)
