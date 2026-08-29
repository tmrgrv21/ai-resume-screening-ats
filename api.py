"""
FastAPI REST API v1
Exposes enterprise endpoints for candidate screening, talent pool data access,
authentication, session management, and system governance.
"""

from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Header, UploadFile, File, Form, Depends, Query, Request
from pydantic import BaseModel, EmailStr

from src.database.db_manager import DatabaseManager
from src.auth import AuthManager
from src.candidate_ranker import CandidateRanker
from src.workflow import WorkflowEngine

app = FastAPI(
    title="AI Resume Screening Enterprise API",
    description="RESTful microservice for AI candidate ranking, semantic evaluation, and RBAC governance.",
    version="1.0.0"
)

# Initialize Core Services
db = DatabaseManager()
auth_mgr = AuthManager(db)
workflow_mgr = WorkflowEngine(db)


# ----------------------------------------------------
# PYDANTIC SCHEMAS
# ----------------------------------------------------
class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str
    role: Optional[str] = "recruiter"
    full_name: Optional[str] = ""
    organization: Optional[str] = ""

class LoginRequest(BaseModel):
    username_or_email: str
    password: str

class ForgotPasswordRequest(BaseModel):
    email: str

class ResetPasswordRequest(BaseModel):
    reset_token: str
    new_password: str

class StatusUpdateRequest(BaseModel):
    eval_id: str
    status: str
    notes: Optional[str] = ""


# ----------------------------------------------------
# AUTHENTICATION ENDPOINTS
# ----------------------------------------------------
@app.post("/api/v1/auth/register", tags=["Authentication"])
def register_user(req: RegisterRequest):
    success, msg = auth_mgr.register(
        username=req.username,
        email=req.email,
        password=req.password,
        role=req.role,
        full_name=req.full_name,
        organization=req.organization
    )
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    return {"message": msg, "username": req.username, "role": req.role}


@app.post("/api/v1/auth/login", tags=["Authentication"])
def login_user(req: LoginRequest, request: Request):
    ip_addr = request.client.host if request.client else "127.0.0.1"
    ua = request.headers.get("user-agent", "FastAPI Client")

    success, user_data, err_msg = auth_mgr.login(
        identifier=req.username_or_email,
        password=req.password,
        user_agent=ua,
        ip_address=ip_addr
    )
    if not success:
        raise HTTPException(status_code=401, detail=err_msg)
    return user_data


@app.post("/api/v1/auth/logout", tags=["Authentication"])
def logout_user(x_session_token: Optional[str] = Header(None)):
    if x_session_token:
        auth_mgr.logout(x_session_token)
    return {"message": "Successfully logged out."}


@app.post("/api/v1/auth/forgot-password", tags=["Authentication"])
def forgot_password(req: ForgotPasswordRequest):
    _, msg, dev_token = auth_mgr.security_service.create_password_reset_token(req.email)
    return {"message": msg, "dev_reset_token": dev_token}


@app.post("/api/v1/auth/reset-password", tags=["Authentication"])
def reset_password(req: ResetPasswordRequest):
    success, msg = auth_mgr.security_service.reset_password_with_token(req.reset_token, req.new_password)
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    return {"message": msg}


# ----------------------------------------------------
# SCREENING & TALENT POOL ENDPOINTS
# ----------------------------------------------------
@app.get("/api/v1/health", tags=["System"])
def health_check():
    return {
        "status": "healthy",
        "database": "MongoDB Operational",
        "service": "AI Resume Screening API v1"
    }


@app.get("/api/v1/candidates", tags=["Candidates"])
def list_candidates():
    return db.get_all_evaluations()


@app.post("/api/v1/candidates/status", tags=["Candidates"])
def update_candidate_status(req: StatusUpdateRequest):
    success = db.update_evaluation_status(req.eval_id, req.status, req.notes or "")
    if not success:
        raise HTTPException(status_code=404, detail="Candidate evaluation not found.")
    return {"message": "Status updated successfully.", "eval_id": req.eval_id, "new_status": req.status}


@app.get("/api/v1/audit-logs", tags=["Governance"])
def get_audit_logs(limit: int = Query(50, ge=1, le=500)):
    return db.get_audit_logs(limit=limit)
