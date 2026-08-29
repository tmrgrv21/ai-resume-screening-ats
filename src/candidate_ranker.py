"""
Candidate Ranker Module
Orchestrates end-to-end processing, evaluation, scoring, and ranking of batch candidate resumes.
"""

from typing import List, Dict, Any, Union, Optional
import io
import pandas as pd

from src.resume_parser import ResumeParser
from src.text_preprocessor import preprocess_for_embedding
from src.skill_extractor import SkillExtractor
from src.semantic_matcher import SemanticMatcher
from src.scoring import ScoringEngine


class CandidateRanker:
    """
    Main pipeline execution engine for candidate resume evaluation.
    """

    def __init__(
        self,
        semantic_weight: float = 0.60,
        skill_weight: float = 0.30,
        exp_weight: float = 0.10,
        custom_skills: Optional[List[str]] = None
    ):
        self.skill_extractor = SkillExtractor(custom_skills=custom_skills)
        self.semantic_matcher = SemanticMatcher()
        self.scoring_engine = ScoringEngine(
            semantic_weight=semantic_weight,
            skill_weight=skill_weight,
            exp_weight=exp_weight
        )

    def process_candidates(
        self,
        job_description: str,
        resume_files: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Processes batch resumes against job description.

        Parameters:
            job_description (str): Raw or cleaned text of Job Description.
            resume_files (List[Dict]): List of dicts, each with 'filename' and 'content' (bytes or path).

        Returns:
            Dict containing sorted candidate results list, metadata summary, and pandas DataFrame.
        """
        if not job_description or not job_description.strip():
            raise ValueError("Job Description cannot be empty.")

        if not resume_files:
            raise ValueError("No resume files uploaded for analysis.")

        cleaned_job = preprocess_for_embedding(job_description)
        job_skills_info = self.skill_extractor.extract_skills(job_description)

        processed_results = []
        errors = []

        for idx, item in enumerate(resume_files):
            filename = item.get("filename", f"Resume_{idx+1}")
            file_content = item.get("content")

            try:
                # 1. Parse resume
                parsed_data = ResumeParser.parse_file(file_content, filename)
                raw_text = parsed_data["cleaned_text"]

                # 2. Preprocess text for embedding (with demographic masking)
                prep_resume_text = preprocess_for_embedding(raw_text)

                # 3. Compute Semantic Similarity
                sem_score, sem_method = self.semantic_matcher.compute_similarity(cleaned_job, prep_resume_text)

                # 4. Compare Skills
                skill_comp = self.skill_extractor.compare_skills(job_description, raw_text)

                # 5. Calculate Weighted Score
                score_dict = self.scoring_engine.compute_match(
                    job_text=job_description,
                    semantic_score=sem_score,
                    skill_comparison=skill_comp,
                    candidate_exp_years=parsed_data["experience_years"]
                )

                candidate_record = {
                    "filename": filename,
                    "candidate_name": parsed_data["candidate_name"],
                    "email": parsed_data["email"],
                    "phone": parsed_data["phone"],
                    "overall_match_score": score_dict["overall_match_score"],
                    "semantic_score": score_dict["semantic_score"],
                    "skill_score": score_dict["skill_score"],
                    "exp_score": score_dict["exp_score"],
                    "status": score_dict["status"],
                    "badge_color": score_dict["badge_color"],
                    "matched_skills": skill_comp["matched_skills"],
                    "missing_skills": skill_comp["missing_skills"],
                    "candidate_skills": skill_comp["candidate_skills"],
                    "matched_count": skill_comp["matched_count"],
                    "total_required_count": skill_comp["total_required_count"],
                    "experience_years": parsed_data["experience_years"],
                    "sections": parsed_data["sections"],
                    "raw_text": parsed_data["raw_text"],
                    "sem_method": sem_method,
                    "weights_used": score_dict["weights_used"]
                }

                processed_results.append(candidate_record)

            except Exception as e:
                errors.append({"filename": filename, "error": str(e)})

        # Sort candidates by overall match score descending
        processed_results.sort(key=lambda x: x["overall_match_score"], reverse=True)

        # Assign ranks
        for rank_idx, cand in enumerate(processed_results, start=1):
            cand["rank"] = rank_idx
            cand["rank_str"] = f"#{rank_idx}"

        # Create display dataframe for summary table
        df_summary = pd.DataFrame([
            {
                "Rank": c["rank_str"],
                "Candidate Name": c["candidate_name"],
                "Match Score": f"{c['overall_match_score']:.1f}%",
                "Status": c["status"],
                "Matched Skills": ", ".join(c["matched_skills"][:5]) + ("..." if len(c["matched_skills"]) > 5 else "") if c["matched_skills"] else "None",
                "Missing Skills": ", ".join(c["missing_skills"][:5]) + ("..." if len(c["missing_skills"]) > 5 else "") if c["missing_skills"] else "None",
                "Experience": f"{c['experience_years']} yrs" if c["experience_years"] > 0 else "Not detected",
                "Filename": c["filename"]
            }
            for c in processed_results
        ])

        return {
            "candidates": processed_results,
            "df_summary": df_summary,
            "errors": errors,
            "total_processed": len(processed_results),
            "job_required_skills": job_skills_info
        }

    @staticmethod
    def check_duplicate_candidate(new_email: str, new_phone: str, new_name: str, existing_candidates: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Checks if candidate matching email, phone, or name already exists in talent pool.
        """
        if not existing_candidates:
            return None
        for c in existing_candidates:
            if new_email and new_email != "Not detected" and c.get("email", "").lower() == new_email.lower():
                return {"type": "Email Match", "candidate": c}
            if new_phone and new_phone != "Not detected" and c.get("phone", "") == new_phone:
                return {"type": "Phone Match", "candidate": c}
            if new_name and len(new_name) > 3 and c.get("candidate_name", "").lower() == new_name.lower():
                return {"type": "Name Match", "candidate": c}
        return None
