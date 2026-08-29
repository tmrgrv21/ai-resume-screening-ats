# REST API Documentation (v1)

Base URL: `http://localhost:8000/api/v1`

## Endpoints

### 1. Health Check
`GET /api/v1/health`
Returns real-time status of system services.

**Response:**
```json
{
  "status": "operational",
  "version": "1.0.0",
  "services": {
    "api": "Operational",
    "database": "Operational",
    "storage": "Operational",
    "ml_engine": "Operational"
  }
}
```

### 2. User Authentication
`POST /api/v1/auth/login`
Authenticates recruiter credentials.

**Payload:**
```json
{
  "username": "recruiter",
  "password": "recruiter123"
}
```

### 3. Screen Resumes Batch
`POST /api/v1/screen`
Performs AI screening on uploaded resumes against a job description.

**Payload:**
```json
{
  "job_description": "Seeking Senior AI Engineer with Python, PyTorch, Docker...",
  "resumes": [
    { "filename": "alex_rivera.txt", "content": "..." }
  ],
  "semantic_weight": 0.6,
  "skill_weight": 0.3,
  "exp_weight": 0.1
}
```

### 4. Candidate Database List
`GET /api/v1/candidates`
Returns all persistent candidate evaluations stored in database.

### 5. Candidate PDF/HTML Evaluation Report
`GET /api/v1/reports/{eval_id}/html`
Returns executive HTML evaluation brief for the specified candidate evaluation ID.
