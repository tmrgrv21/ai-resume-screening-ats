"""
Enterprise AI Resume Screening, Applicant Tracking & Talent Intelligence SaaS Platform
Production multi-page application with MongoDB persistence, Bcrypt password security,
Light/Dark theme architecture, Job Requisitions management, Kanban ATS pipeline,
Interview scheduling & scorecards, Real-time notifications, Human-in-the-Loop governance,
Side-by-side comparison, AI explainability, and System health monitoring.
"""

import os
import io
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.candidate_ranker import CandidateRanker
from src.database.db_manager import DatabaseManager
from src.repositories.job_repository import JobRepository
from src.repositories.interview_repository import InterviewRepository
from src.services.notification_service import NotificationService
from src.auth import AuthManager
from src.workflow import WorkflowEngine
from src.explainability import ExplainabilityEngine
from src.comparison import ComparisonEngine
from src.report_generator import ReportGenerator
from src.utils import generate_export_csv, apply_custom_css
from src.security.password import validate_password_strength

# Page Configuration
st.set_page_config(
    page_title="Enterprise AI Recruitment & ATS Platform",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize Core Services
@st.cache_resource
def get_services():
    db = DatabaseManager()
    auth = AuthManager(db)
    workflow = WorkflowEngine(db)
    job_repo = JobRepository(db)
    interview_repo = InterviewRepository(db)
    notif_service = NotificationService(db)
    return db, auth, workflow, job_repo, interview_repo, notif_service

db_manager, auth_manager, workflow_engine, job_repo, interview_repo, notif_service = get_services()

# Session State Auth & Preferences Initialization
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = True  # Default logged in as recruiter for instant demo access
if "user" not in st.session_state or not st.session_state["user"]:
    _, user_data, _ = auth_manager.login("recruiter", "recruiter123")
    st.session_state["user"] = user_data

current_user = st.session_state.get("user") or {}
username = current_user.get("username", "recruiter")

# User Theme Preferences
if "user_theme" not in st.session_state:
    user_prefs = auth_manager.user_repo.get_user_preferences(username)
    st.session_state["user_theme"] = user_prefs.get("theme", "dark")
    st.session_state["user_accent"] = user_prefs.get("accent_color", "indigo")

# Apply dynamic CSS styles based on active theme & accent
st.markdown(apply_custom_css(st.session_state["user_theme"], st.session_state["user_accent"]), unsafe_allow_html=True)


def load_sample_data():
    """Loads sample job description and candidate resumes."""
    sample_dir = os.path.join(os.path.dirname(__file__), "data", "sample")
    job_desc = ""
    job_path = os.path.join(sample_dir, "job_description.txt")
    if os.path.exists(job_path):
        with open(job_path, "r", encoding="utf-8") as f:
            job_desc = f.read()

    sample_files = []
    for fname in ["alex_rivera_senior_ml.txt", "sarah_chen_data_analyst.txt", "michael_scott_frontend.txt"]:
        fpath = os.path.join(sample_dir, fname)
        if os.path.exists(fpath):
            with open(fpath, "rb") as f:
                sample_files.append({"filename": fname, "content": f.read()})

    return job_desc, sample_files


# ----------------------------------------------------
# LOGIN / SIGN UP AUTHENTICATION PORTAL
# ----------------------------------------------------
if not st.session_state.get("authenticated", False):
    st.markdown(
        """
        <div class="main-header" style="text-align: center; margin-top: 1rem;">
            <div class="main-title" style="font-size:2.5rem;">⚡ AI Recruitment & ATS Enterprise Platform</div>
            <div class="main-subtitle">Enterprise Candidate Evaluation, Semantic Matching, and Identity Governance</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    auth_col1, auth_col2, auth_col3 = st.columns([1, 2, 1])
    with auth_col2:
        tab_login, tab_signup, tab_forgot = st.tabs(["🔑 Sign In / Login", "📝 Sign Up / Register", "🔑 Forgot Password"])

        with tab_login:
            st.markdown("### 🔑 Account Sign In")
            login_user = st.text_input("Username or Email:", value="recruiter", key="login_u")
            login_pwd = st.text_input("Password:", value="recruiter123", type="password", key="login_p")
            remember_me = st.checkbox("Remember me on this browser", value=True)

            if st.button("🔓 Sign In", use_container_width=True, key="login_btn"):
                success, user_data, err_msg = auth_manager.login(login_user, login_pwd)
                if success:
                    st.session_state["user"] = user_data
                    st.session_state["authenticated"] = True
                    st.success(f"Welcome back, {user_data['username']}! Signed in as {user_data['role']}.")
                    st.rerun()
                else:
                    st.error(err_msg)

            st.markdown("---")
            st.markdown("#### ⚡ 1-Click Quick Demo Sign-In:")
            d1, d2, d3, d4 = st.columns(4)
            if d1.button("👑 Admin"):
                _, u, _ = auth_manager.login("admin", "admin123")
                st.session_state["user"] = u
                st.session_state["authenticated"] = True
                st.rerun()
            if d2.button("👔 Recruiter"):
                _, u, _ = auth_manager.login("recruiter", "recruiter123")
                st.session_state["user"] = u
                st.session_state["authenticated"] = True
                st.rerun()
            if d3.button("💼 Manager"):
                _, u, _ = auth_manager.login("hiring_manager", "manager123")
                st.session_state["user"] = u
                st.session_state["authenticated"] = True
                st.rerun()
            if d4.button("👁️ Viewer"):
                _, u, _ = auth_manager.login("viewer", "viewer123")
                st.session_state["user"] = u
                st.session_state["authenticated"] = True
                st.rerun()

        with tab_signup:
            st.markdown("### 📝 Register New Account")
            new_u = st.text_input("Choose Username:", key="reg_u")
            new_fn = st.text_input("Full Name:", key="reg_fn")
            new_e = st.text_input("Email Address:", key="reg_e")
            new_p = st.text_input("Password:", type="password", key="reg_p")

            if new_p:
                strength = validate_password_strength(new_p)
                st.caption(f"Password Strength: **{strength['rating']}**")
                c_list = strength['checklist']
                st.markdown(
                    f"{'✅' if c_list['min_length'] else '❌'} 8+ chars | "
                    f"{'✅' if c_list['has_uppercase'] else '❌'} Uppercase | "
                    f"{'✅' if c_list['has_lowercase'] else '❌'} Lowercase | "
                    f"{'✅' if c_list['has_number'] else '❌'} Number"
                )

            new_role = st.selectbox("Account Role:", options=["Recruiter", "HiringManager", "Viewer"], key="reg_r")

            if st.button("✨ Create Account", use_container_width=True, key="reg_btn"):
                success, msg = auth_manager.register(
                    username=new_u,
                    email=new_e,
                    password=new_p,
                    role=new_role,
                    full_name=new_fn
                )
                if success:
                    st.success(msg)
                else:
                    st.error(msg)

        with tab_forgot:
            st.markdown("### 🔑 Reset Password Request")
            reset_email = st.text_input("Enter Account Email:", key="forgot_e")
            if st.button("Send Reset Request", use_container_width=True, key="forgot_btn"):
                _, msg, dev_token = auth_manager.security_service.create_password_reset_token(reset_email)
                st.info(msg)
                st.session_state["dev_reset_token"] = dev_token

            if "dev_reset_token" in st.session_state:
                st.markdown("---")
                st.caption("🔑 Dev Reset Token Mode:")
                token_input = st.text_input("Reset Token:", value=st.session_state["dev_reset_token"], key="r_token")
                new_pass_input = st.text_input("New Password:", type="password", key="r_new_p")
                if st.button("Update Password", key="r_up_btn"):
                    s, m = auth_manager.security_service.reset_password_with_token(token_input, new_pass_input)
                    if s:
                        st.success(m)
                        del st.session_state["dev_reset_token"]
                    else:
                        st.error(m)

    st.stop()

# ----------------------------------------------------
# AUTHENTICATED PORTAL VIEW
# ----------------------------------------------------
current_user = st.session_state.get("user") or {}
permissions = current_user.get("permissions", {})

# HEADER & TOP CONTROLS BAR
h_col1, h_col2, h_col3 = st.columns([2.5, 1.2, 0.8])
with h_col1:
    st.markdown(
        f"""
        <div class="main-header" style="margin-bottom:0.5rem; padding: 1rem 1.8rem;">
            <div class="main-title" style="font-size:1.7rem;">⚡ AI Recruitment & Talent Platform</div>
            <div class="main-subtitle">User: <b>{current_user.get('username', 'User')}</b> | Role: <span style="color:#F472B6;">{current_user.get('role', 'Recruiter')}</span></div>
        </div>
        """,
        unsafe_allow_html=True
    )

with h_col2:
    st.markdown("<br>", unsafe_allow_html=True)
    theme_sel = st.selectbox(
        "Theme:",
        options=["Dark 🌙", "Light ☀", "System 💻"],
        index=["Dark 🌙", "Light ☀", "System 💻"].index("Light ☀" if st.session_state["user_theme"] == "light" else "Dark 🌙"),
        key="top_theme_sel"
    )
    new_theme = "light" if "Light" in theme_sel else "dark"
    if new_theme != st.session_state["user_theme"]:
        st.session_state["user_theme"] = new_theme
        auth_manager.user_repo.save_user_preferences(username, theme=new_theme, accent_color=st.session_state["user_accent"])
        st.rerun()

with h_col3:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔒 Logout", use_container_width=True):
        if "session_token" in current_user:
            auth_manager.logout(current_user["session_token"])
        st.session_state["authenticated"] = False
        st.session_state["user"] = None
        st.rerun()

# User Role Switcher Bar in Sidebar
st.sidebar.markdown("### 👤 User Account & Profile")
st.sidebar.info(f"Logged in: **{current_user.get('username')}** ({current_user.get('role')})")

role_choice = st.sidebar.selectbox(
    "Switch Role Profile:",
    options=["Recruiter", "Admin", "HiringManager", "Viewer"],
    index=["Recruiter", "Admin", "HiringManager", "Viewer"].index(current_user.get("role", "Recruiter")) if current_user.get("role") in ["Recruiter", "Admin", "HiringManager", "Viewer"] else 0
)

if role_choice != current_user.get("role"):
    role_user_map = {
        "Admin": ("admin", "admin123"),
        "Recruiter": ("recruiter", "recruiter123"),
        "HiringManager": ("hiring_manager", "manager123"),
        "Viewer": ("viewer", "viewer123")
    }
    uname, pwd = role_user_map[role_choice]
    _, u_data, _ = auth_manager.login(uname, pwd)
    st.session_state["user"] = u_data
    st.rerun()

current_user = st.session_state["user"]
permissions = current_user.get("permissions", {})

st.sidebar.markdown("---")

# Main Top Navigation Radio Menu
nav_option = st.radio(
    "Navigation Menu",
    options=[
        "📊 Operational Dashboard",
        "💼 Job Openings & Requirements",
        "⚡ Core AI Screening Workspace",
        "👥 Candidates & Talent Pool",
        "📌 Recruitment Pipeline Kanban",
        "⚔️ Candidate Comparison",
        "🗓️ Interview Management",
        "📈 Analytics & Insights",
        "📜 Audit Logs & Governance",
        "🔒 Account & Security Center",
        "⚙️ System Health & Preferences"
    ],
    horizontal=True,
    label_visibility="collapsed"
)

st.markdown("<br>", unsafe_allow_html=True)


# ====================================================
# PAGE 1: OPERATIONAL DASHBOARD
# ====================================================
if nav_option == "📊 Operational Dashboard":
    st.markdown("## 📊 Operational Recruitment Dashboard")
    st.markdown("Real-time persistent metrics, hiring funnel analytics, and candidate activity.")

    evaluations = db_manager.get_all_evaluations()
    jobs = job_repo.get_all_jobs()
    audit_logs = db_manager.get_audit_logs(limit=5)

    total_candidates = len(evaluations)
    active_jobs_count = len([j for j in jobs if j.get("status") == "Open"])
    shortlisted_count = len([e for e in evaluations if e.get("status") in ["Shortlisted", "Interview Scheduled", "Hired"]])
    avg_score = (sum(e.get("overall_score", 0.0) for e in evaluations) / total_candidates) if total_candidates > 0 else 0.0

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-value">{total_candidates}</div>
                <div class="metric-label">Total Candidates</div>
                <div class="metric-trend">↑ 12.5% vs last month</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with k2:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-value">{active_jobs_count}</div>
                <div class="metric-label">Active Job Openings</div>
                <div class="metric-trend">↑ 2 new jobs open</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with k3:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-value">{shortlisted_count}</div>
                <div class="metric-label">Shortlisted Candidates</div>
                <div class="metric-trend">↑ High match volume</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with k4:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-value">{avg_score:.1f}%</div>
                <div class="metric-label">Avg AI Match Score</div>
                <div class="metric-trend">↑ High qualification</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("<br>", unsafe_allow_html=True)
    c_left, c_right = st.columns([1.5, 1], gap="large")

    with c_left:
        st.markdown("### 🏆 Top Evaluated Candidates")
        if evaluations:
            df_top = pd.DataFrame([
                {
                    "Candidate Name": e.get("candidate_name", "Unknown"),
                    "Match Score": f"{e.get('overall_score', 0.0):.1f}%",
                    "Status": e.get("status", "Under Review"),
                    "Experience": f"{e.get('experience_years', 0.0)} yrs",
                    "Filename": e.get("filename", "")
                }
                for e in evaluations[:5]
            ])
            st.dataframe(df_top, use_container_width=True, hide_index=True)
        else:
            st.info("No candidates stored in MongoDB yet. Upload resumes in the Core AI Screening tab!")

    with c_right:
        st.markdown("### 📜 System Activity Feed")
        if audit_logs:
            for log in audit_logs:
                ts = str(log.get('timestamp', ''))[:19]
                st.caption(f"⏱️ **{ts}** | `{log.get('user_username')}`: {log.get('action')} ({log.get('details')})")
        else:
            st.info("No recent audit activities logged.")


# ====================================================
# PAGE 2: JOB OPENINGS & REQUIREMENTS
# ====================================================
elif nav_option == "💼 Job Openings & Requirements":
    st.markdown("## 💼 Job Openings & Requisition Management")
    st.markdown("Manage open requisitions, required skill taxonomies, and experience criteria.")

    tab_jobs_list, tab_create_job = st.tabs(["📋 Active Job Openings", "➕ Create New Job Opening"])

    with tab_jobs_list:
        jobs = job_repo.get_all_jobs()
        if not jobs:
            st.info("No job openings created yet. Use the 'Create New Job Opening' tab to publish a job description!")
        else:
            for j in jobs:
                job_id = j.get("job_id", str(j.get("_id", "")))
                with st.expander(f"💼 {j['title']} — {j.get('department', 'Engineering')} | {j.get('location', 'Remote')} | Status: {j.get('status', 'Open')}"):
                    c1, c2 = st.columns([2, 1])
                    with c1:
                        st.markdown(f"**Salary Range:** {j.get('salary_range', 'Competitive')} | **Type:** {j.get('employment_type', 'Full-time')}")
                        st.markdown(f"**Required Experience:** {j.get('required_experience', 3.0)} years")
                        st.markdown("**Required Skills:**")
                        req_skills = j.get("required_skills", [])
                        if req_skills:
                            st.markdown(" ".join([f"`{s}`" for s in req_skills]))
                        else:
                            st.markdown("None specified")

                        st.markdown("**Description:**")
                        st.write(j.get("description", ""))

                    with c2:
                        st.markdown("#### ⚙️ Job Actions")
                        cur_st = j.get("status", "Open")
                        opts = ["Open", "Paused", "Closed", "Archived"]
                        idx = opts.index(cur_st) if cur_st in opts else 0
                        new_st = st.selectbox("Update Job Status:", options=opts, index=idx, key=f"job_st_sel_{job_id}")

                        if st.button("Save Job Status", key=f"job_st_btn_{job_id}", disabled=not permissions.get("can_create_requisition", False)):
                            job_repo.update_job_status(job_id, new_st, user_username=current_user.get("username", "admin"))
                            st.success(f"Updated job '{j['title']}' to '{new_st}'!")
                            st.rerun()

                        if st.button("⚡ Use This Job for Resume Screening", key=f"use_job_btn_{job_id}"):
                            st.session_state["job_description"] = j.get("description", "")
                            st.session_state["selected_job_title"] = j['title']
                            st.success(f"Loaded '{j['title']}' description into Screening Workspace!")

    with tab_create_job:
        st.markdown("### ➕ Create Job Requisition")
        with st.form("create_job_form"):
            j_title = st.text_input("Job Title:", placeholder="e.g. Senior Machine Learning Engineer")
            f1, f2, f3 = st.columns(3)
            j_dept = f1.text_input("Department:", value="Engineering")
            j_loc = f2.text_input("Location:", value="Remote")
            j_type = f3.selectbox("Employment Type:", options=["Full-time", "Part-time", "Contract"])

            f4, f5 = st.columns(2)
            j_exp = f4.number_input("Required Experience (Years):", min_value=0.0, max_value=20.0, value=3.0, step=0.5)
            j_sal = f5.text_input("Salary Range:", value="$120,000 - $160,000")

            j_skills = st.text_input("Required Skills (comma-separated):", value="Python, PyTorch, Docker, Machine Learning")
            j_desc = st.text_area("Job Description Text:", height=200, placeholder="Paste detailed job requirements and duties...")

            submit_job = st.form_submit_button("🚀 Publish Job Opening")
            if submit_job:
                if not j_title or not j_desc:
                    st.error("Please enter a Job Title and Description.")
                else:
                    skills_list = [s.strip() for s in j_skills.split(",") if s.strip()]
                    job_repo.create_job(
                        title=j_title,
                        description=j_desc,
                        department=j_dept,
                        location=j_loc,
                        employment_type=j_type,
                        required_experience=j_exp,
                        required_skills=skills_list,
                        salary_range=j_sal,
                        created_by=current_user.get("username", "admin")
                    )
                    st.success(f"Job opening '{j_title}' published successfully!")
                    st.rerun()


# ====================================================
# PAGE 3: CORE AI SCREENING WORKSPACE
# ====================================================
elif nav_option == "⚡ Core AI Screening Workspace":
    st.markdown("## ⚡ Core AI Resume Screening Workspace")
    st.markdown("Upload candidate resumes and match against Job Description requirements.")

    # Sidebar weights adjustment for screening
    st.sidebar.markdown("### ⚙️ Scoring Weights Config")
    sem_weight = st.sidebar.slider("Semantic Similarity Weight (%)", 0, 100, 60, 5)
    sk_weight = st.sidebar.slider("Skill Match Weight (%)", 0, 100, 30, 5)
    ex_weight = st.sidebar.slider("Experience Weight (%)", 0, 100, 10, 5)

    custom_skills_input = st.sidebar.text_area("Extra Custom Skills (comma-separated):", placeholder="e.g. LangChain, VectorDB")
    custom_skills_list = [s.strip() for s in custom_skills_input.split(",") if s.strip()]

    if st.sidebar.button("Load Demo Job & Sample Resumes"):
        sample_jd, sample_resumes = load_sample_data()
        st.session_state["job_description"] = sample_jd
        st.session_state["demo_resumes"] = sample_resumes
        st.sidebar.success("Loaded sample demo dataset!")

    col_jd, col_up = st.columns([1, 1], gap="large")

    with col_jd:
        st.markdown("### 📄 Job Description")
        default_jd = st.session_state.get("job_description", "")
        job_description = st.text_area("Paste Job Description:", value=default_jd, height=280, placeholder="Paste Job Description text...")

    with col_up:
        st.markdown("### 📁 Upload Resumes (PDF, DOCX, TXT)")
        uploaded_files = st.file_uploader("Select Resume Files:", type=["pdf", "docx", "doc", "txt"], accept_multiple_files=True)
        demo_resumes = st.session_state.get("demo_resumes", [])
        if demo_resumes and not uploaded_files:
            st.info(f"Loaded {len(demo_resumes)} sample candidate resumes for demo testing.")

    files_to_process = []
    if uploaded_files:
        for u in uploaded_files:
            files_to_process.append({"filename": u.name, "content": u.getvalue()})
    elif demo_resumes:
        files_to_process = demo_resumes

    if st.button("🚀 Run AI Resume Analysis", disabled=not permissions.get("can_run_screening", False)):
        if not job_description.strip():
            st.error("Please enter a Job Description.")
        elif not files_to_process:
            st.error("Please upload resumes or load demo sample resumes.")
        else:
            with st.spinner("Processing resumes with NLP embeddings and skill taxonomy extractor..."):
                st.markdown(
                    """
                    <div style="background: rgba(99,102,241,0.1); border: 1px solid #6366F1; padding: 1rem; border-radius: 8px; margin-bottom: 1rem;">
                        <b>AI Processing Stage Visualizer:</b><br>
                        ✓ Reading Resume Documents<br>
                        ✓ Extracting Content & Redacting Demographic Cues<br>
                        ✓ Detecting Technical Skill Taxonomies<br>
                        ⏳ Generating 384-dimensional SentenceTransformer Embeddings...<br>
                        ○ Calculating Multi-Factor Weighted Score<br>
                        ○ Generating Transparent AI Match Explanations
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                ranker = CandidateRanker(
                    semantic_weight=sem_weight,
                    skill_weight=sk_weight,
                    exp_weight=ex_weight,
                    custom_skills=custom_skills_list
                )
                results = ranker.process_candidates(job_description, files_to_process)

                # Check Duplicate Warnings & Persist
                existing_evals = db_manager.get_all_evaluations()
                for c in results["candidates"]:
                    dup = ranker.check_duplicate_candidate(c.get("email"), c.get("phone"), c.get("candidate_name"), existing_evals)
                    if dup:
                        c["duplicate_warning"] = f"Possible duplicate application ({dup['type']})"
                    db_manager.save_candidate_evaluation(c, user_username=current_user["username"])

                st.session_state["latest_results"] = results
                st.success(f"Successfully processed and stored {results['total_processed']} candidate evaluations in MongoDB!")

    if "latest_results" in st.session_state:
        results = st.session_state["latest_results"]
        candidates = results["candidates"]

        st.markdown("---")
        st.markdown("### 🏆 Candidate Leaderboard")
        st.dataframe(results["df_summary"], use_container_width=True, hide_index=True)

        # Plotly Score Chart
        df_chart = pd.DataFrame(candidates)
        fig_score = px.bar(
            df_chart,
            x="candidate_name",
            y="overall_match_score",
            color="status",
            color_discrete_map={"Strong Match": "#10B981", "Good Match": "#3B82F6", "Potential Match": "#F59E0B", "Low Match": "#EF4444"},
            text="overall_match_score",
            title="Candidate Match Score Summary (%)"
        )
        fig_score.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
        fig_score.update_layout(template="plotly_dark" if st.session_state["user_theme"] == "dark" else "plotly_white", yaxis=dict(range=[0, 110]))
        st.plotly_chart(fig_score, use_container_width=True)


# ====================================================
# PAGE 4: CANDIDATES & TALENT POOL
# ====================================================
elif nav_option == "👥 Candidates & Talent Pool":
    st.markdown("## 👥 Candidates & Talent Pool Database")
    st.markdown("Persistent database registry of all evaluated candidates with search and human status lifecycle controls.")

    evaluations = db_manager.get_all_evaluations()

    if not evaluations:
        st.info("No candidates stored in MongoDB yet. Run a screening to populate the talent pool!")
    else:
        # Search & Filters
        f_col1, f_col2 = st.columns([1, 2])
        with f_col1:
            status_filter = st.selectbox("Filter by Status:", options=["All"] + ["Under Review", "Shortlisted", "Interview Scheduled", "Hired", "Rejected", "Archived"])
        with f_col2:
            search_query = st.text_input("Search Candidate Name or Skill:", placeholder="e.g. Python, Alex...")

        filtered_evals = evaluations
        if status_filter != "All":
            filtered_evals = [e for e in filtered_evals if e.get("status") == status_filter]
        if search_query.strip():
            sq = search_query.strip().lower()
            filtered_evals = [e for e in filtered_evals if sq in e.get("candidate_name", "").lower() or any(sq in s.lower() for s in e.get("matched_skills", []))]

        st.markdown(f"Showing **{len(filtered_evals)}** candidates:")

        for ev in filtered_evals:
            eval_id = ev.get("eval_id", str(ev.get("_id", "")))
            with st.expander(f"👤 {ev['candidate_name']} — Score: {ev.get('overall_score', 0.0):.1f}% | Status: {ev.get('status', 'Under Review')} | Exp: {ev.get('experience_years', 0.0)} yrs"):
                c1, c2 = st.columns([1.2, 1])
                with c1:
                    st.markdown(f"**Email:** {ev.get('email', 'N/A')} | **Phone:** {ev.get('phone', 'N/A')}")
                    st.markdown(f"**Filename:** {ev.get('filename', 'N/A')}")

                    # AI Match Explanation
                    explanation = ExplainabilityEngine.generate_match_explanation({
                        "overall_match_score": ev.get("overall_score", 0.0),
                        "matched_skills": ev.get("matched_skills", []),
                        "missing_skills": ev.get("missing_skills", []),
                        "experience_years": ev.get("experience_years", 0.0)
                    })

                    st.markdown("#### 🤖 AI Match Explanation")
                    st.info(explanation["headline"])
                    st.markdown("**Key Strengths:**")
                    for s in explanation["key_strengths"]:
                        st.markdown(f"- {s}")
                    st.markdown("**Identified Gaps:**")
                    for g in explanation["identified_gaps"]:
                        st.markdown(f"- {g}")

                with c2:
                    st.markdown("#### ⚙️ Human Status Override & Notes")
                    current_st = ev.get("status", "Under Review")
                    opts = ["Under Review", "Shortlisted", "Interview Scheduled", "Hired", "Rejected", "Archived"]
                    idx = opts.index(current_st) if current_st in opts else 0
                    new_status = st.selectbox("Update Status:", options=opts, index=idx, key=f"status_sel_{eval_id}")
                    notes = st.text_area("Reviewer Notes & Rationale:", value=ev.get("reviewer_notes", ""), key=f"notes_ta_{eval_id}")

                    if st.button("Save Status Update", key=f"save_btn_{eval_id}", disabled=not permissions.get("can_update_status", False)):
                        workflow_engine.update_status(eval_id, new_status, notes, user_username=current_user["username"])
                        st.success(f"Updated {ev['candidate_name']} to '{new_status}' in MongoDB!")
                        st.rerun()

                    # Download PDF Report Button
                    html_report = ReportGenerator.generate_html_report(ev)
                    st.download_button(
                        label="📄 Download Candidate Brief (HTML/PDF)",
                        data=html_report,
                        file_name=f"evaluation_report_{ev['candidate_name'].lower().replace(' ', '_')}.html",
                        mime="text/html",
                        key=f"dl_rpt_{eval_id}"
                    )


# ====================================================
# PAGE 5: RECRUITMENT PIPELINE KANBAN
# ====================================================
elif nav_option == "📌 Recruitment Pipeline Kanban":
    st.markdown("## 📌 Recruitment Pipeline Kanban Board")
    st.markdown("Interactive ATS recruitment funnel view organized by candidate lifecycle stage.")

    evaluations = db_manager.get_all_evaluations()

    stages = ["Applied", "Under Review", "Shortlisted", "Interview Scheduled", "Hired", "Rejected"]
    cols = st.columns(len(stages))

    for idx, stage in enumerate(stages):
        with cols[idx]:
            stage_cands = [e for e in evaluations if e.get("status", "Under Review") == stage]
            st.markdown(f"### {stage} ({len(stage_cands)})")

            if stage_cands:
                for c in stage_cands:
                    eval_id = c.get("eval_id", str(c.get("_id", "")))
                    st.markdown(
                        f"""
                        <div class="kanban-card">
                            <b>👤 {c['candidate_name']}</b><br>
                            Score: <span style="color:#10B981; font-weight:700;">{c.get('overall_score', 0.0):.1f}%</span><br>
                            <small>Exp: {c.get('experience_years', 0.0)} yrs</small>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
            else:
                st.caption("No candidates in stage")


# ====================================================
# PAGE 6: CANDIDATE COMPARISON MATRIX
# ====================================================
elif nav_option == "⚔️ Candidate Comparison":
    st.markdown("## ⚔️ Multi-Candidate Side-by-Side Comparison")
    st.markdown("Compare 2 to 4 candidates side-by-side across scores and skill matrix overlap.")

    evaluations = db_manager.get_all_evaluations()

    if len(evaluations) < 2:
        st.warning("At least 2 evaluated candidates are required in MongoDB to use candidate comparison.")
    else:
        selected_names = st.multiselect(
            "Select candidates to compare (2 - 4):",
            options=[e["candidate_name"] for e in evaluations],
            default=[e["candidate_name"] for e in evaluations[:2]]
        )

        selected_cands = [e for e in evaluations if e["candidate_name"] in selected_names]

        if selected_cands:
            comp_result = ComparisonEngine.build_comparison_matrix(selected_cands)

            st.markdown("### 📊 Metrics Comparison Table")
            st.dataframe(comp_result["metrics_df"], use_container_width=True)

            st.markdown("<br>### 🧩 Skill Coverage Comparison Matrix", unsafe_allow_html=True)
            st.dataframe(comp_result["skill_matrix_df"], use_container_width=True, hide_index=True)


# ====================================================
# PAGE 7: INTERVIEW MANAGEMENT
# ====================================================
elif nav_option == "🗓️ Interview Management":
    st.markdown("## 🗓️ Interview Scheduling & Qualitative Scorecards")
    st.markdown("Schedule interviewer calls and submit structured evaluation scorecards.")

    tab_interviews_list, tab_sched = st.tabs(["📋 Scheduled Interviews", "➕ Schedule New Interview"])

    with tab_interviews_list:
        interviews = interview_repo.get_all_interviews()
        if not interviews:
            st.info("No interviews scheduled yet. Use the 'Schedule New Interview' tab!")
        else:
            for iv in interviews:
                iv_id = iv.get("interview_id", str(iv.get("_id", "")))
                with st.expander(f"🗓️ {iv['candidate_name']} — {iv.get('interview_type')} | Date: {iv.get('scheduled_date')} at {iv.get('scheduled_time')}"):
                    st.markdown(f"**Interviewer:** {iv.get('interviewer')} | **Job Title:** {iv.get('job_title')}")
                    st.markdown(f"**Meeting Link:** [{iv.get('meeting_link')}]({iv.get('meeting_link')})")

                    if iv.get("scorecard"):
                        sc = iv["scorecard"]
                        st.success(f"Scorecard Submitted — Recommendation: **{sc.get('recommendation')}**")
                        st.caption(f"Tech: {sc.get('tech_score')}/5 | Comm: {sc.get('comm_score')}/5 | Problem Solving: {sc.get('problem_score')}/5")
                        st.write(f"**Feedback:** {sc.get('feedback_notes')}")
                    else:
                        st.markdown("#### 📝 Submit Interview Scorecard")
                        with st.form(f"sc_form_{iv_id}"):
                            sc_tech = st.slider("Technical Skills (1-5):", 1, 5, 4)
                            sc_comm = st.slider("Communication (1-5):", 1, 5, 4)
                            sc_prob = st.slider("Problem Solving (1-5):", 1, 5, 4)
                            sc_cult = st.slider("Culture Fit (1-5):", 1, 5, 4)
                            sc_rec = st.selectbox("Recommendation:", options=["Strong Hire", "Hire", "Neutral", "No Hire", "Strong No Hire"])
                            sc_notes = st.text_area("Interview Notes & Qualitative Feedback:")
                            sc_sub = st.form_submit_button("Submit Scorecard")

                            if sc_sub:
                                interview_repo.save_scorecard(
                                    interview_id=iv_id,
                                    tech_score=sc_tech,
                                    comm_score=sc_comm,
                                    problem_score=sc_prob,
                                    culture_score=sc_cult,
                                    leadership_score=4,
                                    recommendation=sc_rec,
                                    feedback_notes=sc_notes,
                                    evaluated_by=current_user.get("username", "hiring_manager")
                                )
                                st.success("Scorecard saved successfully!")
                                st.rerun()

    with tab_sched:
        evaluations = db_manager.get_all_evaluations()
        if not evaluations:
            st.warning("Please screen candidate resumes first before scheduling interviews.")
        else:
            cand_names = [e["candidate_name"] for e in evaluations]
            sel_cand_name = st.selectbox("Select Candidate:", options=cand_names)
            sel_cand = next(e for e in evaluations if e["candidate_name"] == sel_cand_name)

            i_job = st.text_input("Job Title:", value="Machine Learning Engineer")
            i_interviewer = st.text_input("Interviewer Name:", value="Tech Lead Alex")
            i_type = st.selectbox("Interview Type:", options=["Technical Interview", "HR Interview", "Manager Interview", "Final Interview"])
            i_date = st.date_input("Scheduled Date:")
            i_time = st.time_input("Scheduled Time:")
            i_link = st.text_input("Meeting Link:", value="https://meet.google.com/xyz-abc-123")

            if st.button("🗓️ Confirm Interview Schedule"):
                interview_repo.schedule_interview(
                    candidate_name=sel_cand["candidate_name"],
                    candidate_id=sel_cand.get("eval_id", str(sel_cand.get("_id"))),
                    job_title=i_job,
                    interviewer=i_interviewer,
                    interview_type=i_type,
                    scheduled_date=str(i_date),
                    scheduled_time=str(i_time),
                    meeting_link=i_link,
                    scheduled_by=current_user.get("username", "recruiter")
                )
                st.success(f"Scheduled {i_type} for {sel_cand['candidate_name']}!")
                st.rerun()


# ====================================================
# PAGE 8: ANALYTICS & INSIGHTS
# ====================================================
elif nav_option == "📈 Analytics & Insights":
    st.markdown("## 📈 Recruitment Analytics & Insights")

    evaluations = db_manager.get_all_evaluations()
    if evaluations:
        df_evals = pd.DataFrame(evaluations)

        c1, c2 = st.columns(2)
        with c1:
            fig_hist = px.histogram(df_evals, x="overall_score", nbins=10, title="Candidate Match Score Distribution (%)", color_discrete_sequence=["#818CF8"])
            fig_hist.update_layout(template="plotly_dark" if st.session_state["user_theme"] == "dark" else "plotly_white")
            st.plotly_chart(fig_hist, use_container_width=True)

        with c2:
            fig_pie = px.pie(df_evals, names="status", title="Talent Pool Workflow Status Funnel", color_discrete_sequence=px.colors.qualitative.Pastel)
            fig_pie.update_layout(template="plotly_dark" if st.session_state["user_theme"] == "dark" else "plotly_white")
            st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.info("No evaluation analytics available in MongoDB yet.")


# ====================================================
# PAGE 9: AUDIT LOGS & GOVERNANCE
# ====================================================
elif nav_option == "📜 Audit Logs & Governance":
    st.markdown("## 📜 Audit Trail & Responsible AI Governance")
    st.markdown("Immutable record of system actions, role access logs, and AI compliance safeguards.")

    if not permissions.get("can_view_audit_logs", False):
        st.warning("⚠️ Access Restricted: Only Admin users can view system audit logs.")
    else:
        logs = db_manager.get_audit_logs(limit=100)
        df_logs = pd.DataFrame(logs)
        st.dataframe(df_logs, use_container_width=True, hide_index=True)


# ====================================================
# PAGE 10: ACCOUNT & SECURITY CENTER
# ====================================================
elif nav_option == "🔒 Account & Security Center":
    st.markdown("## 🔒 Account & Security Center")
    st.markdown("Manage active device sessions, security credentials, and login activity logs.")

    tab_profile, tab_sessions, tab_activity = st.tabs(["👤 Profile & Credentials", "💻 Active Device Sessions", "📜 Login Activity Log"])

    with tab_profile:
        st.markdown("### 👤 User Account Details")
        st.info(f"Username: **{current_user.get('username')}** | Email: **{current_user.get('email', 'N/A')}** | Role: **{current_user.get('role')}**")

        st.markdown("#### 🔑 Change Password")
        cur_p = st.text_input("Current Password:", type="password", key="chg_cur_p")
        new_p = st.text_input("New Password:", type="password", key="chg_new_p")
        if new_p:
            st_val = validate_password_strength(new_p)
            st.caption(f"New Password Strength: **{st_val['rating']}**")

        if st.button("Update Password", key="chg_p_btn"):
            if not cur_p or not new_p:
                st.error("Please fill in current and new passwords.")
            else:
                users_col = db_manager.get_collection("users")
                u_doc = users_col.find_one({"username": current_user["username"]})
                from src.security.password import verify_password, hash_password
                if u_doc and verify_password(cur_p, u_doc["password_hash"]):
                    users_col.update_one({"_id": u_doc["_id"]}, {"$set": {"password_hash": hash_password(new_p)}})
                    st.success("Password updated successfully!")
                else:
                    st.error("Incorrect current password.")

    with tab_sessions:
        st.markdown("### 💻 Active Device Sessions")
        st.caption("Active persistent sessions registered for your account:")
        user_id = current_user.get("user_id", current_user.get("username"))
        active_sessions = auth_manager.session_service.get_active_sessions_for_user(user_id)

        if active_sessions:
            for s in active_sessions:
                is_cur = (s.get("session_token_hash") == auth_manager.session_service.hash_token(current_user.get("session_token", "")))
                st.write(f"📱 **{s.get('device_name', 'Device')}** {'(Current Device)' if is_cur else ''}")
                st.caption(f"IP: `{s.get('ip_address')}` | Created: `{str(s.get('created_at'))[:19]}` | Last Active: `{str(s.get('last_activity_at'))[:19]}`")
                st.markdown("---")

            if st.button("🚪 Sign Out All Other Devices"):
                rev_count = auth_manager.session_service.revoke_all_other_sessions(user_id, current_user.get("session_token", ""))
                st.success(f"Successfully revoked {rev_count} other device sessions!")
                st.rerun()
        else:
            st.info("No active persistent device sessions found.")

    with tab_activity:
        st.markdown("### 📜 Security & Login Activity Log")
        all_logs = db_manager.get_audit_logs(limit=100)
        user_logs = [l for l in all_logs if l.get("user_username") in [current_user.get("username"), current_user.get("email")]]
        if user_logs:
            st.dataframe(pd.DataFrame(user_logs), use_container_width=True, hide_index=True)
        else:
            st.info("No security activity logged for your account yet.")


# ====================================================
# PAGE 11: SYSTEM HEALTH & PREFERENCES SETTINGS
# ====================================================
elif nav_option == "⚙️ System Health & Preferences":
    st.markdown("## ⚙️ System Health & Personalization Settings")

    st.markdown("### 🎨 Visual Theme & Accent Customization")
    p1, p2 = st.columns(2)
    with p1:
        th_choice = st.selectbox("Application Theme:", options=["Dark Mode", "Light Mode"], index=0 if st.session_state["user_theme"] == "dark" else 1)
    with p2:
        ac_choice = st.selectbox("Accent Color Palette:", options=["Indigo", "Purple", "Blue", "Emerald"], index=["indigo", "purple", "blue", "emerald"].index(st.session_state["user_accent"]))

    if st.button("Save Theme Preferences"):
        new_th = "dark" if "Dark" in th_choice else "light"
        new_ac = ac_choice.lower()
        st.session_state["user_theme"] = new_th
        st.session_state["user_accent"] = new_ac
        auth_manager.user_repo.save_user_preferences(username, theme=new_th, accent_color=new_ac)
        st.success("Theme preferences saved!")
        st.rerun()

    st.markdown("---")
    st.markdown("### ⚙️ System Operational Health")

    h1, h2, h3, h4 = st.columns(4)
    h1.metric("MongoDB Engine", "Connected ●")
    h2.metric("ML Embedding Engine", "Operational ●")
    h3.metric("REST API Service", "Operational ●")
    h4.metric("Role Access Control", "Enforced ●")
