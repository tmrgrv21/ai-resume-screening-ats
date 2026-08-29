"""
Comparison Engine Module
Builds side-by-side comparison matrix for evaluating multiple candidates simultaneously.
"""

from typing import List, Dict, Any
import pandas as pd


class ComparisonEngine:
    """
    Side-by-side candidate comparison matrix builder.
    """

    @staticmethod
    def build_comparison_matrix(candidates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Builds a comprehensive comparison dataset for selected candidates.
        """
        if not candidates:
            return {"metrics_df": pd.DataFrame(), "skill_matrix_df": pd.DataFrame()}

        # 1. Primary Metrics Comparison Table
        metrics_data = []
        for c in candidates:
            metrics_data.append({
                "Metric": c.get("candidate_name", "Unknown"),
                "Overall Score": f"{c.get('overall_match_score', 0.0):.1f}%",
                "Semantic Similarity": f"{c.get('semantic_score', 0.0):.1f}%",
                "Skill Match Score": f"{c.get('skill_score', 0.0):.1f}%",
                "Experience Score": f"{c.get('exp_score', 0.0):.1f}%",
                "Experience Years": f"{c.get('experience_years', 0.0)} yrs",
                "Status": c.get("status", "Under Review"),
                "Matched Count": len(c.get("matched_skills", [])),
                "Missing Count": len(c.get("missing_skills", []))
            })

        metrics_df = pd.DataFrame(metrics_data).set_index("Metric").T

        # 2. Skill Matrix Comparison Grid
        # Collect all unique required/candidate skills across selected candidates
        all_skills = set()
        for c in candidates:
            all_skills.update(c.get("matched_skills", []))
            all_skills.update(c.get("missing_skills", []))

        skill_matrix = []
        for s in sorted(list(all_skills)):
            row = {"Skill": s}
            for c in candidates:
                cand_name = c.get("candidate_name", "Unknown")
                if s in c.get("matched_skills", []):
                    row[cand_name] = "✅ Matched"
                elif s in c.get("missing_skills", []):
                    row[cand_name] = "❌ Missing"
                else:
                    row[cand_name] = "➖ N/A"
            skill_matrix.append(row)

        skill_matrix_df = pd.DataFrame(skill_matrix)

        return {
            "metrics_df": metrics_df,
            "skill_matrix_df": skill_matrix_df
        }
