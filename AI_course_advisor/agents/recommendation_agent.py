import json
import sys
import urllib.request
from pathlib import Path


# ============================================================
# PROJECT ROOT
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ============================================================
# RAG
# ============================================================

from rag.retriever import retrieve_courses


# ============================================================
# FILES
# ============================================================

COURSE_FILE = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "courses.json"
)


# ============================================================
# OLLAMA
# ============================================================

OLLAMA_URL = (
    "http://localhost:11434/api/generate"
)

OLLAMA_MODEL = "qwen2.5:3b"


# ============================================================
# OLLAMA CALL
# ============================================================

def ask_ollama(prompt):

    data = json.dumps(
        {
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False
        }
    ).encode()

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
            response.read()
        )

        return result.get(
            "response",
            ""
        ).strip()

    except Exception as e:

        return (
            "AI explanation unavailable: "
            f"{e}"
        )


# ============================================================
# LOAD COURSES
# ============================================================

def load_courses():

    with open(
        COURSE_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        return json.load(file)


# ============================================================
# NORMALIZE
# ============================================================

def normalize(text):

    if text is None:
        return ""

    return (
        str(text)
        .strip()
        .lower()
        .replace("-", " ")
        .replace("_", " ")
    )


# ============================================================
# CAREER DIRECTION
# ============================================================

def detect_career_direction(
    career_goal
):

    goal = normalize(
        career_goal
    )

    # --------------------------------------------------------
    # CLOUD
    # --------------------------------------------------------

    if any(
        keyword in goal
        for keyword in [
            "cloud engineer",
            "cloud architect",
            "cloud developer",
            "aws engineer",
            "aws developer",
            "cloud computing",
            "cloud"
        ]
    ):

        return "cloud"

    # --------------------------------------------------------
    # DEVOPS
    # --------------------------------------------------------

    if any(
        keyword in goal
        for keyword in [
            "devops",
            "devops engineer",
            "devops developer",
            "site reliability",
            "sre",
            "platform engineer"
        ]
    ):

        return "devops"

    # --------------------------------------------------------
    # GENERATIVE AI
    # --------------------------------------------------------

    if any(
        keyword in goal
        for keyword in [
            "generative ai",
            "gen ai",
            "genai",
            "llm engineer",
            "llm developer",
            "ai application developer"
        ]
    ):

        return "generative_ai"

    # --------------------------------------------------------
    # AI / ML
    # --------------------------------------------------------

    if any(
        keyword in goal
        for keyword in [
            "ai/ml",
            "ai ml",
            "machine learning",
            "ml engineer",
            "ml developer",
            "ai engineer",
            "artificial intelligence",
            "ai developer"
        ]
    ):

        return "ai_ml"

    # --------------------------------------------------------
    # DATA SCIENCE
    # --------------------------------------------------------

    if any(
        keyword in goal
        for keyword in [
            "data scientist",
            "data science",
            "data analyst",
            "data analytics"
        ]
    ):

        return "data_science"

    return "general"


# ============================================================
# CAREER PRIORITIES
# ============================================================

CAREER_PRIORITIES = {

    "cloud": {

        "CL001": 55,
        "CL002": 50,
        "CL003": 40,
        "CL004": 30,
        "CL005": 20,
        "CL006": 15,

        "AI002": 5,
        "AI007": 5
    },

    "devops": {

        "CL001": 55,
        "CL002": 45,
        "CL004": 55,
        "CL005": 50,
        "CL006": 45,
        "CL003": 30,

        "AI002": 5
    },

    "ai_ml": {

        "AI002": 55,
        "AI003": 45,
        "AI004": 40,
        "AI005": 30,
        "AI006": 30,
        "AI007": 25,

        "CL001": 5
    },

    "generative_ai": {

        "AI004": 60,
        "AI008": 55,
        "AI003": 45,
        "AI002": 40,

        "AI005": 25,

        "CL001": 5
    },

    "data_science": {

        "DS001": 55,
        "AI007": 60,
        "DS002": 55,
        "AI002": 40,

        "AI001": 10
    },

    "general": {

        "AI002": 30,
        "AI003": 25,
        "AI004": 25,
        "AI007": 25,

        "CL001": 25,
        "CL002": 20,

        "DS001": 15,
        "DS002": 15,

        "AI001": 10
    }
}


# ============================================================
# CATEGORY PRIORITIES
# ============================================================

CATEGORY_PRIORITY = {

    "cloud": {
        "Cloud Computing": 20,
        "DevOps": 10
    },

    "devops": {
        "DevOps": 25,
        "Cloud Computing": 15
    },

    "ai_ml": {
        "Artificial Intelligence": 20,
        "Generative AI": 15,
        "Data Science": 10
    },

    "generative_ai": {
        "Generative AI": 25,
        "Artificial Intelligence": 15
    },

    "data_science": {
        "Data Science": 25,
        "Artificial Intelligence": 10
    },

    "general": {}
}


# ============================================================
# SKILL MATCH
# ============================================================

def calculate_skill_match(
    course,
    learner_skills
):

    learner_skills_normalized = {
        normalize(skill)
        for skill in learner_skills
    }

    course_skills = course.get(
        "skills",
        []
    )

    if not course_skills:

        return 0

    matched = 0

    for skill in course_skills:

        if normalize(skill) in learner_skills_normalized:

            matched += 1

    return int(
        (
            matched
            / len(course_skills)
        )
        * 15
    )


# ============================================================
# PREREQUISITES
# ============================================================

def check_prerequisites(
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
        normalize(skill)
        for skill in learner_skills
    }

    satisfied = []
    missing = []

    for prerequisite in prerequisites:

        prerequisite_text = str(
            prerequisite
        ).strip()

        normalized = normalize(
            prerequisite_text
        )

        if not normalized:
            continue

        if normalized == (
            "basic computer knowledge"
        ):

            satisfied.append(
                prerequisite_text
            )

            continue

        if normalized in learner_skill_set:

            satisfied.append(
                prerequisite_text
            )

            continue

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
# COURSE SCORE
# ============================================================

def calculate_course_score(
    course,
    profile,
    career_direction
):

    course_id = course.get(
        "course_id",
        ""
    )

    learner_skills = profile.get(
        "skills",
        []
    )

    interests = profile.get(
        "interests",
        []
    )

    # --------------------------------------------------------
    # Career relevance
    # --------------------------------------------------------

    career_score = (
        CAREER_PRIORITIES
        .get(
            career_direction,
            {}
        )
        .get(
            course_id,
            0
        )
    )

    # --------------------------------------------------------
    # Category relevance
    # --------------------------------------------------------

    category = course.get(
        "category",
        ""
    )

    category_score = (
        CATEGORY_PRIORITY
        .get(
            career_direction,
            {}
        )
        .get(
            category,
            0
        )
    )

    # --------------------------------------------------------
    # Skill match
    # --------------------------------------------------------

    skill_score = calculate_skill_match(
        course,
        learner_skills
    )

    # --------------------------------------------------------
    # Interest match
    # --------------------------------------------------------

    interest_score = 0

    normalized_interests = [
        normalize(item)
        for item in interests
    ]

    normalized_category = normalize(
        category
    )

    normalized_course_name = normalize(
        course.get(
            "course_name",
            ""
        )
    )

    for interest in normalized_interests:

        if (
            interest in normalized_category
            or interest in normalized_course_name
            or normalized_category in interest
        ):

            interest_score += 5

    interest_score = min(
        interest_score,
        10
    )

    # --------------------------------------------------------
    # Experience / difficulty
    # --------------------------------------------------------

    difficulty = normalize(
        course.get(
            "difficulty",
            ""
        )
    )

    experience = normalize(
        profile.get(
            "experience",
            ""
        )
    )

    difficulty_score = 0

    if (
        experience == "beginner"
        and difficulty == "beginner"
    ):

        difficulty_score = 5

    elif (
        experience == "intermediate"
        and difficulty in [
            "beginner",
            "intermediate"
        ]
    ):

        difficulty_score = 5

    elif experience == "advanced":

        difficulty_score = 5

    total = (
        career_score
        + category_score
        + skill_score
        + interest_score
        + difficulty_score
    )

    return min(
        total,
        100
    )


# ============================================================
# COURSE LOOKUP
# ============================================================

def build_course_lookup(
    courses
):

    lookup = {}

    for course in courses:

        course_name = normalize(
            course.get(
                "course_name",
                ""
            )
        )

        course_id = course.get(
            "course_id",
            ""
        )

        if course_name:

            lookup[
                course_name
            ] = course

        if course_id:

            lookup[
                normalize(course_id)
            ] = course

    return lookup


# ============================================================
# FIND COURSE BY PREREQUISITE NAME
# ============================================================

def find_course_by_name(
    prerequisite,
    course_lookup
):

    normalized = normalize(
        prerequisite
    )

    # --------------------------------------------------------
    # Exact name match
    # --------------------------------------------------------

    if normalized in course_lookup:

        return course_lookup[
            normalized
        ]

    # --------------------------------------------------------
    # Direct substring match
    # --------------------------------------------------------

    for course_name, course in (
        course_lookup.items()
    ):

        if (
            normalized == course_name
            or normalized in course_name
            or course_name in normalized
        ):

            return course

    # --------------------------------------------------------
    # Special semantic mapping
    # --------------------------------------------------------

    aliases = {

        "deep learning":
            "deep learning with neural networks",

        "ml fundamentals":
            "machine learning fundamentals",

        "machine learning":
            "machine learning fundamentals",

        "aws":
            "aws cloud foundations",

        "cloud foundations":
            "aws cloud foundations",

        "solutions architect":
            "aws solutions architect fundamentals",

        "docker":
            "docker and container fundamentals",

        "kubernetes":
            "kubernetes fundamentals",

        "sql":
            "sql and database fundamentals"
    }

    mapped = aliases.get(
        normalized
    )

    if mapped:

        return course_lookup.get(
            mapped
        )

    return None


# ============================================================
# DYNAMIC DEPENDENCY GRAPH
# ============================================================

def build_dependency_graph(
    selected_courses,
    all_courses
):

    course_lookup = build_course_lookup(
        all_courses
    )

    graph = {}

    for course in selected_courses:

        course_id = course.get(
            "course_id"
        )

        if not course_id:
            continue

        graph[course_id] = []

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

        for prerequisite in prerequisites:

            prerequisite_text = str(
                prerequisite
            ).strip()

            if not prerequisite_text:
                continue

            dependency = (
                find_course_by_name(
                    prerequisite_text,
                    course_lookup
                )
            )

            if dependency:

                dependency_id = (
                    dependency.get(
                        "course_id"
                    )
                )

                if (
                    dependency_id
                    and dependency_id
                    != course_id
                ):

                    graph[
                        course_id
                    ].append(
                        dependency_id
                    )

    return graph


# ============================================================
# RECURSIVE DEPENDENCY RESOLUTION
# ============================================================

def resolve_dependencies(
    course_id,
    graph,
    visited=None,
    visiting=None,
    ordered=None
):

    if visited is None:
        visited = set()

    if visiting is None:
        visiting = set()

    if ordered is None:
        ordered = []

    # --------------------------------------------------------
    # Already resolved
    # --------------------------------------------------------

    if course_id in visited:

        return ordered

    # --------------------------------------------------------
    # Circular dependency protection
    # --------------------------------------------------------

    if course_id in visiting:

        return ordered

    visiting.add(
        course_id
    )

    # --------------------------------------------------------
    # Resolve prerequisites first
    # --------------------------------------------------------

    for dependency_id in graph.get(
        course_id,
        []
    ):

        resolve_dependencies(
            dependency_id,
            graph,
            visited,
            visiting,
            ordered
        )

    visiting.remove(
        course_id
    )

    visited.add(
        course_id
    )

    ordered.append(
        course_id
    )

    return ordered


# ============================================================
# DYNAMIC LEARNING PATH
# ============================================================

def build_dynamic_learning_path(
    profile,
    recommended_courses,
    all_courses,
    career_direction
):

    if not recommended_courses:

        return []

    # --------------------------------------------------------
    # Career-relevant courses
    # --------------------------------------------------------

    career_scores = (
        CAREER_PRIORITIES.get(
            career_direction,
            {}
        )
    )

    relevant_courses = []

    for course in recommended_courses:

        course_id = course.get(
            "course_id"
        )

        if not course_id:
            continue

        priority = career_scores.get(
            course_id,
            0
        )

        if priority > 0:

            relevant_courses.append(
                course
            )

    # --------------------------------------------------------
    # If no career mapping exists,
    # use recommended courses.
    # --------------------------------------------------------

    if not relevant_courses:

        relevant_courses = (
            recommended_courses[:5]
        )

    # --------------------------------------------------------
    # Build dependency graph
    # --------------------------------------------------------

    graph = build_dependency_graph(
        relevant_courses,
        all_courses
    )

    # --------------------------------------------------------
    # Resolve all career-relevant courses
    # --------------------------------------------------------

    ordered_ids = []

    visited = set()

    visiting = set()

    for course in sorted(
        relevant_courses,
        key=lambda item:
            career_scores.get(
                item.get(
                    "course_id"
                ),
                0
            ),
        reverse=True
    ):

        course_id = course.get(
            "course_id"
        )

        resolve_dependencies(
            course_id,
            graph,
            visited,
            visiting,
            ordered_ids
        )

    # --------------------------------------------------------
    # Course lookup
    # --------------------------------------------------------

    course_lookup = {
        course.get(
            "course_id"
        ): course
        for course in all_courses
    }

    # --------------------------------------------------------
    # Convert IDs to path
    # --------------------------------------------------------

    path = []

    added_ids = set()

    learner_skills = profile.get(
        "skills",
        []
    )

    learner_skill_set = {
        normalize(skill)
        for skill in learner_skills
    }

    for course_id in ordered_ids:

        if course_id in added_ids:
            continue

        course = course_lookup.get(
            course_id
        )

        if not course:
            continue

        # ----------------------------------------------------
        # Skip courses whose primary skill is already known
        # ----------------------------------------------------

        course_name = normalize(
            course.get(
                "course_name",
                ""
            )
        )

        if (
            course_name
            == "python for beginners"
            and "python"
            in learner_skill_set
        ):

            continue

        path.append(
            {
                "item":
                    course.get(
                        "course_name",
                        "Unknown"
                    ),

                "type":
                    "Course",

                "course_id":
                    course_id
            }
        )

        added_ids.add(
            course_id
        )

    # --------------------------------------------------------
    # Add unresolved preparation prerequisites
    # --------------------------------------------------------

    preparation_items = []

    for course in path:

        original_course = (
            course_lookup.get(
                course["course_id"]
            )
        )

        if not original_course:
            continue

        prerequisites = (
            original_course.get(
                "prerequisites",
                []
            )
        )

        if not isinstance(
            prerequisites,
            list
        ):

            prerequisites = [
                prerequisites
            ]

        for prerequisite in prerequisites:

            prerequisite_text = str(
                prerequisite
            ).strip()

            normalized = normalize(
                prerequisite_text
            )

            if not normalized:
                continue

            # Basic computer knowledge is baseline.
            if normalized == (
                "basic computer knowledge"
            ):

                continue

            # Already known skill.
            if normalized in learner_skill_set:

                continue

            # If it is already represented by
            # a course in the path, don't add it.
            represented_by_course = False

            for path_item in path:

                if normalize(
                    path_item["item"]
                ) == normalized:

                    represented_by_course = True
                    break

            if represented_by_course:
                continue

            # If a course with this prerequisite
            # name exists, dependency resolver handles it.
            dependency_course = (
                find_course_by_name(
                    prerequisite_text,
                    build_course_lookup(
                        all_courses
                    )
                )
            )

            if dependency_course:

                continue

            # Otherwise this is a knowledge
            # prerequisite such as mathematics
            # or statistics.
            preparation_items.append(
                prerequisite_text
            )

    # --------------------------------------------------------
    # Remove duplicate preparation items
    # --------------------------------------------------------

    unique_preparation = []

    seen_preparation = set()

    for item in preparation_items:

        normalized = normalize(
            item
        )

        if normalized in seen_preparation:
            continue

        seen_preparation.add(
            normalized
        )

        unique_preparation.append(
            item
        )

    # --------------------------------------------------------
    # Insert preparation at beginning
    # --------------------------------------------------------

    final_path = []

    for preparation in unique_preparation:

        final_path.append(
            {
                "item":
                    preparation,

                "type":
                    "Preparation"
            }
        )

    final_path.extend(
        path
    )

    return final_path


# ============================================================
# RECOMMEND COURSES
# ============================================================

def recommend_courses(
    profile
):

    all_courses = load_courses()

    career_goal = profile.get(
        "career_goal",
        ""
    )

    career_direction = (
        detect_career_direction(
            career_goal
        )
    )

    # ========================================================
    # RAG
    # ========================================================

    query = (
        f"courses suitable for "
        f"{career_goal} career path "
        f"for learner with "
        f"{', '.join(profile.get('skills', []))} "
        f"skills"
    )

    try:

        rag_results = retrieve_courses(
            query,
            top_k=len(all_courses)
        )

    except Exception:

        rag_results = []

    # --------------------------------------------------------
    # RAG course IDs
    # --------------------------------------------------------

    rag_course_ids = []

    for item in rag_results:

        if isinstance(
            item,
            dict
        ):

            course_id = item.get(
                "course_id"
            )

            if course_id:

                rag_course_ids.append(
                    course_id
                )

    # --------------------------------------------------------
    # If RAG returns nothing,
    # use the complete knowledge base.
    # --------------------------------------------------------

    if not rag_course_ids:

        rag_course_ids = [
            course.get(
                "course_id"
            )
            for course in all_courses
        ]

    # ========================================================
    # CALCULATE RECOMMENDATIONS
    # ========================================================

    results = []

    for course in all_courses:

        course_id = course.get(
            "course_id",
            ""
        )

        # ----------------------------------------------------
        # Use RAG relevance.
        # ----------------------------------------------------

        if (
            rag_course_ids
            and course_id
            not in rag_course_ids
        ):

            continue

        satisfied, missing = (
            check_prerequisites(
                course,
                profile.get(
                    "skills",
                    []
                )
            )
        )

        readiness = (
            "Ready"
            if not missing
            else "Partially Ready"
        )

        score = calculate_course_score(
            course,
            profile,
            career_direction
        )

        # ----------------------------------------------------
        # Python already present
        # ----------------------------------------------------

        learner_skill_set = {
            normalize(skill)
            for skill in profile.get(
                "skills",
                []
            )
        }

        course_name = normalize(
            course.get(
                "course_name",
                ""
            )
        )

        if (
            course_name
            == "python for beginners"
            and "python"
            in learner_skill_set
        ):

            status = (
                "Skip - Skill Already Present"
            )

            score = 0

        elif missing:

            status = "Prepare First"

        else:

            status = "Recommended Now"

        results.append(
            {
                "course_id":
                    course.get(
                        "course_id"
                    ),

                "course_name":
                    course.get(
                        "course_name"
                    ),

                "category":
                    course.get(
                        "category"
                    ),

                "difficulty":
                    course.get(
                        "difficulty"
                    ),

                "score":
                    score,

                "readiness":
                    readiness,

                "ui_readiness":
                    readiness,

                "status":
                    status,

                "ui_status":
                    status,

                "prerequisites":
                    course.get(
                        "prerequisites",
                        []
                    ),

                "satisfied_prerequisites":
                    satisfied,

                "missing_prerequisites":
                    missing,

                "skills":
                    course.get(
                        "skills",
                        []
                    ),

                "learning_outcomes":
                    course.get(
                        "learning_outcomes",
                        []
                    )
            }
        )

    # ========================================================
    # SORT
    # ========================================================

    results.sort(
        key=lambda item: (
            item.get(
                "score",
                0
            ),
            -len(
                item.get(
                    "missing_prerequisites",
                    []
                )
            )
        ),
        reverse=True
    )

    # ========================================================
    # DYNAMIC LEARNING PATH
    # ========================================================

    learning_path = (
        build_dynamic_learning_path(
            profile,
            results,
            all_courses,
            career_direction
        )
    )

    # ========================================================
    # BEST COURSE
    # ========================================================

    best_course = ""

    available_courses = [
        item
        for item in results
        if item.get(
            "status"
        )
        != "Skip - Skill Already Present"
    ]

    if available_courses:

        career_scores = (
            CAREER_PRIORITIES.get(
                career_direction,
                {}
            )
        )

        # ----------------------------------------------------
        # Prefer career-relevant courses
        # ----------------------------------------------------

        career_courses = [
            item
            for item in available_courses
            if career_scores.get(
                item.get(
                    "course_id"
                ),
                0
            ) > 0
        ]

        if career_courses:

            career_courses.sort(
                key=lambda item:
                    (
                        career_scores.get(
                            item.get(
                                "course_id"
                            ),
                            0
                        ),
                        item.get(
                            "score",
                            0
                        )
                    ),
                reverse=True
            )

            best_course = (
                career_courses[0]
                .get(
                    "course_name",
                    ""
                )
            )

        else:

            best_course = (
                available_courses[0]
                .get(
                    "course_name",
                    ""
                )
            )

    # ========================================================
    # AI EXPLANATION
    # ========================================================

    explanation_prompt = f"""
You are the explanation component of an AI Course Advisor.

The recommendation engine has already calculated
the results deterministically.

Do NOT change any calculated result.

LEARNER PROFILE:
{json.dumps(profile, indent=2)}

CAREER DIRECTION:
{career_direction}

BEST COURSE:
{best_course}

RECOMMENDATIONS:
{json.dumps(results, indent=2)}

DYNAMIC LEARNING PATH:
{json.dumps(learning_path, indent=2)}

Explain:

1. Why the best course matches the career goal.
2. Which prerequisites are satisfied.
3. Which prerequisites are missing.
4. Why the learning path follows this order.
5. How prerequisite dependencies affect the order.
6. How the final path supports the career goal.

IMPORTANT:

- Do not invent courses.
- Do not invent prerequisites.
- Do not invent skills.
- Do not change scores.
- Do not change statuses.
- Do not change the best course.
- Do not change the learning path.
- Use only the supplied course information.
"""

    explanation = ask_ollama(
        explanation_prompt
    )

    # ========================================================
    # FINAL RESULT
    # ========================================================

    final_result = {

        "career_direction":
            career_direction,

        "best_course":
            best_course,

        "recommendations":
            results,

        "learning_path":
            learning_path,

        "explanation":
            explanation
    }

    return (
        "\n===== FINAL RECOMMENDATIONS =====\n"
        + str(final_result)
    )


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    profile = {

        "education":
            "B.Tech ECE",

        "skills": [
            "Python",
            "Basic SQL",
            "Basic Cloud"
        ],

        "experience":
            "Beginner",

        "interests": [
            "AI",
            "Cloud Computing"
        ],

        "career_goal":
            "Cloud Engineer"
    }

    result = recommend_courses(
        profile
    )

    print(
        "\n========== AI COURSE ADVISOR ==========\n"
    )

    print(
        result
    )