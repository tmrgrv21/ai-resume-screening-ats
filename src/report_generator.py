"""
Report Generator Module
Generates executive evaluation report briefs for candidate screening results.
"""

from typing import Dict, Any


class ReportGenerator:
    """
    Generates structured executive PDF / HTML report briefs.
    """

    @staticmethod
    def generate_html_report(candidate: Dict[str, Any]) -> str:
        """
        Generates a styled, printable HTML evaluation report brief for a candidate.
        """
        cand_name = candidate.get("candidate_name", "Candidate")
        score = candidate.get("overall_match_score", 0.0)
        status = candidate.get("status", "Under Review")
        email = candidate.get("email", "N/A")
        phone = candidate.get("phone", "N/A")
        exp_yrs = candidate.get("experience_years", 0.0)
        filename = candidate.get("filename", "N/A")

        matched = candidate.get("matched_skills", [])
        missing = candidate.get("missing_skills", [])
        notes = candidate.get("reviewer_notes", "No notes recorded.")

        matched_html = "".join([f'<li style="color:#10B981;">{s}</li>' for s in matched]) if matched else "<li>None</li>"
        missing_html = "".join([f'<li style="color:#EF4444;">{s}</li>' for s in missing]) if missing else "<li>None</li>"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Candidate Evaluation Brief - {cand_name}</title>
            <style>
                body {{ font-family: 'Helvetica', 'Arial', sans-serif; color: #1E293B; margin: 30px; background: #FFFFFF; }}
                .header {{ border-bottom: 2px solid #6366F1; padding-bottom: 15px; margin-bottom: 25px; }}
                .title {{ font-size: 24px; font-weight: bold; color: #1E1B4B; }}
                .subtitle {{ font-size: 14px; color: #64748B; margin-top: 5px; }}
                .badge {{ display: inline-block; padding: 6px 12px; border-radius: 6px; font-weight: bold; color: white; background-color: #6366F1; }}
                .grid {{ display: flex; margin-bottom: 20px; }}
                .col {{ flex: 1; padding: 10px; background: #F8FAFC; border-radius: 8px; margin-right: 15px; }}
                .section-title {{ font-size: 16px; font-weight: bold; margin-top: 20px; border-bottom: 1px solid #E2E8F0; padding-bottom: 5px; }}
                ul {{ margin-top: 5px; padding-left: 20px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <div class="title">AI Candidate Evaluation Brief</div>
                <div class="subtitle">AI Resume Screening System — Decision Support Signal</div>
            </div>

            <div class="grid">
                <div class="col">
                    <h3>Candidate Information</h3>
                    <p><b>Name:</b> {cand_name}</p>
                    <p><b>Email:</b> {email}</p>
                    <p><b>Phone:</b> {phone}</p>
                    <p><b>Experience Detected:</b> {exp_yrs} years</p>
                    <p><b>File Name:</b> {filename}</p>
                </div>
                <div class="col">
                    <h3>Evaluation Metrics</h3>
                    <p><b>Overall Match Score:</b> <span style="font-size:20px; font-weight:bold; color:#4F46E5;">{score:.1f}%</span></p>
                    <p><b>Semantic Similarity:</b> {candidate.get('semantic_score', 0.0):.1f}%</p>
                    <p><b>Skill Coverage:</b> {candidate.get('skill_score', 0.0):.1f}%</p>
                    <p><b>Experience Relevance:</b> {candidate.get('exp_score', 0.0):.1f}%</p>
                    <p><b>Current Workflow Status:</b> <span class="badge">{status}</span></p>
                </div>
            </div>

            <div class="section-title">✅ Matched Skills ({len(matched)})</div>
            <ul>{matched_html}</ul>

            <div class="section-title">❌ Missing Skills ({len(missing)})</div>
            <ul>{missing_html}</ul>

            <div class="section-title">📝 Recruiter Notes & Human Reviewer Rationale</div>
            <p style="background:#F1F5F9; padding:12px; border-radius:6px;">{notes}</p>

            <div style="margin-top:40px; font-size:11px; color:#94A3B8; border-top:1px solid #E2E8F0; padding-top:10px;">
                Notice: AI-generated screening scores are decision-support signals, not final hiring decisions. Human recruiter review is required.
            </div>
        </body>
        </html>
        """
        return html_content
