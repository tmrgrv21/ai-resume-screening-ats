"""
Password Security Module
Handles Bcrypt salted password hashing, verification, and dynamic password strength validation.
"""

import re
import hashlib
from typing import Dict, Any, Tuple, List

try:
    import bcrypt
    BCRYPT_AVAILABLE = True
except ImportError:
    BCRYPT_AVAILABLE = False


def hash_password(password: str) -> str:
    """
    Hashes password securely using Bcrypt (or salted SHA-256 fallback if bcrypt is missing).
    """
    if not password:
        raise ValueError("Password cannot be empty.")

    if BCRYPT_AVAILABLE:
        # Generate salted Bcrypt hash
        salt = bcrypt.gensalt(rounds=12)
        pwd_bytes = password.encode('utf-8')
        hashed = bcrypt.hashpw(pwd_bytes, salt)
        return hashed.decode('utf-8')
    else:
        # Fallback SHA-256 with salt
        salt = "ai_resume_screening_secure_salt_2026"
        return "sha256$" + hashlib.sha256((password + salt).encode('utf-8')).hexdigest()


def verify_password(password: str, hashed_password: str) -> bool:
    """
    Verifies candidate password against stored bcrypt or fallback hash.
    """
    if not password or not hashed_password:
        return False

    if BCRYPT_AVAILABLE and hashed_password.startswith("$2"):
        try:
            pwd_bytes = password.encode('utf-8')
            hash_bytes = hashed_password.encode('utf-8')
            return bcrypt.checkpw(pwd_bytes, hash_bytes)
        except Exception:
            return False
    elif hashed_password.startswith("sha256$"):
        salt = "ai_resume_screening_secure_salt_2026"
        expected = "sha256$" + hashlib.sha256((password + salt).encode('utf-8')).hexdigest()
        return expected == hashed_password
    else:
        # Legacy raw SHA256 check
        salt = "ai_resume_screening_secure_salt_2026"
        legacy = hashlib.sha256((password + salt).encode('utf-8')).hexdigest()
        return legacy == hashed_password


def validate_password_strength(password: str) -> Dict[str, Any]:
    """
    Evaluates password strength and returns rating (Weak, Fair, Good, Strong)
    along with detailed checklist requirement validations.
    """
    if not password:
        return {
            "score": 0,
            "rating": "Weak",
            "is_valid": False,
            "checklist": {
                "min_length": False,
                "has_uppercase": False,
                "has_lowercase": False,
                "has_number": False,
                "has_special": False
            }
        }

    min_length = len(password) >= 8
    has_uppercase = bool(re.search(r'[A-Z]', password))
    has_lowercase = bool(re.search(r'[a-z]', password))
    has_number = bool(re.search(r'\d', password))
    has_special = bool(re.search(r'[!@#$%^&*(),.?":{}|<>]', password))

    score = sum([min_length, has_uppercase, has_lowercase, has_number, has_special])

    if score == 5 and len(password) >= 10:
        rating = "Strong"
    elif score >= 4:
        rating = "Good"
    elif score >= 3:
        rating = "Fair"
    else:
        rating = "Weak"

    is_valid = min_length and has_uppercase and has_lowercase and has_number

    return {
        "score": score,
        "rating": rating,
        "is_valid": is_valid,
        "checklist": {
            "min_length": min_length,
            "has_uppercase": has_uppercase,
            "has_lowercase": has_lowercase,
            "has_number": has_number,
            "has_special": has_special
        }
    }
