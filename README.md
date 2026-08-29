# AI Resume Screening System 🚀

An enterprise-grade, end-to-end AI-powered recruitment application that evaluates candidate resumes against job descriptions using SentenceTransformer embeddings (`sentence-transformers/all-MiniLM-L6-v2`), transparent multi-factor scoring, skill gap analysis, and interactive visual analytics.

---

## 📌 Project Overview

Recruiters and hiring managers often receive hundreds of candidate resumes for every open position. Manual screening is time-consuming, inconsistent, and susceptible to unconscious bias. 

The **AI Resume Screening System** automates the initial screening phase by semantically understanding the candidate's resume content, extracting technical skills, matching against job requirements, and generating a transparent, reproducible **Resume–Job Match Score (0–100%)**.

---

## 🎯 Key Objectives

1. **Automate Document Parsing**: Extract text cleanly from PDF, DOCX, and TXT resume formats.
2. **Semantic NLP Matching**: Use dense vector representations to capture context and semantic alignment beyond keyword matching.
3. **Skill Taxonomy Engine**: Compare required skills vs candidate skills to reveal matched and missing skills.
4. **Transparent Scoring**: Multi-factor scoring formula combining Semantic Similarity, Skill Coverage, and Experience Relevance.
5. **Responsible & Fair AI**: Mask demographic details (gender, age, marital status) to eliminate bias and enforce human-in-the-loop decision making.
6. **Executive Visual Dashboard**: Provide recruiters with interactive Plotly charts, candidate inspector tabs, and CSV data export capabilities.

---

## 🛠️ Technology Stack

- **Core Language**: Python 3.10+
- **Machine Learning & NLP**: `sentence-transformers`, `transformers`, `torch`, `scikit-learn`, `numpy`, `pandas`, `spaCy`
- **Document Extractors**: `pypdf`, `python-docx`
- **Frontend Dashboard**: `Streamlit`
- **Data Visualization**: `Plotly`
- **Testing**: `pytest`

---

## 🏗️ Architecture & Project Structure

```
ai-resume-screening/
│
├── app.py                      # Main Streamlit Dashboard Application
├── requirements.txt            # Project Dependencies
├── README.md                   # Complete Documentation
├── .gitignore                  # Git Ignore Configuration
├── .env.example                # Environment Variable Template
│
├── data/
│   └── sample/                 # Sample Job Description & Resumes (PDF, DOCX, TXT)
│       ├── job_description.txt
│       ├── alex_rivera_senior_ml.txt
│       ├── sarah_chen_data_analyst.txt
│       └── michael_scott_frontend.txt
│
├── src/                        # Core NLP & ML Modules
│   ├── __init__.py
│   ├── text_preprocessor.py    # Text cleaning & demographic info masking
│   ├── resume_parser.py        # PDF/DOCX/TXT text & metadata extractor
│   ├── skill_extractor.py      # Skill taxonomy & regex matcher
│   ├── semantic_matcher.py     # SentenceTransformer embeddings & cosine similarity
│   ├── scoring.py              # Multi-factor transparent scoring engine
│   ├── candidate_ranker.py     # End-to-end pipeline & candidate ranker
│   └── utils.py                # CSV export helper & custom dark-mode CSS
│
└── tests/                      # Automated Unit Test Suite
    ├── test_parser.py          # Document parsing tests
    ├── test_matching.py        # Skill & semantic similarity tests
    └── test_scoring.py         # Scoring & ranking pipeline tests
```

---

## 🧠 ML Methodology & Scoring Architecture

### 1. Vector Embeddings
Each resume text $T_{\text{resume}}$ and job description $T_{\text{job}}$ is preprocessed, sanitized, and encoded into dense vector embeddings using the `sentence-transformers/all-MiniLM-L6-v2` transformer model:

$$E_{\text{job}} = \text{Encoder}(T_{\text{job}}), \quad E_{\text{resume}} = \text{Encoder}(T_{\text{resume}})$$

Cosine similarity between the normalized vectors yields the raw **Semantic Similarity Score**:

$$\text{Semantic Similarity} = \max\left(0, \frac{E_{\text{job}} \cdot E_{\text{resume}}}{\|E_{\text{job}}\| \|E_{\text{resume}}\|}\right) \times 100$$

*Fallback Engine*: If SentenceTransformer model weights cannot be downloaded, a TF-IDF N-gram cosine similarity engine is used automatically.

### 2. Multi-Factor Transparent Composite Score

$$\text{Overall Match Score} = \left( w_{\text{semantic}} \times S_{\text{semantic}} \right) + \left( w_{\text{skill}} \times S_{\text{skill}} \right) + \left( w_{\text{exp}} \times S_{\text{exp}} \right)$$

Default Weights (Configurable in Sidebar):
- **Semantic Weight ($w_{\text{semantic}}$)**: 60%
- **Skill Weight ($w_{\text{skill}}$)**: 30%
- **Experience Weight ($w_{\text{exp}}$)**: 10%

---

## 🚀 Installation & Setup

### Prerequisites
- Python 3.10 or higher
- Git

### 1. Clone & Install Dependencies
```bash
git clone https://github.com/your-username/ai-resume-screening.git
cd ai-resume-screening
pip install -r requirements.txt
```

---

## 💻 How to Run the Application

Launch the Streamlit dashboard:
```bash
streamlit run app.py
```
The application will open automatically in your browser at `http://localhost:8501`.

### 1-Click Quick Demo
1. Open the application.
2. In the left sidebar under **🧪 Quick Demo**, click **"Load Demo Job & Sample Resumes"**.
3. Click the main button **🚀 Analyze Resumes**.
4. Explore candidate rankings, skill coverage, Plotly charts, and export CSV results.

---

## 🧪 Running Automated Tests

Run the complete pytest test suite:
```bash
pytest tests/ -v
```

---

## ⚖️ Responsible AI & Demographic Fairness

- **Demographic Information Masking**: The text preprocessor automatically masks protected attributes (gender cues, age indicators, marital status, religion/nationality labels) before generating embeddings.
- **Decision-Support Signal**: The screening score is explicitly labeled as a **Resume–Job Match Score**, not a hiring probability or guarantee.
- **Human-in-the-Loop**: A prominent disclaimer reminds recruiters that AI scores are decision-support signals and human review is required.

---

## 🔮 Future Improvements

- Add support for multilingual resume parsing.
- Integrate OCR support (Tesseract) for scanned image resumes.
- Provide vector database storage (ChromaDB / Pinecone) for persistent candidate search across large enterprise talent pools.
