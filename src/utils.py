"""
Utils & Theme Module
Provides custom dynamic CSS styling for Streamlit Light/Dark/System themes,
accent color customizations, status badge formatting, and CSV export helpers.
"""

import pandas as pd
from typing import List, Dict, Any


def generate_export_csv(candidates: List[Dict[str, Any]]) -> str:
    """
    Generates a clean CSV string of candidate evaluation results for export.
    Excludes private/demographic contact information.
    """
    export_rows = []
    for c in candidates:
        export_rows.append({
            "Rank": c.get("rank", 1),
            "Candidate Name": c.get("candidate_name", "Unknown"),
            "Match Score (%)": c.get("overall_match_score", 0.0),
            "Semantic Similarity (%)": c.get("semantic_score", 0.0),
            "Skill Score (%)": c.get("skill_score", 0.0),
            "Experience Score (%)": c.get("exp_score", 0.0),
            "Status": c.get("status", "Under Review"),
            "Matched Skills Count": len(c.get("matched_skills", [])),
            "Matched Skills": "; ".join(c.get("matched_skills", [])),
            "Missing Skills": "; ".join(c.get("missing_skills", [])),
            "Detected Experience (Years)": c.get("experience_years", 0.0),
            "Filename": c.get("filename", "")
        })

    df = pd.DataFrame(export_rows)
    return df.to_csv(index=False)


# Accent Color Palette Map
ACCENT_PALETTES = {
    "indigo": {"primary": "#6366F1", "secondary": "#8B5CF6", "gradient": "linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%)"},
    "purple": {"primary": "#8B5CF6", "secondary": "#D946EF", "gradient": "linear-gradient(135deg, #8B5CF6 0%, #D946EF 100%)"},
    "blue": {"primary": "#3B82F6", "secondary": "#06B6D4", "gradient": "linear-gradient(135deg, #3B82F6 0%, #06B6D4 100%)"},
    "emerald": {"primary": "#10B981", "secondary": "#059669", "gradient": "linear-gradient(135deg, #10B981 0%, #059669 100%)"}
}


