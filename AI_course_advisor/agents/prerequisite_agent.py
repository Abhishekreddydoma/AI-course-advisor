import json
import urllib.request
from pathlib import Path


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

COURSES_FILE = PROJECT_ROOT / "data" / "raw" / "courses.json"


# ============================================================
# OLLAMA
# ============================================================

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "qwen2.5:3b"


def ask_ollama(prompt):
    """
    Send a prompt to the local Ollama model.
    """

    data = json.dumps({
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False
    }).encode("utf-8")

    request = urllib.request.Request(
        OLLAMA_URL,
        data=data,
        headers={
            "Content-Type": "application/json"
        }
    )

    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            result = json.loads(response.read().decode("utf-8"))
        return result.get("response", "").strip()
    except Exception as error:
        return f"AI prerequisite explanation unavailable: {error}"


# ============================================================
# LOAD COURSE DATA
# ============================================================

def load_courses():
    """
    Load course knowledge base from courses.json.
    """

    with open(COURSES_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


# ============================================================
# FIND COURSE
# ============================================================

def find_course(course_name, courses):
    """
    Find a course by name.
    """

    course_name = str(course_name).strip().lower()

    for course in courses:
        if course["course_name"].strip().lower() == course_name:
            return course

    return None


# ============================================================
# NORMALIZE SKILLS
# ============================================================

def normalize_skills(skills):
    """
    Convert learner skills into a clean lowercase set.

    Handles:
    - list
    - tuple
    - string
    - None
    """

    if skills is None:
        return set()

    if isinstance(skills, str):
        skills = [skills]

    elif isinstance(skills, (list, tuple, set)):
        skills = list(skills)

    else:
        skills = [str(skills)]

    return {
        str(skill).strip().lower()
        for skill in skills
        if str(skill).strip()
    }


# ============================================================
# CHECK PREREQUISITES
# ============================================================

def check_prerequisites(course, learner_skills):
    """
    Deterministically check which prerequisites are satisfied.
    """

    prerequisites = course.get("prerequisites", [])

    skill_set = normalize_skills(learner_skills)

    satisfied = []
    missing = []

    for prerequisite in prerequisites:

        prerequisite_normalized = (
            str(prerequisite)
            .strip()
            .lower()
        )

        # ----------------------------------------------------
        # Baseline prerequisite
        # ----------------------------------------------------

        if prerequisite_normalized == "basic computer knowledge":
            satisfied.append(prerequisite)
            continue

        # ----------------------------------------------------
        # Direct skill match
        # ----------------------------------------------------

        if prerequisite_normalized in skill_set:
            satisfied.append(prerequisite)
            continue

        # ----------------------------------------------------
        # Common equivalent skill handling
        # ----------------------------------------------------

        equivalent_found = False

        for skill in skill_set:

            # Python
            if (
                prerequisite_normalized == "python"
                and "python" in skill
            ):
                equivalent_found = True
                break

            # Machine Learning Fundamentals
            if (
                prerequisite_normalized
                == "machine learning fundamentals"
                and (
                    "machine learning fundamentals" in skill
                    or skill == "machine learning"
                )
            ):
                equivalent_found = True
                break

            # Deep Learning
            if (
                prerequisite_normalized == "deep learning"
                and "deep learning" in skill
            ):
                equivalent_found = True
                break

            # AWS Cloud Foundations
            if (
                prerequisite_normalized
                == "aws cloud foundations"
                and (
                    "aws cloud foundations" in skill
                    or skill == "aws"
                )
            ):
                equivalent_found = True
                break

        if equivalent_found:
            satisfied.append(prerequisite)
        else:
            missing.append(prerequisite)

    # ========================================================
    # READINESS
    # ========================================================

    if len(missing) == 0:
        readiness = "Ready"

    elif len(satisfied) > 0:
        readiness = "Partially Ready"

    else:
        readiness = "Not Ready"

    return {
        "satisfied": satisfied,
        "missing": missing,
        "readiness": readiness
    }


# ============================================================
# AI EXPLANATION
# ============================================================

def generate_explanation(
    course,
    learner_skills,
    satisfied,
    missing,
    readiness
):
    """
    Ask Qwen to explain the prerequisite analysis.

    The model explains the deterministic result.
    It does NOT decide the result.
    """

    prompt = f"""
You are the Prerequisite Analysis Agent of an AI Course Advisor.

Explain the prerequisite analysis clearly and concisely.

COURSE:
{json.dumps(course, indent=2)}

LEARNER SKILLS:
{json.dumps(learner_skills, indent=2)}

SYSTEM-CALCULATED SATISFIED PREREQUISITES:
{json.dumps(satisfied, indent=2)}

SYSTEM-CALCULATED MISSING PREREQUISITES:
{json.dumps(missing, indent=2)}

SYSTEM-CALCULATED READINESS:
{readiness}

IMPORTANT RULES:
1. Do not change the calculated readiness.
2. Do not add new prerequisites.
3. Do not invent courses.
4. Use only the course information provided.
5. Do not claim a skill is present unless it appears in the learner skills
   or was marked satisfied by the system.
6. Clearly distinguish satisfied and missing prerequisites.
7. Keep the explanation suitable for a student.

Return:

1. Readiness
2. Prerequisites already satisfied
3. Prerequisites still missing
4. Short explanation
"""

    try:
        return ask_ollama(prompt)

    except Exception as error:
        return (
            f"Readiness: {readiness}\n\n"
            f"Satisfied prerequisites: "
            f"{', '.join(satisfied) if satisfied else 'None'}\n\n"
            f"Missing prerequisites: "
            f"{', '.join(missing) if missing else 'None'}\n\n"
            f"AI explanation unavailable: {error}"
        )


# ============================================================
# MAIN AGENT FUNCTION
# ============================================================

def analyze_prerequisites(course_name, learner_skills):
    """
    Main Prerequisite Analysis Agent.

    Parameters:
        course_name: Course name
        learner_skills: List of learner skills

    Returns:
        Structured prerequisite analysis.
    """

    courses = load_courses()

    course = find_course(course_name, courses)

    if course is None:
        return {
            "course_name": course_name,
            "readiness": "Unknown",
            "satisfied": [],
            "missing": [],
            "error": f"Course not found: {course_name}"
        }

    result = check_prerequisites(
        course,
        learner_skills
    )

    explanation = generate_explanation(
        course,
        learner_skills,
        result["satisfied"],
        result["missing"],
        result["readiness"]
    )

    return {
        "course_id": course["course_id"],
        "course_name": course["course_name"],
        "prerequisites": course.get("prerequisites", []),
        "satisfied": result["satisfied"],
        "missing": result["missing"],
        "readiness": result["readiness"],
        "explanation": explanation
    }


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    profile_skills = [
        "Python",
        "Basic SQL",
        "Basic Cloud"
    ]

    test_courses = [
        "Machine Learning Fundamentals",
        "Deep Learning with Neural Networks",
        "Generative AI and LLMs"
    ]

    print("\n" + "=" * 70)
    print("              PREREQUISITE ANALYSIS AGENT")
    print("=" * 70)

    for course_name in test_courses:

        print("\n" + "-" * 60)
        print(f"Course: {course_name}")
        print("-" * 60)

        result = analyze_prerequisites(
            course_name,
            profile_skills
        )

        print(f"\nReadiness: {result['readiness']}")

        print("\nSatisfied:")
        if result["satisfied"]:
            for item in result["satisfied"]:
                print(f"   [OK] {item}")
        else:
            print("   None")

        print("\nMissing:")
        if result["missing"]:
            for item in result["missing"]:
                print(f"   [X] {item}")
        else:
            print("   None")

        print("\nAI Explanation:")
        print(result["explanation"])