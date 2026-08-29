# Security & Responsible AI Documentation

## Security Architecture

1. **Authentication & Password Protection**:
   - Passwords are encrypted using SHA-256 with a unique salt (`hashlib`). Plaintext credentials are never saved or exposed.
2. **Role-Based Access Control (RBAC)**:
   - System enforces permissions at the backend layer (`AuthManager`). Role profiles: `Admin`, `Recruiter`, `HiringManager`, `Viewer`.
3. **SQL Injection Protection**:
   - All SQLite queries use parameterized prepared statements (`?` bindings).
4. **Input Sanitization & File Upload Safety**:
   - Uploaded files (PDF, DOCX, TXT) are inspected for extensions, text length, and valid UTF-8 character bounds before parsing.
5. **Audit Trail Governance**:
   - Critical system actions (User login, evaluation creation, status updates) write immutable records to the `audit_logs` table.

## Responsible AI & Fair Screening Policy

1. **Demographic Info Masking**:
   - Text preprocessor automatically masks protected attributes (gender indicators, age, date of birth, marital status, religion) before generating vector embeddings.
2. **Human-in-the-Loop Requirement**:
   - AI screening scores are decision-support signals. The system requires human recruiter review and manual status confirmation for all candidate decisions.
