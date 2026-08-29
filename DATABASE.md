# Database Architecture Documentation

Database Engine: SQLite 3 (`data/app_database.db`)

## Schema Diagrams & Tables

### 1. `users` Table
Stores operational user accounts and RBAC profiles.
- `id` (INTEGER PRIMARY KEY)
- `username` (TEXT UNIQUE)
- `email` (TEXT)
- `password_hash` (TEXT)
- `role` (TEXT: 'Admin', 'Recruiter', 'HiringManager', 'Viewer')
- `created_at` (TIMESTAMP)

### 2. `job_requisitions` Table
Stores open job descriptions and requirements.
- `id` (INTEGER PRIMARY KEY)
- `title` (TEXT)
- `department` (TEXT)
- `location` (TEXT)
- `description` (TEXT)
- `required_experience` (REAL)
- `status` (TEXT: 'Active', 'Closed', 'Archived')
- `created_by` (TEXT)
- `created_at` (TIMESTAMP)

### 3. `candidates` Table
Stores parsed candidate profiles.
- `id` (INTEGER PRIMARY KEY)
- `candidate_name` (TEXT)
- `email` (TEXT)
- `phone` (TEXT)
- `experience_years` (REAL)
- `skills_json` (TEXT)
- `raw_text` (TEXT)
- `filename` (TEXT)
- `created_at` (TIMESTAMP)

### 4. `evaluations` Table
Stores AI screening results and human workflow decisions.
- `id` (INTEGER PRIMARY KEY)
- `requisition_id` (INTEGER FOREIGN KEY)
- `candidate_id` (INTEGER FOREIGN KEY)
- `overall_score` (REAL)
- `semantic_score` (REAL)
- `skill_score` (REAL)
- `exp_score` (REAL)
- `status` (TEXT: 'Under Review', 'Shortlisted', 'Interview Scheduled', 'Hired', 'Rejected', 'Archived')
- `matched_skills_json` (TEXT)
- `missing_skills_json` (TEXT)
- `reviewer_notes` (TEXT)
- `evaluated_at` (TIMESTAMP)

### 5. `audit_logs` Table
Immutable log of system events.
- `id` (INTEGER PRIMARY KEY)
- `user_username` (TEXT)
- `action` (TEXT)
- `resource_type` (TEXT)
- `resource_id` (TEXT)
- `details` (TEXT)
- `ip_address` (TEXT)
- `timestamp` (TIMESTAMP)