def apply_custom_css(theme_mode: str = "dark", accent_color: str = "indigo") -> str:
    """
    Returns dynamic CSS string for Streamlit based on active theme mode (light/dark/system)
    and selected accent color palette.
    """
    palette = ACCENT_PALETTES.get(accent_color.lower(), ACCENT_PALETTES["indigo"])
    primary_color = palette["primary"]
    secondary_color = palette["secondary"]
    grad_bg = palette["gradient"]

    is_light = (theme_mode.lower() == "light")

    if is_light:
        bg_color = "#F8FAFC"
        surface_color = "#FFFFFF"
        card_bg = "#FFFFFF"
        text_primary = "#0F172A"
        text_secondary = "#64748B"
        border_color = "#E2E8F0"
        header_bg = "linear-gradient(135deg, #EEF2FF 0%, #E0E7FF 100%)"
        header_title = "#312E81"
        nav_bg = "#F1F5F9"
        radio_active_bg = grad_bg
        radio_active_text = "#FFFFFF"
    else:
        # Dark mode tokens (deep navy slate)
        bg_color = "#0B1120"
        surface_color = "#111827"
        card_bg = "#1E293B"
        text_primary = "#F8FAFC"
        text_secondary = "#94A3B8"
        border_color = "#334155"
        header_bg = "linear-gradient(135deg, #1E1B4B 0%, #312E81 50%, #4C1D95 100%)"
        header_title = "#F472B6"
        nav_bg = "#1E293B"
        radio_active_bg = grad_bg
        radio_active_text = "#FFFFFF"

    return f"""
    <style>
    /* Base App Styling */
    .stApp {{
        background-color: {bg_color};
        color: {text_primary};
        font-family: 'Inter', system-ui, -apple-system, sans-serif;
    }}

    /* Card Containers */
    div[data-testid="stVerticalBlock"] > div.element-container {{
        transition: all 0.2s ease-in-out;
    }}

    /* Custom Header Banner */
    .main-header {{
        background: {header_bg};
        border: 1px solid {border_color};
        border-radius: 12px;
        padding: 1.5rem 2rem;
        margin-bottom: 1rem;
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.15);
    }}
    
    .main-title {{
        font-size: 2.2rem;
        font-weight: 800;
        color: {header_title};
        background: {grad_bg};
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }}
    
    .main-subtitle {{
        color: {text_secondary};
        font-size: 1.05rem;
        font-weight: 400;
        margin-bottom: 0;
    }}

    /* Top Horizontal Navigation Container */
    div[role="radiogroup"] {{
        background: {nav_bg};
        padding: 0.4rem;
        border-radius: 12px;
        border: 1px solid {border_color};
        display: flex;
        justify-content: space-around;
        margin-bottom: 1.5rem;
    }}

    div[role="radiogroup"] label {{
        background: transparent;
        padding: 0.5rem 1rem;
        border-radius: 8px;
        color: {text_secondary};
        font-weight: 500;
        transition: all 0.2s ease;
    }}

    div[role="radiogroup"] label:hover {{
        color: {text_primary};
        background: rgba(99, 102, 241, 0.15);
    }}

    div[role="radiogroup"] label[data-checked="true"] {{
        background: {radio_active_bg} !important;
        color: {radio_active_text} !important;
        font-weight: 600;
        box-shadow: 0 4px 14px rgba(99, 102, 241, 0.35);
    }}

    /* Metric Cards */
    .metric-card {{
        background: {card_bg};
        border: 1px solid {border_color};
        border-radius: 12px;
        padding: 1.2rem;
        text-align: center;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }}

    .metric-card:hover {{
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.12);
    }}

    .metric-value {{
        font-size: 2.2rem;
        font-weight: 800;
        color: {primary_color};
    }}

    .metric-label {{
        font-size: 0.85rem;
        color: {text_secondary};
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-top: 0.3rem;
    }}

    .metric-trend {{
        font-size: 0.85rem;
        font-weight: 600;
        color: #10B981;
        margin-top: 0.2rem;
    }}

    /* Status Badges with Meaningful Color System */
    .badge-applied {{ background: rgba(59, 130, 246, 0.15); color: #60A5FA; border: 1px solid #3B82F6; padding: 3px 10px; border-radius: 12px; font-weight: 600; font-size: 0.8rem; }}
    .badge-screening {{ background: rgba(139, 92, 246, 0.15); color: #C084FC; border: 1px solid #8B5CF6; padding: 3px 10px; border-radius: 12px; font-weight: 600; font-size: 0.8rem; }}
    .badge-under-review {{ background: rgba(245, 158, 11, 0.15); color: #FBBF24; border: 1px solid #F59E0B; padding: 3px 10px; border-radius: 12px; font-weight: 600; font-size: 0.8rem; }}
    .badge-shortlisted {{ background: rgba(6, 182, 212, 0.15); color: #22D3EE; border: 1px solid #06B6D4; padding: 3px 10px; border-radius: 12px; font-weight: 600; font-size: 0.8rem; }}
    .badge-interview {{ background: rgba(99, 102, 241, 0.15); color: #818CF8; border: 1px solid #6366F1; padding: 3px 10px; border-radius: 12px; font-weight: 600; font-size: 0.8rem; }}
    .badge-offer {{ background: rgba(16, 185, 129, 0.15); color: #34D399; border: 1px solid #10B981; padding: 3px 10px; border-radius: 12px; font-weight: 600; font-size: 0.8rem; }}
    .badge-hired {{ background: rgba(5, 150, 105, 0.2); color: #10B981; border: 1px solid #059669; padding: 3px 10px; border-radius: 12px; font-weight: 700; font-size: 0.8rem; }}
    .badge-rejected {{ background: rgba(239, 68, 68, 0.15); color: #F87171; border: 1px solid #EF4444; padding: 3px 10px; border-radius: 12px; font-weight: 600; font-size: 0.8rem; }}
    .badge-on-hold {{ background: rgba(234, 179, 8, 0.15); color: #FACC15; border: 1px solid #EAB308; padding: 3px 10px; border-radius: 12px; font-weight: 600; font-size: 0.8rem; }}

    /* Skill Pill Badges */
    .skill-pill {{
        display: inline-block;
        background: rgba(99, 102, 241, 0.18);
        color: #A5B4FC;
        border: 1px solid rgba(99, 102, 241, 0.4);
        border-radius: 16px;
        padding: 0.25rem 0.75rem;
        font-size: 0.8rem;
        font-weight: 500;
        margin: 0.2rem;
    }}

    .missing-pill {{
        display: inline-block;
        background: rgba(239, 68, 68, 0.18);
        color: #FCA5A5;
        border: 1px solid rgba(239, 68, 68, 0.4);
        border-radius: 16px;
        padding: 0.25rem 0.75rem;
        font-size: 0.8rem;
        font-weight: 500;
        margin: 0.2rem;
    }}

    /* Kanban Card Container */
    .kanban-col {{
        background: {card_bg};
        border: 1px solid {border_color};
        border-radius: 12px;
        padding: 1rem;
        min-height: 400px;
    }}

    .kanban-card {{
        background: {surface_color};
        border: 1px solid {border_color};
        border-radius: 8px;
        padding: 0.8rem;
        margin-bottom: 0.8rem;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05);
    }}
    </style>
    """
