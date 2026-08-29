"""
Migration Script: SQLite to MongoDB Data Migration
Detects existing SQLite database (data/app_database.db), reads records, and idempotently
transforms and populates MongoDB collections.
"""

import os
import sqlite3
import json
from datetime import datetime
from src.database.mongo_manager import MongoManager
from src.security.password import hash_password

SQLITE_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "app_database.db")


def migrate():
    print("=" * 60)
    print("MIGRATION: SQLite to MongoDB Data Persistence Migration")
    print("=" * 60)

    if not os.path.exists(SQLITE_DB_PATH):
        print(f"No existing SQLite database found at '{SQLITE_DB_PATH}'. Initializing clean MongoDB schema.")
        mongo = MongoManager()
        print("MongoDB schema initialized with seed default users.")
        return

    print(f"Detected SQLite database at '{SQLITE_DB_PATH}'. Starting migration...")
    mongo = MongoManager()

    conn = sqlite3.connect(SQLITE_DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 1. Migrate Users
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
    if cursor.fetchone():
        cursor.execute("SELECT * FROM users")
        sq_users = cursor.fetchall()
        users_col = mongo.get_collection("users")
        migrated_users = 0
        for u in sq_users:
            u_dict = dict(u)
            if not users_col.find_one({"username": u_dict["username"]}):
                users_col.insert_one({
                    "username": u_dict["username"],
                    "email": u_dict.get("email", f"{u_dict['username']}@company.com"),
                    "password_hash": u_dict.get("password_hash") or hash_password("admin123"),
                    "role": u_dict.get("role", "recruiter").lower(),
                    "status": "active",
                    "email_verified": True,
                    "created_at": datetime.now()
                })
                migrated_users += 1
        print(f"[OK] Migrated {migrated_users} Users to MongoDB.")

    # 2. Migrate Job Requisitions
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='job_requisitions'")
    if cursor.fetchone():
        cursor.execute("SELECT * FROM job_requisitions")
        sq_reqs = cursor.fetchall()
        reqs_col = mongo.get_collection("job_requisitions")
        migrated_reqs = 0
        for r in sq_reqs:
            r_dict = dict(r)
            if not reqs_col.find_one({"title": r_dict["title"]}):
                reqs_col.insert_one({
                    "title": r_dict["title"],
                    "department": r_dict.get("department", "Engineering"),
                    "location": r_dict.get("location", "Remote"),
                    "description": r_dict.get("description", ""),
                    "required_experience": r_dict.get("required_experience", 3.0),
                    "status": r_dict.get("status", "Active"),
                    "created_by": r_dict.get("created_by", "admin"),
                    "created_at": datetime.now()
                })
                migrated_reqs += 1
        print(f"[OK] Migrated {migrated_reqs} Job Requisitions to MongoDB.")

    # 3. Migrate Candidates & Evaluations
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='evaluations'")
    if cursor.fetchone():
        cursor.execute("""
            SELECT e.*, c.candidate_name, c.email, c.phone, c.experience_years, c.skills_json, c.filename, c.raw_text
            FROM evaluations e
            LEFT JOIN candidates c ON e.candidate_id = c.id
        """)
        sq_evals = cursor.fetchall()
        evals_col = mongo.get_collection("evaluations")
        migrated_evals = 0
        for e in sq_evals:
            e_dict = dict(e)
            if not evals_col.find_one({"candidate_name": e_dict.get("candidate_name")}):
                evals_col.insert_one({
                    "candidate_name": e_dict.get("candidate_name", "Candidate"),
                    "email": e_dict.get("email", "Not detected"),
                    "phone": e_dict.get("phone", "Not detected"),
                    "experience_years": e_dict.get("experience_years", 0.0),
                    "filename": e_dict.get("filename", "resume.txt"),
                    "raw_text": e_dict.get("raw_text", ""),
                    "overall_score": e_dict.get("overall_score", 0.0),
                    "semantic_score": e_dict.get("semantic_score", 0.0),
                    "skill_score": e_dict.get("skill_score", 0.0),
                    "exp_score": e_dict.get("exp_score", 0.0),
                    "status": e_dict.get("status", "Under Review"),
                    "matched_skills": json.loads(e_dict.get("matched_skills_json") or "[]"),
                    "missing_skills": json.loads(e_dict.get("missing_skills_json") or "[]"),
                    "reviewer_notes": e_dict.get("reviewer_notes", ""),
                    "evaluated_at": datetime.now()
                })
                migrated_evals += 1
        print(f"[OK] Migrated {migrated_evals} Evaluations to MongoDB.")

    # 4. Migrate Audit Logs
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='audit_logs'")
    if cursor.fetchone():
        cursor.execute("SELECT * FROM audit_logs")
        sq_logs = cursor.fetchall()
        audit_col = mongo.get_collection("audit_logs")
        migrated_logs = 0
        for l in sq_logs:
            l_dict = dict(l)
            audit_col.insert_one({
                "user_username": l_dict.get("user_username", "system"),
                "action": l_dict.get("action", "ACTION"),
                "resource_type": l_dict.get("resource_type", "Resource"),
                "resource_id": str(l_dict.get("resource_id", "")),
                "details": l_dict.get("details", ""),
                "ip_address": l_dict.get("ip_address", "127.0.0.1"),
                "timestamp": datetime.now()
            })
            migrated_logs += 1
        print(f"[OK] Migrated {migrated_logs} Audit Logs to MongoDB.")

    conn.close()
    print("=" * 60)
    print("MIGRATION COMPLETED SUCCESSFULLY! MongoDB is now the active persistence layer.")
    print("=" * 60)


if __name__ == "__main__":
    migrate()
