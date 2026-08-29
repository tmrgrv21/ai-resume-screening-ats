"""
Explainability & AI Justification Engine
Generates human-readable explanations, key strength callouts, risk flags,
and tailored technical interview questions based on screening results.
"""

from typing import Dict, Any, List


class ExplainabilityEngine:
    """
    Generates transparent match justifications and candidate-specific interview questions.
    """

    @staticmethod
    def generate_match_explanation(candidate: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generates structured explanation dictionary detailing why the candidate received their score.
        """
        score = candidate.get("overall_match_score", 0.0)
        matched_skills = candidate.get("matched_skills", [])
        missing_skills = candidate.get("missing_skills", [])
        exp_years = candidate.get("experience_years", 0.0)

        # 1. Summary Headline
        if score >= 85.0:
            summary = f"Exceptional candidate match ({score:.1f}%). Highly aligned in both core technical skills and domain experience."
        elif score >= 70.0:
            summary = f"Strong candidate match ({score:.1f}%). Possesses majority of core required technical competencies."
        elif score >= 50.0:
            summary = f"Potential match ({score:.1f}%). Demonstrates relevant background with a few missing technical prerequisites."
        else:
            summary = f"Low match ({score:.1f}%). Significant skill gaps identified relative to job description requirements."

        # 2. Key Strengths
        strengths = []
        if matched_skills:
            strengths.append(f"Demonstrated proficiency in {len(matched_skills)} required skills: {', '.join(matched_skills[:5])}.")
        if exp_years > 0:
            strengths.append(f"Has approximately {exp_years} years of relevant professional experience.")

        # 3. Missing Prerequisites / Risk Areas
        gaps = []
        if missing_skills:
            gaps.append(f"Missing explicit resume evidence for {len(missing_skills)} required skills: {', '.join(missing_skills[:5])}.")
        if exp_years < 2.0:
            gaps.append("Lower total years of professional work experience detected.")

        return {
            "headline": summary,
            "key_strengths": strengths if strengths else ["No major strengths detected."],
            "identified_gaps": gaps if gaps else ["All required core skills are present in resume."]
        }

    @staticmethod
    def generate_interview_questions(candidate: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Generates candidate-specific technical interview questions based on matched and missing skills.
        """
        questions = []
        matched = candidate.get("matched_skills", [])
        missing = candidate.get("missing_skills", [])

        # Questions for top matched skills
        if "Python" in matched:
            questions.append({
                "topic": "Python Core & Architecture",
                "question": "Can you explain how GIL impacts multi-threading in Python, and how you design asynchronous pipelines?",
                "target_type": "Matched Skill Verification"
            })
        if "PyTorch" in matched or "TensorFlow" in matched:
            questions.append({
                "topic": "Deep Learning Models",
                "question": "Walk us through how you prevent model overfitting during training and optimize batch size for GPU inference.",
                "target_type": "Matched Skill Verification"
            })
        if "Docker" in matched or "Kubernetes" in matched:
            questions.append({
                "topic": "DevOps & Containerization",
                "question": "How do you optimize Docker image layer sizes and manage secrets in production Kubernetes clusters?",
                "target_type": "Matched Skill Verification"
            })

        # Probe questions for missing skills
        for m_skill in missing[:3]:
            questions.append({
                "topic": f"Skill Gap Probe: {m_skill}",
                "question": f"The job description requires {m_skill}. Do you have practical project experience with {m_skill} or related toolings?",
                "target_type": "Missing Skill Probe"
            })

        if not questions:
            questions.append({
                "topic": "General Engineering",
                "question": "Can you walk us through the most challenging technical project you built recently and your architectural choices?",
                "target_type": "General Competency"
            })

        return questions
