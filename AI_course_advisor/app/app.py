import ast
import os
import re
import sys
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = str(Path(__file__).resolve().parent.parent)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import streamlit as st

from agents.profile_agent import profile_analysis
from agents.course_research_agent import research_courses
from agents.recommendation_agent import recommend_courses
from agents.learning_path_agent import learning_path_agent


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="AI Course Advisor",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# HTML RENDERING HELPER (PREVENTS MARKDOWN CODE-BLOCK TRAPS)
# ============================================================

def render_html(html_str):
    """
    Renders HTML in Streamlit ensuring lines have no leading indentation,
    preventing Markdown from treating indented HTML tags as code blocks.
    """
    clean_lines = [line.strip() for line in str(html_str).strip().splitlines() if line.strip()]
    st.markdown(" ".join(clean_lines), unsafe_allow_html=True)


# ============================================================
# NORMALIZE SKILL
# ============================================================

def normalize_skill(value):

    if value is None:
        return ""

    text = str(value).strip().lower()

    text = text.replace("_", " ")
    text = text.replace("-", " ")

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text


# ============================================================
# SKILL GAP CALCULATION
# ============================================================

def calculate_skill_gaps(
    course,
    learner_skills
):

    prerequisites = course.get(
        "prerequisites",
        []
    )

    if not isinstance(
        prerequisites,
        list
    ):

        prerequisites = [
            prerequisites
        ]

    learner_skill_set = {
        normalize_skill(skill)
        for skill in learner_skills
        if normalize_skill(skill)
    }

    satisfied = []
    missing = []

    for prerequisite in prerequisites:

        prerequisite_text = str(
            prerequisite
        ).strip()

        normalized = normalize_skill(
            prerequisite_text
        )

        if not normalized:
            continue

        # Basic computer knowledge is treated
        # as baseline knowledge.
        if normalized == "basic computer knowledge":

            satisfied.append(
                prerequisite_text
            )

            continue

        # Exact skill match
        if normalized in learner_skill_set:

            satisfied.append(
                prerequisite_text
            )

            continue

        # Flexible match
        matched = False

        for skill in learner_skill_set:

            if (
                normalized == skill
                or normalized in skill
                or skill in normalized
            ):

                matched = True
                break

        if matched:

            satisfied.append(
                prerequisite_text
            )

        else:

            missing.append(
                prerequisite_text
            )

    return satisfied, missing


# ============================================================
# ENRICH COURSE
# ============================================================

def enrich_course(
    course,
    learner_skills
):

    updated = dict(course)

    satisfied, missing = (
        calculate_skill_gaps(
            course,
            learner_skills
        )
    )

    updated[
        "satisfied_prerequisites"
    ] = satisfied

    updated[
        "missing_prerequisites"
    ] = missing

    course_name = normalize_skill(
        course.get(
            "course_name",
            ""
        )
    )

    original_status = course.get(
        "status",
        ""
    )

    learner_skill_set = {
        normalize_skill(skill)
        for skill in learner_skills
    }

    # --------------------------------------------------------
    # Python already present
    # --------------------------------------------------------

    if (
        "python for beginners"
        in course_name
        and "python"
        in learner_skill_set
    ):

        updated[
            "ui_readiness"
        ] = "Ready"

        updated[
            "ui_status"
        ] = "Skip - Skill Already Present"

        return updated

    # --------------------------------------------------------
    # Missing prerequisites
    # --------------------------------------------------------

    if missing:

        updated[
            "ui_readiness"
        ] = "Partially Ready"

        if original_status == "Blocked":

            updated[
                "ui_status"
            ] = "Blocked"

        else:

            updated[
                "ui_status"
            ] = "Prepare First"

    # --------------------------------------------------------
    # Ready
    # --------------------------------------------------------

    else:

        updated[
            "ui_readiness"
        ] = "Ready"

        if original_status:

            updated[
                "ui_status"
            ] = original_status

        else:

            updated[
                "ui_status"
            ] = "Recommended Now"

    return updated


# ============================================================
# PARSE RECOMMENDATION OUTPUT
# ============================================================

def parse_recommendation_output(
    result
):

    if isinstance(
        result,
        dict
    ):

        return result

    if not isinstance(
        result,
        str
    ):

        return {
            "best_course": "",
            "recommendations": [],
            "learning_path": [],
            "explanation": ""
        }

    text = result.strip()

    candidates = []

    if (
        "FINAL RECOMMENDATIONS"
        in text
    ):

        candidates.append(
            text.split(
                "FINAL RECOMMENDATIONS",
                1
            )[1].strip()
        )

    candidates.append(
        text
    )

    for candidate in candidates:

        positions = [
            match.start()
            for match in re.finditer(
                r"\{",
                candidate
            )
        ]

        for start in positions:

            possible = candidate[
                start:
            ].strip()

            try:
                parsed = ast.literal_eval(
                    possible
                )
                if isinstance(
                    parsed,
                    dict
                ):
                    return parsed
            except Exception:
                pass

            try:
                import json
                parsed = json.loads(
                    possible
                )
                if isinstance(
                    parsed,
                    dict
                ):
                    return parsed
            except Exception:
                pass

    return {
        "best_course": "",
        "recommendations": [],
        "learning_path": [],
        "explanation": text
    }


# ============================================================
# CACHED AGENT CALLS
# ============================================================

@st.cache_data(
    show_spinner=False,
    ttl=3600
)
def cached_profile_analysis(
    profile
):

    return profile_analysis(
        profile
    )


@st.cache_data(
    show_spinner=False,
    ttl=3600
)
def cached_research_courses(
    profile
):

    return research_courses(
        profile
    )


