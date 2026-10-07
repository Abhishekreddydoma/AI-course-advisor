import json
import urllib.request
from pathlib import Path


# ============================================================
# CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

COURSES_FILE = PROJECT_ROOT / "data" / "raw" / "courses.json"

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "qwen2.5:3b"


# ============================================================
# OLLAMA
# ============================================================

def ask_ollama(prompt):

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

        response = urllib.request.urlopen(
            request,
            timeout=120
        )

        result = json.loads(
            response.read().decode("utf-8")
        )

        return result.get(
            "response",
            ""
        ).strip()

    except Exception as error:

        return (
            "AI explanation unavailable: "
            + str(error)
        )


# ============================================================
# LOAD COURSE DATABASE
# ============================================================

def load_courses():

    with open(
        COURSES_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        return json.load(file)


# ============================================================
# FIND COURSE
# ============================================================

def find_course(course_name, courses):

    target = course_name.strip().lower()

    for course in courses:

        if course["course_name"].strip().lower() == target:

            return course

    return None


# ============================================================
# BUILD LEARNING PATH
# ============================================================

def build_learning_path(
    profile,
    recommendations
):

    courses = load_courses()

    path = []

    added = set()

    # --------------------------------------------------------
    # Find Machine Learning Fundamentals
    # --------------------------------------------------------

    ml_recommendation = None

    for recommendation in recommendations:

        if recommendation.get(
            "course_name"
        ) == "Machine Learning Fundamentals":

            ml_recommendation = recommendation
            break

    # --------------------------------------------------------
    # Add missing prerequisites
    # --------------------------------------------------------

    if ml_recommendation:

        missing_prerequisites = (
            ml_recommendation.get(
                "missing_prerequisites",
                []
            )
        )

        for prerequisite in missing_prerequisites:

            key = prerequisite.strip().lower()

            if key not in added:

                path.append({
                    "step": len(path) + 1,
                    "item": prerequisite,
                    "type": "Preparation",
                    "difficulty": "Foundation",
                    "why": (
                        "This preparation is required before "
                        "Machine Learning Fundamentals."
                    ),
                    "skills_gained": [
                        prerequisite
                    ],
                    "prerequisites": []
                })

                added.add(key)

    # --------------------------------------------------------
    # Dependency-aware course order
    # --------------------------------------------------------

    course_order = [
        "Machine Learning Fundamentals",
        "Deep Learning with Neural Networks",
        "Generative AI and LLMs",
        "AWS Cloud Foundations",
        "AWS Solutions Architect Fundamentals"
    ]

    # --------------------------------------------------------
    # Add courses to path
    # --------------------------------------------------------

    for course_name in course_order:

        recommendation = None

        for item in recommendations:

            if item.get(
                "course_name"
            ) == course_name:

                recommendation = item
                break

        if recommendation is None:
            continue

        # ----------------------------------------------------
        # Skip already-known courses
        # ----------------------------------------------------

        status_val = (
            recommendation.get("status")
            or recommendation.get("ui_status")
        )

        if (
            status_val == "Skip - Skill Already Present"
            or recommendation.get("score") == 0
        ):

            continue

        course = find_course(
            course_name,
            courses
        )

        if course is None:
            continue

        key = course_name.strip().lower()

        if key in added:
            continue

        path.append({
            "step": len(path) + 1,
            "item": course["course_name"],
            "type": "Course",
            "difficulty": course["difficulty"],
            "why": (
                "This course follows the prerequisite and "
                "career progression for the learner."
            ),
            "skills_gained": course.get(
                "skills",
                []
            ),
            "prerequisites": course.get(
                "prerequisites",
                []
            )
        })

        added.add(key)

    # Also include top recommendations to ensure all career paths have a complete roadmap
    for item in recommendations:
        if len(path) >= 7:
            break
        c_name = item.get("course_name")
        if not c_name:
            continue
        c_status = item.get("status") or item.get("ui_status")
        if c_status == "Skip - Skill Already Present" or item.get("score") == 0:
            continue
        c_key = c_name.strip().lower()
        if c_key in added:
            continue
        c_obj = find_course(c_name, courses)
        diff = c_obj["difficulty"] if c_obj else item.get("difficulty", "Intermediate")
        path.append({
            "step": len(path) + 1,
            "item": c_name,
            "type": "Course",
            "difficulty": diff,
            "why": f"Recommended to advance toward {profile.get('career_goal', 'your target role')}.",
            "skills_gained": c_obj.get("skills", []) if c_obj else item.get("skills", []),
            "prerequisites": c_obj.get("prerequisites", []) if c_obj else item.get("prerequisites", [])
        })
        added.add(c_key)

    return path


# ============================================================
# AI PATH EXPLANATION
# ============================================================

def explain_learning_path(
    profile,
    learning_path
):

    if not learning_path:
        return "No learning path items required. Your selected skills already cover the foundational courses."

    path_text = ""

    for item in learning_path:

        skills = ", ".join(
            item.get(
                "skills_gained",
                []
            )
        )

        prerequisites = ", ".join(
            item.get(
                "prerequisites",
                []
            )
        )

        if not prerequisites:
            prerequisites = "None"

        path_text += f"""
Step {item['step']}
Name: {item['item']}
Type: {item['type']}
Difficulty: {item['difficulty']}
Why: {item['why']}
Skills: {skills}
Prerequisites: {prerequisites}

"""

    prompt = f"""
You are the Learning Path Agent of an AI Course Advisor.

Your job is ONLY to explain the learning path calculated
by the deterministic system.

Do NOT modify the path.

Do NOT add courses.

Do NOT remove courses.

Do NOT change the order.

Do NOT invent prerequisites.

Do NOT invent skills.

LEARNER PROFILE:

{json.dumps(profile, indent=2)}

CALCULATED LEARNING PATH:

{path_text}

Explain the path using these sections:

1. Why this order is suitable
2. Step-by-step learning progression
3. Skills developed
4. Career benefit
5. Short conclusion

IMPORTANT:

The calculated learning path is authoritative.

If a preparation step appears before a course, explain why
that preparation is required.

If a course has prerequisites, respect them exactly.

Keep the explanation professional and concise.
"""

    return ask_ollama(prompt)


# ============================================================
# PUBLIC LEARNING PATH AGENT
# ============================================================

def learning_path_agent(
    profile,
    recommendations
):

    learning_path = build_learning_path(
        profile,
        recommendations
    )

    explanation = explain_learning_path(
        profile,
        learning_path
    )

    return {
        "learning_path": learning_path,
        "explanation": explanation
    }


# ============================================================
# DIRECT TEST
# ============================================================

if __name__ == "__main__":

    profile = {
        "education": "B.Tech ECE",
        "skills": [
            "Python",
            "Basic SQL",
            "Basic Cloud"
        ],
        "experience": "Beginner",
        "interests": [
            "AI",
            "Cloud Computing"
        ],
        "career_goal": "AI/ML Engineer"
    }

    recommendations = [

        {
            "course_name": "Machine Learning Fundamentals",
            "status": "Prepare First",
            "missing_prerequisites": [
                "Basic Mathematics",
                "Basic Statistics"
            ]
        },

        {
            "course_name": "Deep Learning with Neural Networks",
            "status": "Prepare First",
            "missing_prerequisites": [
                "Machine Learning Fundamentals"
            ]
        },

        {
            "course_name": "Generative AI and LLMs",
            "status": "Prepare First",
            "missing_prerequisites": [
                "Machine Learning Fundamentals",
                "Deep Learning"
            ]
        },

        {
            "course_name": "AWS Cloud Foundations",
            "status": "Recommended Now",
            "missing_prerequisites": []
        },

        {
            "course_name": "AWS Solutions Architect Fundamentals",
            "status": "Blocked",
            "missing_prerequisites": [
                "AWS Cloud Foundations"
            ]
        },

        {
            "course_name": "Python for Beginners",
            "status": "Skip - Skill Already Present",
            "missing_prerequisites": []
        }
    ]

    result = learning_path_agent(
        profile,
        recommendations
    )

    print("\n" + "=" * 70)
    print("                 LEARNING PATH AGENT")
    print("=" * 70)

    print("\n===== CALCULATED LEARNING PATH =====\n")

    for item in result["learning_path"]:

        print(
            f"{item['step']}. "
            f"{item['item']} "
            f"({item['type']})"
        )

        print(
            f"   Difficulty: {item['difficulty']}"
        )

        print(
            f"   Skills: "
            f"{', '.join(item['skills_gained'])}"
        )

        prerequisite_text = ", ".join(
            item["prerequisites"]
        )

        if not prerequisite_text:
            prerequisite_text = "None"

        print(
            f"   Prerequisites: "
            f"{prerequisite_text}"
        )

        print()

    print("\n===== AI PATH EXPLANATION =====\n")

    print(
        result["explanation"]
    )

    print("\n" + "=" * 70)
    print("              LEARNING PATH COMPLETE")
    print("=" * 70)