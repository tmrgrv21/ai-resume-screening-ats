"""
MongoDB Database Manager Module
Handles PyMongo database connection, collection creation, indexing,
data persistence, resilient offline fallback mode, and seed user accounts.
"""

import os
import secrets
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
import pymongo
from pymongo import MongoClient, ASCENDING, DESCENDING

from src.security.password import hash_password, verify_password

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "ai_resume_screening")


class InMemCollection:
    """
    In-Memory PyMongo Collection fallback layer used when MongoDB server is offline.
    Provides PyMongo-compatible find, find_one, insert_one, update_one, delete_many, and count_documents methods.
    """

    def __init__(self, name: str):
        self.name = name
        self.documents = []
        self._id_counter = 1

    def create_index(self, keys, **kwargs):
        pass

    def insert_one(self, doc: Dict[str, Any]):
        doc = dict(doc)
        if "_id" not in doc:
            doc["_id"] = str(self._id_counter)
            self._id_counter += 1
        self.documents.append(doc)

        class Result:
            def __init__(self, inserted_id):
                self.inserted_id = inserted_id

        return Result(doc["_id"])

    def find_one(self, filter_dict: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        docs = self.find(filter_dict)
        return docs[0] if docs else None

    def find(self, filter_dict: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        if not filter_dict:
            return [dict(d) for d in self.documents]

        results = []
        for doc in self.documents:
            match = True
            for k, v in filter_dict.items():
                if k == "$or" and isinstance(v, list):
                    or_match = any(self._check_condition(doc, cond) for cond in v)
                    if not or_match:
                        match = False
                        break
                elif not self._check_condition(doc, {k: v}):
                    match = False
                    break
            if match:
                results.append(dict(doc))
        return results

    def _check_condition(self, doc: Dict[str, Any], cond: Dict[str, Any]) -> bool:
        for k, v in cond.items():
            doc_val = doc.get(k)
            if isinstance(v, dict):
                for op, val in v.items():
                    if op == "$gte" and not (doc_val and doc_val >= val):
                        return False
                    elif op == "$lte" and not (doc_val and doc_val <= val):
                        return False
                    elif op == "$in" and not (doc_val in val):
                        return False
            elif doc_val != v:
                return False
        return True

    def update_one(self, filter_dict: Dict[str, Any], update_dict: Dict[str, Any]):
        target = self.find_one(filter_dict)
        if target:
            idx = next(i for i, d in enumerate(self.documents) if d["_id"] == target["_id"])
            if "$set" in update_dict:
                for k, v in update_dict["$set"].items():
                    self.documents[idx][k] = v

    def delete_many(self, filter_dict: Dict[str, Any]):
        self.documents = [d for d in self.documents if not self._check_condition(d, filter_dict)]

    def count_documents(self, filter_dict: Dict[str, Any]) -> int:
        return len(self.find(filter_dict))


class MongoManager:
    """
    Enterprise MongoDB Database & Repository Layer.
    """

    def __init__(self, uri: str = MONGODB_URI, db_name: str = MONGODB_DATABASE):
        self.uri = uri
        self.db_name = db_name
        self.is_offline = False
        self._collections = {}

        try:
            self.client = MongoClient(self.uri, serverSelectionTimeoutMS=2000)
            # Test connection
            self.client.admin.command('ping')
            self.db = self.client[self.db_name]
            self._create_indexes()
        except Exception as e:
            # Fall back to in-memory collection mode for reliable testing/offline environment
            self.is_offline = True
            self.client = None
            self.db = None

        self.seed_users()

    def get_collection(self, collection_name: str):
        """Returns PyMongo collection or in-memory fallback collection."""
        if not self.is_offline and self.db is not None:
            return self.db[collection_name]
        else:
            if collection_name not in self._collections:
                self._collections[collection_name] = InMemCollection(collection_name)
            return self._collections[collection_name]

    def _create_indexes(self):
        """Creates unique and non-unique MongoDB indexes across collections."""
        try:
            # Users
            users_col = self.db["users"]
            users_col.create_index("username", unique=True)
            users_col.create_index("email", unique=True)
            users_col.create_index("role")

            # Sessions
            sessions_col = self.db["sessions"]
            sessions_col.create_index("session_token_hash", unique=True)
            sessions_col.create_index([("user_id", ASCENDING), ("is_active", ASCENDING)])
            sessions_col.create_index("expires_at")

            # Resets & Verifications
            self.db["password_resets"].create_index("token_hash", unique=True)
            self.db["email_verifications"].create_index("token_hash", unique=True)

            # Audit Logs
            self.db["audit_logs"].create_index([("user_username", ASCENDING), ("timestamp", DESCENDING)])
        except Exception as e:
            print(f"Index creation warning: {e}")

    def seed_users(self):
        """Seeds default operational demo user accounts into MongoDB users collection."""
        default_users = [
            {
                "username": "admin",
                "full_name": "System Administrator",
                "email": "admin@company.com",
                "password_hash": hash_password("admin123"),
                "role": "admin",
                "status": "active",
                "email_verified": True,
                "created_at": datetime.now()
            },
            {
                "username": "recruiter",
                "full_name": "Lead Recruiter",
                "email": "recruiter@company.com",
                "password_hash": hash_password("recruiter123"),
                "role": "recruiter",
                "status": "active",
                "email_verified": True,
                "created_at": datetime.now()
            },
            {
                "username": "hiring_manager",
                "full_name": "Engineering Hiring Manager",
                "email": "manager@company.com",
                "password_hash": hash_password("manager123"),
                "role": "hiring_manager",
                "status": "active",
                "email_verified": True,
                "created_at": datetime.now()
            },
            {
                "username": "viewer",
                "full_name": "Guest Viewer",
                "email": "viewer@company.com",
                "password_hash": hash_password("viewer123"),
                "role": "viewer",
                "status": "active",
                "email_verified": True,
                "created_at": datetime.now()
            }
        ]

        users_col = self.get_collection("users")
        for u in default_users:
            existing = users_col.find_one({"username": u["username"]})
            if not existing:
                users_col.insert_one(u)

    # --------------------------------------------------
    # AUDIT LOGGING HELPER
    # --------------------------------------------------
    def log_audit(self, user_username: str, action: str, resource_type: str, resource_id: str = "", details: str = "", ip_address: str = "127.0.0.1"):
        """Logs security audit event to MongoDB audit_logs collection."""
        audit_col = self.get_collection("audit_logs")
        audit_col.insert_one({
            "user_username": user_username,
            "action": action,
            "resource_type": resource_type,
            "resource_id": str(resource_id),
            "details": details,
            "ip_address": ip_address,
            "timestamp": datetime.now()
        })

    def get_audit_logs(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Retrieves recent audit logs."""
        audit_col = self.get_collection("audit_logs")
        logs = list(audit_col.find())
        # Sort descending by timestamp
        logs.sort(key=lambda x: x.get("timestamp", datetime.now()), reverse=True)
        return logs[:limit]