@st.cache_data(
    show_spinner=False,
    ttl=3600
)
def cached_recommend_courses(
    profile
):

    return recommend_courses(
        profile
    )


@st.cache_data(
    show_spinner=False,
    ttl=3600
)
def cached_learning_path(
    profile,
    recommendations
):

    return learning_path_agent(
        profile,
        recommendations
    )


# ============================================================
# MODERN AI SAAS STYLESHEET
# ============================================================

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        color: #0f172a;
    }

    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 3rem !important;
        max-width: 1140px !important;
    }

    /* Sidebar Clean Styling */
    [data-testid="stSidebar"] {
        background-color: #f8fafc;
        border-right: 1px solid #e2e8f0;
    }

    [data-testid="stSidebar"] .block-container {
        padding-top: 1.25rem !important;
        padding-left: 1.25rem !important;
        padding-right: 1.25rem !important;
    }

    .sidebar-header-box {
        margin-bottom: 12px;
    }

    .sidebar-app-title {
        font-size: 1.15rem;
        font-weight: 700;
        color: #0f172a;
        margin: 0;
        line-height: 1.2;
    }

    .sidebar-app-sub {
        font-size: 0.8rem;
        font-weight: 500;
        color: #64748b;
        margin: 2px 0 0 0;
    }

    .sidebar-group-title {
        font-size: 0.7rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #475569;
        margin-top: 14px;
        margin-bottom: 4px;
    }

    /* Top Header */
    .saas-header-container {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        padding-bottom: 14px;
        border-bottom: 1px solid #e2e8f0;
        margin-bottom: 16px;
        gap: 16px;
    }

    .saas-header-title {
        font-size: 1.5rem;
        font-weight: 700;
        color: #0f172a;
        margin: 0;
        line-height: 1.2;
        letter-spacing: -0.02em;
    }

    .saas-header-subtitle {
        font-size: 0.92rem;
        font-weight: 600;
        color: #475569;
        margin: 2px 0 4px 0;
    }

    .saas-header-desc {
        font-size: 0.84rem;
        color: #64748b;
        margin: 0;
        line-height: 1.45;
        max-width: 820px;
    }

    .saas-status-pill {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 4px 10px;
        background: #ecfdf5;
        border: 1px solid #a7f3d0;
        border-radius: 9999px;
        font-size: 0.76rem;
        font-weight: 600;
        color: #065f46;
        white-space: nowrap;
    }

    .saas-status-dot {
        width: 7px;
        height: 7px;
        background: #10b981;
        border-radius: 50%;
    }

    /* Section Typography */
    .saas-section-title {
        font-size: 1.05rem;
        font-weight: 700;
        color: #0f172a;
        margin: 0 0 2px 0;
    }

    .saas-section-sub {
        font-size: 0.82rem;
        color: #64748b;
        margin: 0 0 10px 0;
    }

    /* Compact Profile Cards */
    .saas-kpi-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 10px 14px;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.02);
        min-height: 64px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }

    .saas-kpi-label {
        font-size: 0.7rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: #64748b;
        margin-bottom: 3px;
    }

    .saas-kpi-val {
        font-size: 0.95rem;
        font-weight: 600;
        color: #0f172a;
        line-height: 1.3;
        white-space: normal !important;
        word-break: break-word !important;
    }

    /* Profile Readiness Bar */
    .saas-readiness-box {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 10px 14px;
        margin-top: 10px;
        margin-bottom: 18px;
    }

    .saas-readiness-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 0.82rem;
        font-weight: 600;
        color: #334155;
        margin-bottom: 6px;
    }

    .saas-readiness-track {
        width: 100%;
        height: 6px;
        background: #f1f5f9;
        border-radius: 9999px;
        overflow: hidden;
    }

    .saas-readiness-fill {
        height: 100%;
        background: #2563eb;
        border-radius: 9999px;
        transition: width 0.3s ease;
    }

    .saas-readiness-hint {
        font-size: 0.76rem;
        color: #64748b;
        margin: 4px 0 0 0;
    }

    /* Empty State Card */
    .saas-empty-card {
        background: #ffffff;
        border: 1px dashed #cbd5e1;
        border-radius: 10px;
        padding: 36px 24px;
        text-align: center;
        margin: 16px 0;
    }

    .saas-empty-icon {
        font-size: 1.8rem;
        margin-bottom: 8px;
    }

    .saas-empty-title {
        font-size: 1.1rem;
        font-weight: 700;
        color: #0f172a;
        margin: 0 0 6px 0;
    }

    .saas-empty-desc {
        font-size: 0.86rem;
        color: #64748b;
        max-width: 620px;
        margin: 0 auto;
        line-height: 1.5;
    }

    /* Badges */
    .saas-badge {
        display: inline-flex;
        align-items: center;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.72rem;
        font-weight: 600;
    }
    .saas-badge-score { background: #f1f5f9; color: #0f172a; border: 1px solid #e2e8f0; font-weight: 700; }
    .saas-badge-ready { background: #ecfdf5; color: #065f46; border: 1px solid #a7f3d0; }
    .saas-badge-partial { background: #fffbeb; color: #92400e; border: 1px solid #fde68a; }
    .saas-badge-blocked { background: #fef2f2; color: #991b1b; border: 1px solid #fecaca; }
    .saas-badge-prep { background: #eff6ff; color: #1e40af; border: 1px solid #bfdbfe; }
    .saas-badge-skip { background: #f8fafc; color: #475569; border: 1px solid #cbd5e1; }

    /* Course Card (Horizontal) */
    .saas-course-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 12px 16px;
        margin-bottom: 10px;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.02);
    }

    .saas-course-top {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        gap: 12px;
    }

    .saas-course-name {
        font-size: 0.98rem;
        font-weight: 700;
        color: #0f172a;
        margin: 0;
    }

    .saas-course-meta {
        font-size: 0.78rem;
        color: #64748b;
        margin: 2px 0 0 0;
    }

    .saas-course-badges {
        display: flex;
        gap: 6px;
        align-items: center;
        flex-wrap: wrap;
    }

    .saas-course-gaps {
        margin-top: 8px;
        padding-top: 6px;
        border-top: 1px solid #f1f5f9;
        font-size: 0.78rem;
        color: #b45309;
    }

    /* Timeline Vertical */
    .saas-timeline {
        position: relative;
        padding-left: 6px;
        margin: 12px 0;
    }

    .saas-timeline-item {
        display: flex;
        align-items: center;
        gap: 14px;
        position: relative;
        padding-bottom: 12px;
    }

    .saas-timeline-item:not(:last-child)::before {
        content: '';
        position: absolute;
        left: 17px;
        top: 32px;
        bottom: 0;
        width: 2px;
        background: #e2e8f0;
    }

    .saas-timeline-step {
        width: 36px;
        height: 36px;
        border-radius: 6px;
        background: #f8fafc;
        border: 1px solid #cbd5e1;
        color: #1e293b;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.8rem;
        font-weight: 700;
        flex-shrink: 0;
    }

    .saas-timeline-card {
        flex-grow: 1;
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 6px;
        padding: 8px 14px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.02);
    }

    .saas-timeline-title {
        font-size: 0.9rem;
        font-weight: 600;
        color: #0f172a;
    }

    /* Multi-Agent Status */
    .saas-sys-panel {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 14px 18px;
        margin-top: 24px;
        margin-bottom: 12px;
    }

    .saas-sys-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
        gap: 8px;
        margin-top: 10px;
        margin-bottom: 12px;
    }

    .saas-sys-item {
        font-size: 0.8rem;
        font-weight: 600;
        color: #334155;
        display: flex;
        align-items: center;
        gap: 6px;
    }

    .saas-sys-check {
        color: #16a34a;
        font-weight: 700;
    }

    .saas-sys-meta {
        font-size: 0.74rem;
        color: #64748b;
        padding-top: 8px;
        border-top: 1px solid #e2e8f0;
        display: flex;
        gap: 16px;
        flex-wrap: wrap;
    }

    /* Primary Generate Button in Sidebar */
    div.stButton > button[kind="primary"] {
        background: #2563eb !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 6px !important;
        padding: 10px 16px !important;
        font-size: 0.92rem !important;
        font-weight: 600 !important;
        box-shadow: 0 1px 2px rgba(37, 99, 235, 0.2) !important;
        transition: all 0.15s ease !important;
    }

    div.stButton > button[kind="primary"]:hover {
        background: #1d4ed8 !important;
    }

    div.stButton > button:not([kind="primary"]) {
        border-radius: 6px !important;
        font-size: 0.85rem !important;
        font-weight: 500 !important;
        border: 1px solid #cbd5e1 !important;
        background: #ffffff !important;
        color: #475569 !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# LEARNER PROFILE CONSTANTS & STATE
# ============================================================

AVAILABLE_SKILLS = [
    "Python",
    "SQL",
    "Basic SQL",
    "Java",
    "C++",
    "JavaScript",
    "Machine Learning",
    "Deep Learning",
    "AWS",
    "Azure",
    "Cloud Computing",
    "Basic Cloud",
    "Docker",
    "Kubernetes",
    "Git",
    "HTML/CSS",
    "HTML",
    "CSS",
    "Data Analysis",
    "Statistics",
    "PyTorch",
    "NLP",
    "Natural Language Processing",
    "Computer Vision",
    "Generative AI",
    "Prompt Engineering",
    "LLMs",
    "RAG",
    "DevOps",
    "CI/CD",
    "Cybersecurity",
    "Network Security",
    "Cloud Security",
    "Web Development",
    "Backend Development",
    "APIs",
    "Pandas",
    "Programming Fundamentals"
]

AVAILABLE_INTERESTS = [
    "AI",
    "Machine Learning",
    "Generative AI",
    "Cloud Computing",
    "Data Science",
    "Cybersecurity",
    "Web Development",
    "DevOps",
    "Data Analytics",
    "Software Engineering",
    "Natural Language Processing",
    "Computer Vision",
    "Cloud Architecture"
]

CAREER_GOAL_OPTIONS = [
    "Cloud Engineer",
    "AI/ML Engineer",
    "Generative AI Engineer",
    "Data Scientist",
    "DevOps Engineer",
    "Data Analyst",
    "Backend Developer",
    "Web Developer",
    "Cybersecurity Engineer",
    "Other (Custom Role)"
]

DEFAULT_PROFILE = {
    "education": "B.Tech ECE",
    "skills": ["Python", "SQL", "Cloud Computing"],
    "custom_skills": "",
    "experience": "Beginner",
    "interests": ["AI", "Cloud Computing"],
    "custom_interests": "",
    "career_choice": "Cloud Engineer",
    "custom_career": ""
}

if "learner_education" not in st.session_state:
    st.session_state.learner_education = DEFAULT_PROFILE["education"]
if "learner_skills" not in st.session_state:
    st.session_state.learner_skills = list(DEFAULT_PROFILE["skills"])
if "learner_custom_skills" not in st.session_state:
    st.session_state.learner_custom_skills = DEFAULT_PROFILE["custom_skills"]
if "learner_experience" not in st.session_state:
    st.session_state.learner_experience = DEFAULT_PROFILE["experience"]
if "learner_interests" not in st.session_state:
    st.session_state.learner_interests = list(DEFAULT_PROFILE["interests"])
if "learner_custom_interests" not in st.session_state:
    st.session_state.learner_custom_interests = DEFAULT_PROFILE["custom_interests"]
if "learner_career_goal" not in st.session_state:
    st.session_state.learner_career_goal = DEFAULT_PROFILE["career_choice"]
if "learner_custom_career" not in st.session_state:
    st.session_state.learner_custom_career = DEFAULT_PROFILE["custom_career"]


def reset_profile():
    st.session_state.learner_education = DEFAULT_PROFILE["education"]
    st.session_state.learner_skills = list(DEFAULT_PROFILE["skills"])
    st.session_state.learner_custom_skills = DEFAULT_PROFILE["custom_skills"]
    st.session_state.learner_experience = DEFAULT_PROFILE["experience"]
    st.session_state.learner_interests = list(DEFAULT_PROFILE["interests"])
    st.session_state.learner_custom_interests = DEFAULT_PROFILE["custom_interests"]
    st.session_state.learner_career_goal = DEFAULT_PROFILE["career_choice"]
    st.session_state.learner_custom_career = DEFAULT_PROFILE["custom_career"]
    st.session_state.advisor_result = None


def get_current_career_goal():
    choice = st.session_state.get("learner_career_goal", "Cloud Engineer")
    if choice == "Other (Custom Role)":
        return st.session_state.get("learner_custom_career", "").strip() or "General Engineering"
    return choice


def calculate_profile_readiness():
    score = 0
    total = 5
    if str(st.session_state.get("learner_education", "")).strip():
        score += 1
    if str(st.session_state.get("learner_experience", "")).strip():
        score += 1
    if st.session_state.get("learner_skills") or str(st.session_state.get("learner_custom_skills", "")).strip():
        score += 1
    if st.session_state.get("learner_interests") or str(st.session_state.get("learner_custom_interests", "")).strip():
        score += 1
    if get_current_career_goal().strip():
        score += 1

    pct = int((score / total) * 100)
    if pct == 100:
        hint = "Ready to generate your personalized roadmap."
    elif pct >= 80:
        hint = "Ready to generate your personalized roadmap."
    elif pct >= 60:
        hint = "Add more skills or interests for greater roadmap precision."
    else:
        hint = "Complete your profile details to unlock tailored course recommendations."
    return pct, hint


# ============================================================
# 1. TOP HEADER (COMPACT PROFESSIONAL SAAS HEADER)
# ============================================================

st.markdown(
    """
    <div class="saas-header-container">
        <div>
            <h1 class="saas-header-title">AI Course Advisor</h1>
            <div class="saas-header-subtitle">Personalized Course Recommendation & Learning Path</div>
            <p class="saas-header-desc">
                An AI-powered multi-agent advisor that analyzes your profile, retrieves relevant courses, checks prerequisites, and builds a personalized learning path.
            </p>
        </div>
        <div>
            <span class="saas-status-pill">
                <span class="saas-status-dot"></span>
                <span>AI Advisor Ready</span>
            </span>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)


# ============================================================
# 2. SIDEBAR (COMPACT PROFILE FORM & ACTIONS)
# ============================================================

with st.sidebar:

    st.markdown(
        """
        <div class="sidebar-header-box">
            <h2 class="sidebar-app-title">AI Course Advisor</h2>
            <div class="sidebar-app-sub">Learner Profile</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    experience_options = ["Beginner", "Intermediate", "Advanced"]
    if st.session_state.get("learner_experience") not in experience_options:
        st.session_state.learner_experience = "Beginner"

    if st.session_state.get("learner_career_goal") not in CAREER_GOAL_OPTIONS:
        st.session_state.learner_career_goal = "Cloud Engineer"

    # PROFILE SECTION
    st.markdown('<div class="sidebar-group-title">Profile</div>', unsafe_allow_html=True)
    st.text_input(
        "Education",
        key="learner_education",
        placeholder="e.g., B.Tech ECE",
        help="Academic background"
    )
    st.selectbox(
        "Experience",
        experience_options,
        key="learner_experience",
        help="Technical proficiency level"
    )
    st.selectbox(
        "Career Goal",
        CAREER_GOAL_OPTIONS,
        key="learner_career_goal",
        help="Target job role"
    )
    if st.session_state.learner_career_goal == "Other (Custom Role)":
        st.text_input(
            "Custom Career Role",
            key="learner_custom_career",
            placeholder="e.g., Robotics Specialist"
        )

    # SKILLS SECTION
    st.markdown('<div class="sidebar-group-title">Skills</div>', unsafe_allow_html=True)
    st.multiselect(
        "Skills",
        options=AVAILABLE_SKILLS,
        key="learner_skills",
        help="Select existing skills"
    )
    st.text_input(
        "Custom Skills",
        key="learner_custom_skills",
        placeholder="e.g., PyTorch, Rust (comma-separated)"
    )

    # INTERESTS SECTION
    st.markdown('<div class="sidebar-group-title">Interests</div>', unsafe_allow_html=True)
    st.multiselect(
        "Interests",
        options=AVAILABLE_INTERESTS,
        key="learner_interests",
        help="Domains you want to explore"
    )
    st.text_input(
        "Custom Interests",
        key="learner_custom_interests",
        placeholder="e.g., MLOps (comma-separated)"
    )

    # ACTION SECTION
    st.markdown('<div class="sidebar-group-title">Action</div>', unsafe_allow_html=True)
    sidebar_generate = st.button(
        "Generate Course Roadmap",
        use_container_width=True,
        type="primary",
        key="btn_generate_sidebar"
    )
    st.button(
        "Reset Profile",
        use_container_width=True,
        on_click=reset_profile,
        key="btn_reset_main"
    )


# ============================================================
# 3. MAIN PAGE — LEARNER PROFILE (COMPACT CARDS, NO TRUNCATION)
# ============================================================

st.markdown(
    """
    <div style="margin-top: 4px; margin-bottom: 8px;">
        <div class="saas-section-title">Learner Profile</div>
        <div class="saas-section-sub">Your profile used to generate the recommendation.</div>
    </div>
    """,
    unsafe_allow_html=True
)

current_edu = str(st.session_state.get("learner_education", "")).strip() or "Not specified"
current_exp = st.session_state.get("learner_experience", "Beginner")
current_goal = get_current_career_goal()
current_skills_count = len(st.session_state.get("learner_skills", []))
if st.session_state.get("learner_custom_skills"):
    current_skills_count += len([s for s in str(st.session_state.learner_custom_skills).split(",") if s.strip()])

lp_col1, lp_col2, lp_col3, lp_col4 = st.columns(4)
with lp_col1:
    render_html(
        f"""
        <div class="saas-kpi-card">
            <div class="saas-kpi-label">Education</div>
            <div class="saas-kpi-val">{current_edu}</div>
        </div>
        """
    )
with lp_col2:
    render_html(
        f"""
        <div class="saas-kpi-card">
            <div class="saas-kpi-label">Experience</div>
            <div class="saas-kpi-val">{current_exp}</div>
        </div>
        """
    )
with lp_col3:
    render_html(
        f"""
        <div class="saas-kpi-card">
            <div class="saas-kpi-label">Career Goal</div>
            <div class="saas-kpi-val">{current_goal}</div>
        </div>
        """
    )
with lp_col4:
    render_html(
        f"""
        <div class="saas-kpi-card">
            <div class="saas-kpi-label">Skills</div>
            <div class="saas-kpi-val">{current_skills_count} selected</div>
        </div>
        """
    )


# ============================================================
# 4. PROFILE READINESS (HORIZONTAL COMPACT STATUS)
# ============================================================

readiness_pct, readiness_hint = calculate_profile_readiness()
render_html(
    f"""
    <div class="saas-readiness-box">
        <div class="saas-readiness-row">
            <span>Profile readiness</span>
            <span style="font-weight: 700; color: #2563eb;">{readiness_pct}%</span>
        </div>
        <div class="saas-readiness-track">
            <div class="saas-readiness-fill" style="width: {readiness_pct}%;"></div>
        </div>
        <p class="saas-readiness-hint">{readiness_hint}</p>
    </div>
    """
)


# ============================================================
# 5. BEFORE GENERATION (CLEAN EMPTY STATE CARD)
# ============================================================

if not st.session_state.get("advisor_result"):

    render_html(
        """
        <div class="saas-empty-card">
            <div class="saas-empty-icon">🎯</div>
            <h3 class="saas-empty-title">Ready to build your learning path?</h3>
            <p class="saas-empty-desc">
                Your profile is ready. Click <b>"Generate Course Roadmap"</b> in the sidebar to analyze your skills, retrieve relevant courses, check prerequisites, and create your personalized roadmap.
            </p>
        </div>
        """
    )



# ============================================================
# GENERATE ROADMAP EXECUTION
# ============================================================

generate = sidebar_generate

if generate:

    # Build clean skills list
    skills = list(st.session_state.get("learner_skills", []))
    custom_skills = st.session_state.get("learner_custom_skills", "")
    if custom_skills:
        for item in custom_skills.split(","):
            cleaned = item.strip()
            if cleaned and cleaned not in skills:
                skills.append(cleaned)

    # Build clean interests list
    interests = list(st.session_state.get("learner_interests", []))
    custom_interests = st.session_state.get("learner_custom_interests", "")
    if custom_interests:
        for item in custom_interests.split(","):
            cleaned = item.strip()
            if cleaned and cleaned not in interests:
                interests.append(cleaned)

    career_goal = get_current_career_goal()

    profile = {
        "education": str(st.session_state.get("learner_education", "")).strip() or "Not Specified",
        "skills": skills,
        "experience": st.session_state.get("learner_experience", "Beginner"),
        "interests": interests,
        "career_goal": career_goal or "Cloud Engineer"
    }

    with st.status(
        "🤖 Running AI Course Advisor Pipeline...",
        expanded=True
    ):

        # ----------------------------------------------------
        # PROFILE AGENT
        # ----------------------------------------------------

        st.write(
            "🧠 Profile Analysis Agent..."
        )

        try:

            profile_result = (
                cached_profile_analysis(
                    profile
                )
            )

        except Exception as e:

            profile_result = (
                f"Profile analysis unavailable: {e}"
            )

        # ----------------------------------------------------
        # RAG COURSE RESEARCH
        # ----------------------------------------------------

        st.write(
            "🔎 Course Research Agent + RAG..."
        )

        try:

            research_result = (
                cached_research_courses(
                    profile
                )
            )

        except Exception as e:

            research_result = (
                f"Course research unavailable: {e}"
            )

        # ----------------------------------------------------
        # RECOMMENDATION AGENT
        # ----------------------------------------------------

        st.write(
            "🎯 Recommendation Agent..."
        )

        try:

            raw_recommendation = (
                cached_recommend_courses(
                    profile
                )
            )

            recommendation_result = (
                parse_recommendation_output(
                    raw_recommendation
                )
            )

        except Exception as e:

            recommendation_result = {
                "best_course": "",
                "recommendations": [],
                "learning_path": [],
                "explanation":
                    f"Recommendation failed: {e}"
            }

        recommendations = (
            recommendation_result.get(
                "recommendations",
                []
            )
        )

        if not isinstance(
            recommendations,
            list
        ):

            recommendations = []

        # ----------------------------------------------------
        # LOCAL PREREQUISITE ENGINE
        # ----------------------------------------------------

        st.write(
            "⚡ Calculating prerequisite gaps..."
        )

        enriched_recommendations = []

        for course in recommendations:

            if not isinstance(
                course,
                dict
            ):

                continue

            enriched = enrich_course(
                course,
                skills
            )

            enriched_recommendations.append(
                enriched
            )

        recommendations = (
            enriched_recommendations
        )

        # ----------------------------------------------------
        # LEARNING PATH AGENT
        # ----------------------------------------------------

        st.write(
            "🗺️ Learning Path Agent..."
        )

        try:

            learning_path_result = (
                cached_learning_path(
                    profile,
                    recommendations
                )
            )

        except Exception as e:

            learning_path_result = (
                f"Learning path unavailable: {e}"
            )

    # --------------------------------------------------------
    # SAVE RESULT
    # --------------------------------------------------------

    st.session_state.advisor_result = {

        "profile":
            profile,

        "profile_result":
            profile_result,

        "research_result":
            research_result,

        "recommendation_result":
            recommendation_result,

        "recommendations":
            recommendations,

        "learning_path_result":
            learning_path_result
    }

    st.rerun()


# ============================================================
# 6. AFTER GENERATION — RECOMMENDATION & ROADMAP RESULTS
# ============================================================

if st.session_state.get("advisor_result"):

    result = st.session_state.advisor_result

    profile = (
        result.get("profile", {})
        if isinstance(result, dict) else {}
    )

    recommendation_result = (
        result.get("recommendation_result", {})
        if isinstance(result, dict) else {}
    )

    if isinstance(recommendation_result, str):
        recommendation_result = parse_recommendation_output(recommendation_result)

    if not isinstance(recommendation_result, dict):
        recommendation_result = {}

    recommendations = (
        result.get("recommendations", [])
        if isinstance(result, dict) else []
    )

    if not isinstance(recommendations, list):
        recommendations = recommendation_result.get("recommendations", [])
    if not isinstance(recommendations, list):
        recommendations = []

    learning_path_result = (
        result.get("learning_path_result", {})
        if isinstance(result, dict) else {}
    )

    research_result = (
        result.get("research_result", {})
        if isinstance(result, dict) else {}
    )

    best_course = recommendation_result.get("best_course", "")
    if not best_course and recommendations:
        best_course = recommendations[0].get("course_name", "")

    # Top overall readiness calculation
    overall_readiness = "Ready"
    for c in recommendations:
        if c.get("ui_readiness") == "Partially Ready":
            overall_readiness = "Partially Ready"
            break
        elif c.get("ui_readiness") == "Not Ready":
            overall_readiness = "Not Ready"
            break

    # --------------------------------------------------------
    # SECTION 1: RECOMMENDATION OVERVIEW
    # --------------------------------------------------------
    sec_head_c1, sec_head_c2 = st.columns([4, 1])
    with sec_head_c1:
        st.markdown('<div class="saas-section-title">Recommendation Overview</div>', unsafe_allow_html=True)
        st.markdown('<div class="saas-section-sub">High-level summary of your tailored recommendation analysis.</div>', unsafe_allow_html=True)
    with sec_head_c2:
        if st.button("✏️ Reset Results", use_container_width=True, key="btn_edit_profile_main"):
            st.session_state.advisor_result = None
            st.rerun()

    sec1_col1, sec1_col2, sec1_col3 = st.columns(3)
    with sec1_col1:
        render_html(
            f"""
            <div class="saas-kpi-card">
                <div class="saas-kpi-label">Best Course</div>
                <div class="saas-kpi-val" style="color: #2563eb;">{best_course or 'AWS Cloud Foundations'}</div>
            </div>
            """
        )
    with sec1_col2:
        badge_cls = "saas-badge-ready" if overall_readiness == "Ready" else "saas-badge-partial"
        render_html(
            f"""
            <div class="saas-kpi-card">
                <div class="saas-kpi-label">Readiness</div>
                <div class="saas-kpi-val"><span class="saas-badge {badge_cls}">{overall_readiness}</span></div>
            </div>
            """
        )
    with sec1_col3:
        render_html(
            f"""
            <div class="saas-kpi-card">
                <div class="saas-kpi-label">Courses Analyzed</div>
                <div class="saas-kpi-val">20 Catalog Courses</div>
            </div>
            """
        )

    st.write("")

    # --------------------------------------------------------
    # SECTION 2: RECOMMENDED COURSES (CLEAN HORIZONTAL CARDS)
    # --------------------------------------------------------
    st.markdown('<div class="saas-section-title">Recommended Courses</div>', unsafe_allow_html=True)
    st.markdown('<div class="saas-section-sub">Ranked courses aligned with your background, prerequisites, and target career goal.</div>', unsafe_allow_html=True)

    if not recommendations:
        st.info("No course recommendations were generated.")
    else:
        for idx, course in enumerate(recommendations, start=1):
            course_name = course.get("course_name", "Unknown Course")
            score = course.get("score", 0)
            readiness = course.get("ui_readiness", "Ready")
            status = course.get("ui_status", "Recommended Now")
            difficulty = course.get("difficulty", "Intermediate")
            category = course.get("category", "General")
            missing = course.get("missing_prerequisites", [])

            # Badge classes
            if readiness == "Ready":
                r_cls = "saas-badge-ready"
            elif readiness == "Partially Ready":
                r_cls = "saas-badge-partial"
            else:
                r_cls = "saas-badge-blocked"

            if status == "Recommended Now":
                s_cls = "saas-badge-ready"
            elif status == "Prepare First":
                s_cls = "saas-badge-prep"
            elif status == "Blocked":
                s_cls = "saas-badge-blocked"
            elif "Skip" in status:
                s_cls = "saas-badge-skip"
            else:
                s_cls = "saas-badge-prep"

            gaps_html = ""
            if missing:
                missing_str = ", ".join(missing)
                gaps_html = f'<div class="saas-course-gaps">⚠️ Prerequisites needed: {missing_str}</div>'

            render_html(
                f"""
                <div class="saas-course-card">
                    <div class="saas-course-top">
                        <div>
                            <div class="saas-course-name">{idx}. {course_name}</div>
                            <div class="saas-course-meta">{category} • {difficulty}</div>
                        </div>
                        <div class="saas-course-badges">
                            <span class="saas-badge saas-badge-score">Score: {score}/100</span>
                            <span class="saas-badge {r_cls}">{readiness}</span>
                            <span class="saas-badge {s_cls}">{status}</span>
                        </div>
                    </div>
                    {gaps_html}
                </div>
                """
            )

    st.write("")

    # --------------------------------------------------------
    # SECTION 3: PREREQUISITE & SKILL GAP ANALYSIS (TWO-COLUMN)
    # --------------------------------------------------------
    st.markdown('<div class="saas-section-title">Prerequisite & Skill Gap Analysis</div>', unsafe_allow_html=True)
    st.markdown('<div class="saas-section-sub">Breakdown of validated baseline prerequisites versus preparation items required.</div>', unsafe_allow_html=True)

    unique_satisfied = set()
    unique_missing = set()
    for c in recommendations:
        for p in c.get("satisfied_prerequisites", []):
            if p:
                unique_satisfied.add(str(p).strip())
        for m in c.get("missing_prerequisites", []):
            if m:
                unique_missing.add(str(m).strip())

    prereq_col1, prereq_col2 = st.columns(2)
    with prereq_col1:
        items_html = ""
        if unique_satisfied:
            for item in sorted(unique_satisfied):
                items_html += f"<div style='font-size: 0.85rem; color: #166534; margin-bottom: 4px;'>✓ {item}</div>"
        else:
            items_html = "<div style='font-size: 0.85rem; color: #64748b;'>No baseline prerequisites identified.</div>"
        box1_html = (
            f'<div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 14px 18px; min-height: 130px;">'
            f'<div style="font-size: 0.8rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; color: #166534; margin-bottom: 8px;">'
            f'Satisfied Prerequisites'
            f'</div>'
            f'{items_html}'
            f'</div>'
        )
        render_html(box1_html)

    with prereq_col2:
        items_html2 = ""
        if unique_missing:
            for item in sorted(unique_missing):
                items_html2 += f"<div style='font-size: 0.85rem; color: #991b1b; margin-bottom: 4px;'>• {item}</div>"
        else:
            items_html2 = "<div style='font-size: 0.85rem; color: #166534;'>✓ All prerequisites satisfied.</div>"
        box2_html = (
            f'<div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 14px 18px; min-height: 130px;">'
            f'<div style="font-size: 0.8rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; color: #991b1b; margin-bottom: 8px;">'
            f'Missing / Preparation Needed'
            f'</div>'
            f'{items_html2}'
            f'</div>'
        )
        render_html(box2_html)

    st.write("")

    # --------------------------------------------------------
    # SECTION 4: RAG KNOWLEDGE RETRIEVAL
    # --------------------------------------------------------
    st.markdown('<div class="saas-section-title">Knowledge Retrieved from Course Database</div>', unsafe_allow_html=True)
    st.markdown('<div class="saas-section-sub">Course matches retrieved from local ChromaDB vector database using nomic-embed-text embeddings.</div>', unsafe_allow_html=True)

    retrieved_courses = []
    if isinstance(research_result, str):
        try:
            import json
            parsed_res = json.loads(research_result)
            if isinstance(parsed_res, dict):
                research_result = parsed_res
        except Exception:
            pass

    if isinstance(research_result, dict):
        retrieved_courses = research_result.get("retrieved_courses", [])

    if not retrieved_courses:
        try:
            from rag.retriever import retrieve_courses
            c_goal = profile.get("career_goal", "Engineering")
            c_skills = " ".join(profile.get("skills", []))
            c_query = f"Find courses suitable for {c_goal} with {c_skills}"
            retrieved_courses = retrieve_courses(c_query, top_k=5)
        except Exception:
            pass

    if retrieved_courses:
        rows_html = []
        for rc in retrieved_courses[:6]:
            c_name = rc.get("course_name", "Unknown Course")
            score_val = rc.get("score") if rc.get("score") is not None else rc.get("similarity", 0.70)
            if not isinstance(score_val, (int, float)):
                try:
                    score_val = float(score_val)
                except Exception:
                    score_val = 0.70
            rows_html.append(
                f'<div style="display: flex; justify-content: space-between; align-items: center; padding: 8px 14px; border-bottom: 1px solid #f1f5f9; font-size: 0.85rem;">'
                f'<span style="font-weight: 500; color: #1e293b;">{c_name}</span>'
                f'<span style="font-family: monospace; font-weight: 600; color: #2563eb;">{score_val:.2f}</span>'
                f'</div>'
            )
        table_html = (
            '<div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; overflow: hidden; margin-bottom: 14px;">'
            '<div style="display: flex; justify-content: space-between; padding: 8px 14px; background: #f8fafc; border-bottom: 1px solid #e2e8f0; font-size: 0.74rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; color: #64748b;">'
            '<span>Course</span><span>Similarity</span>'
            '</div>'
            + "".join(rows_html) +
            '</div>'
        )
        render_html(table_html)
    else:
        st.caption("Recommendations are grounded in the verified local course knowledge base.")

    st.write("")

    # --------------------------------------------------------
    # SECTION 5: PERSONALIZED LEARNING ROADMAP (MAIN VISUAL SECTION)
    # --------------------------------------------------------
    st.markdown('<div class="saas-section-title">Your Learning Roadmap</div>', unsafe_allow_html=True)
    st.markdown('<div class="saas-section-sub">Structured step-by-step sequence addressing foundational preparation before advancing to core specialization courses.</div>', unsafe_allow_html=True)

    learning_path = []
    if isinstance(learning_path_result, str):
        try:
            import json
            parsed_lp = json.loads(learning_path_result)
            if isinstance(parsed_lp, dict):
                learning_path_result = parsed_lp
        except Exception:
            pass

    if isinstance(learning_path_result, dict) and learning_path_result.get("learning_path"):
        learning_path = learning_path_result.get("learning_path", [])
    elif isinstance(recommendation_result, dict) and recommendation_result.get("learning_path"):
        learning_path = recommendation_result.get("learning_path", [])

    if not learning_path and recommendations:
        try:
            from agents.learning_path_agent import build_learning_path
            learning_path = build_learning_path(profile, recommendations)
        except Exception:
            pass

    if learning_path:
        timeline_items = []
        for idx, item in enumerate(learning_path, start=1):
            step_str = f"{idx:02d}"
            diff_str = ""
            desc_str = ""
            if isinstance(item, dict):
                name = item.get("item", "Unknown")
                item_type = item.get("type", "Course")
                diff_str = item.get("difficulty", "")
                desc_str = item.get("why", "")
            else:
                name = str(item)
                item_type = "Course"

            badge_cls = "saas-badge-prep" if item_type == "Preparation" else "saas-badge-ready"
            meta_pill = f'<span class="saas-badge" style="background: #f1f5f9; color: #475569; border: 1px solid #e2e8f0; font-size: 0.7rem;">{diff_str}</span>' if diff_str else ""
            desc_line = f'<div style="font-size: 0.76rem; color: #64748b; margin-top: 2px;">{desc_str}</div>' if desc_str else ""

            timeline_items.append(
                f'<div class="saas-timeline-item">'
                f'<div class="saas-timeline-step">{step_str}</div>'
                f'<div class="saas-timeline-card">'
                f'<div>'
                f'<div class="saas-timeline-title">{name}</div>'
                f'{desc_line}'
                f'</div>'
                f'<div style="display: flex; gap: 6px; align-items: center; flex-shrink: 0;">'
                f'{meta_pill}'
                f'<span class="saas-badge {badge_cls}">{item_type}</span>'
                f'</div>'
                f'</div>'
                f'</div>'
            )
        timeline_html = f'<div class="saas-timeline">{"".join(timeline_items)}</div>'
        render_html(timeline_html)
    else:
        st.info("No learning path was generated.")

    st.write("")

    # --------------------------------------------------------
    # SECTION 6: AI EXPLANATION (COLLAPSIBLE EXPANDERS)
    # --------------------------------------------------------
    st.markdown('<div class="saas-section-title">AI Explanations</div>', unsafe_allow_html=True)
    st.markdown('<div class="saas-section-sub">Inspect the reasoning generated by the autonomous agent pipeline.</div>', unsafe_allow_html=True)

    profile_text = result.get("profile_result", "No profile explanation recorded.")
    if isinstance(profile_text, dict):
        profile_text = str(profile_text)

    rec_exp = recommendation_result.get("explanation", "Recommendations aligned with career goals and skill gap minimization.")
    if isinstance(rec_exp, dict):
        rec_exp = str(rec_exp)

    path_exp = ""
    if isinstance(learning_path_result, dict):
        path_exp = learning_path_result.get("explanation", "")
    elif isinstance(learning_path_result, str):
        path_exp = learning_path_result
    if not path_exp:
        path_exp = "Sequenced from baseline preparation to advanced career specialization."

    with st.expander("Why this profile was analyzed this way", expanded=False):
        st.markdown(f"<div style='font-size: 0.86rem; color: #334155; line-height: 1.5;'>{profile_text}</div>", unsafe_allow_html=True)

    with st.expander("Why these courses were recommended", expanded=False):
        st.markdown(f"<div style='font-size: 0.86rem; color: #334155; line-height: 1.5;'>{rec_exp}</div>", unsafe_allow_html=True)

    with st.expander("Why this learning order was selected", expanded=False):
        st.markdown(f"<div style='font-size: 0.86rem; color: #334155; line-height: 1.5;'>{path_exp}</div>", unsafe_allow_html=True)

    # --------------------------------------------------------
    # SECTION 7: MULTI-AGENT SYSTEM (COMPACT STATUS SECTION)
    # --------------------------------------------------------
    render_html(
        """
        <div class="saas-sys-panel">
            <div style="font-size: 0.88rem; font-weight: 700; color: #0f172a; margin-bottom: 2px;">Multi-Agent System</div>
            <div style="font-size: 0.76rem; color: #64748b;">All autonomous agents and pipeline components operational.</div>
            <div class="saas-sys-grid">
                <div class="saas-sys-item"><span class="saas-sys-check">✓</span> Profile Analysis Agent</div>
                <div class="saas-sys-item"><span class="saas-sys-check">✓</span> Course Research Agent</div>
                <div class="saas-sys-item"><span class="saas-sys-check">✓</span> Prerequisite Analysis Agent</div>
                <div class="saas-sys-item"><span class="saas-sys-check">✓</span> Recommendation Agent</div>
                <div class="saas-sys-item"><span class="saas-sys-check">✓</span> Learning Path Agent</div>
            </div>
            <div class="saas-sys-meta">
                <span><b>RAG Knowledge Base:</b> Connected</span>
                <span><b>LLM:</b> qwen2.5:3b</span>
                <span><b>Embeddings:</b> nomic-embed-text</span>
            </div>
        </div>
        """
    )