"""
Skill Extractor Module
Extracts technical and soft skills from job descriptions and resumes using an extensible
taxonomy dictionary and exact/regex boundary matching.
"""

import re
from typing import List, Dict, Set, Tuple, Any, Optional

# Comprehensive Default Skill Taxonomy
DEFAULT_SKILL_DICTIONARY = {
    "Programming Languages": [
        "Python", "Java", "C++", "C#", "C", "JavaScript", "TypeScript",
        "Go", "Golang", "Rust", "R", "PHP", "Ruby", "Swift", "Kotlin", "Scala", "SQL", "HTML", "CSS", "Bash"
    ],
    "Frameworks & Libraries": [
        "React", "React Native", "Angular", "Vue", "Vue.js", "Node.js", "Express", "Django", "Flask",
        "FastAPI", "Spring Boot", "ASP.NET", ".NET", "PyTorch", "TensorFlow", "Keras",
        "Scikit-learn", "Pandas", "NumPy", "OpenCV", "SpaCy", "NLTK", "HuggingFace", "Transformers",
        "Tailwind", "Bootstrap", "Redux", "Next.js"
    ],
    "Databases & Storage": [
        "MySQL", "PostgreSQL", "SQLite", "MongoDB", "Redis", "Elasticsearch", "Cassandra",
        "DynamoDB", "Firebase", "Oracle", "SQL Server", "Snowflake", "Neo4j"
    ],
    "Cloud & DevOps": [
        "AWS", "Azure", "GCP", "Google Cloud", "Docker", "Kubernetes", "K8s", "Jenkins",
        "GitLab CI", "GitHub Actions", "Terraform", "Ansible", "Linux", "Nginx", "CI/CD"
    ],
    "AI & Data Science": [
        "Machine Learning", "Deep Learning", "NLP", "Natural Language Processing",
        "Computer Vision", "Generative AI", "LLM", "RAG", "BERT", "GPT",
        "Neural Networks", "Reinforcement Learning", "Data Mining", "Feature Engineering",
        "Time Series", "MLOps", "Model Deployment"
    ],
    "Tools & Analytics": [
        "Git", "GitHub", "Jira", "Confluence", "Postman", "Power BI", "Tableau", "Excel", "Spark", "Kafka", "Airflow"
    ],
    "Methodologies & Soft Skills": [
        "Agile", "Scrum", "REST API", "Microservices", "System Design", "OOP",
        "Problem Solving", "Leadership", "Communication", "Teamwork"
    ]
}


class SkillExtractor:
    """
    Skill extraction and matching engine.
    """

    def __init__(self, custom_skills: Optional[List[str]] = None):
        """
        Initializes the skill extractor with default and optional custom skills.
        """
        self.skill_map = {}  # Normalized lowercase skill -> Canonical Skill Display Name
        self.category_map = {}

        self._build_taxonomy(custom_skills)

    def _build_taxonomy(self, custom_skills: Optional[List[str]] = None):
        """Populates skill maps for fast case-insensitive lookups."""
        for cat, skills in DEFAULT_SKILL_DICTIONARY.items():
            for skill in skills:
                norm = skill.lower()
                self.skill_map[norm] = skill
                self.category_map[norm] = cat

        if custom_skills:
            for skill in custom_skills:
                norm = skill.strip().lower()
                if norm and norm not in self.skill_map:
                    self.skill_map[norm] = skill.strip()
                    self.category_map[norm] = "Custom Skills"

    def extract_skills(self, text: str) -> List[str]:
        """
        Extracts matched skills from text using boundary matching.
        """
        if not text:
            return []

        extracted = set()

        for norm_skill, canonical in self.skill_map.items():
            # Handle special symbols like C++, C#, .NET
            escaped = re.escape(norm_skill)

            # Build regex with word boundary protections
            if norm_skill in ['c++', 'c#', '.net']:
                pattern = r'(?:^|[\s,;/()\[\]])' + escaped + r'(?:$|[\s,;/()\[\]])'
            elif len(norm_skill) <= 2:
                # Very short skills (e.g. R, Go, C, AI) require strict boundaries
                pattern = r'\b' + escaped + r'\b'
            else:
                pattern = r'\b' + escaped + r'\b'

            if re.search(pattern, text, flags=re.IGNORECASE):
                extracted.add(canonical)

        return sorted(list(extracted))

    def compare_skills(self, job_text: str, resume_text: str) -> Dict[str, Any]:
        """
        Compares skills present in Job Description against candidate resume.
        Returns matched, missing, and extra skills along with a match score (0-100%).
        """
        required_skills = set(self.extract_skills(job_text))
        candidate_skills = set(self.extract_skills(resume_text))

        if not required_skills:
            # If no skills recognized in job description, fall back to candidate skills
            matched_skills = candidate_skills
            missing_skills = set()
            skill_score = 100.0 if candidate_skills else 50.0
        else:
            matched_skills = required_skills.intersection(candidate_skills)
            missing_skills = required_skills.difference(candidate_skills)
            skill_score = (len(matched_skills) / len(required_skills)) * 100.0

        return {
            "required_skills": sorted(list(required_skills)),
            "candidate_skills": sorted(list(candidate_skills)),
            "matched_skills": sorted(list(matched_skills)),
            "missing_skills": sorted(list(missing_skills)),
            "skill_match_score": round(skill_score, 2),
            "matched_count": len(matched_skills),
            "total_required_count": len(required_skills)
        }
