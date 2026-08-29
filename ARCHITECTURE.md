# Enterprise Architecture Documentation

## System Architecture Overview

The **AI Resume Screening & Talent Intelligence Platform** is structured into a 5-layer modular architecture:

```
[ User Interface (Streamlit Portal) ]
               │
[ REST API Interface (FastAPI v1) ]
               │
[ Business Logic & ML Core ]
 (Parser | Preprocessor | Skill Engine | Embeddings | Scoring)
               │
[ Governance & Decision Layer ]
 (RBAC Auth | State Machine | Explainability | Comparison)
               │
[ Relational Data Persistence (SQLite DB Manager) ]
```

## Layer Descriptions

1. **Presentation Layer (`app.py`)**: Role-aware Streamlit web interface with responsive dark mode, operational dashboard, candidate leaderboard, Plotly chart analytics, and candidate inspector.
2. **API Interface (`api.py`)**: FastAPI RESTful application exposing versioned `/api/v1` endpoints for external ATS integration.
3. **Core ML Layer (`src/`)**:
   - `resume_parser.py`: PDF/DOCX/TXT text and metadata extractor.
   - `text_preprocessor.py`: Text cleaner and demographic bias masking engine.
   - `skill_extractor.py`: Taxonomy dictionary and regex boundary matcher.
   - `semantic_matcher.py`: SentenceTransformer embedding similarity with TF-IDF fallback.
   - `scoring.py`: Multi-factor transparent scoring engine.
   - `explainability.py`: Match justification and technical interview question generator.
   - `comparison.py`: Multi-candidate matrix comparison tool.
   - `report_generator.py`: PDF/HTML evaluation report generator.
4. **Data Persistence (`src/database/`)**: Relational SQLite database manager storing `users`, `job_requisitions`, `candidates`, `evaluations`, and `audit_logs`.
5. **Governance (`src/auth.py` & `src/workflow.py`)**: RBAC permission checks, candidate lifecycle state machine, and audit trail logging.
