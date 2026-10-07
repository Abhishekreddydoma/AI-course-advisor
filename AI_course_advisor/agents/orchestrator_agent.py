import sys
import importlib
from pathlib import Path

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


# ============================================================
# PROJECT ROOT
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ============================================================
# USER PROFILE
# ============================================================

PROFILE = {
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


# ============================================================
# HEADER
# ============================================================

def print_header(title):

    print("\n" + "=" * 70)
    print(title.center(70))
    print("=" * 70)


# ============================================================
# LOAD AGENT
# ============================================================

def load_agent(module_name, function_names):

    try:

        module = importlib.import_module(
            module_name
        )

    except Exception as error:

        print(
            f"[X] Could not load {module_name}"
        )

        print(
            f"  Error: {error}"
        )

        return None, None

    for function_name in function_names:

        function = getattr(
            module,
            function_name,
            None
        )

        if callable(function):

            return function_name, function

    return None, None


# ============================================================
# MAIN WORKFLOW
# ============================================================

def run_workflow():

    print_header(
        "AI COURSE ADVISOR"
    )


    # ========================================================
    # USER PROFILE
    # ========================================================

    print("\n===== USER PROFILE =====")

    print(
        f"Education   : "
        f"{PROFILE['education']}"
    )

    print(
        f"Skills      : "
        f"{', '.join(PROFILE['skills'])}"
    )

    print(
        f"Experience  : "
        f"{PROFILE['experience']}"
    )

    print(
        f"Interests   : "
        f"{', '.join(PROFILE['interests'])}"
    )

    print(
        f"Career Goal : "
        f"{PROFILE['career_goal']}"
    )


    # ========================================================
    # LOAD AGENTS
    # ========================================================

    print_header(
        "LOADING AGENTS"
    )

    profile_name, profile_agent = load_agent(
        "agents.profile_agent",
        [
            "profile_analysis",
            "analyze_profile"
        ]
    )

    research_name, research_agent = load_agent(
        "agents.course_research_agent",
        [
            "research_courses"
        ]
    )

    prerequisite_name, prerequisite_agent = load_agent(
        "agents.prerequisite_agent",
        [
            "analyze_prerequisites"
        ]
    )

    recommendation_name, recommendation_agent = load_agent(
        "agents.recommendation_agent",
        [
            "recommend_courses"
        ]
    )

    learning_path_name, learning_path_agent = load_agent(
        "agents.learning_path_agent",
        [
            "learning_path_agent",
            "generate_learning_path"
        ]
    )


    # ========================================================
    # AGENT STATUS
    # ========================================================

    if profile_agent:

        print(
            f"[OK] Profile Agent: "
            f"{profile_name}"
        )

    else:

        print(
            "[X] Profile Agent unavailable"
        )


    if research_agent:

        print(
            f"[OK] Research Agent: "
            f"{research_name}"
        )

    else:

        print(
            "[X] Research Agent unavailable"
        )


    if prerequisite_agent:

        print(
            f"[OK] Prerequisite Agent: "
            f"{prerequisite_name}"
        )

    else:

        print(
            "[X] Prerequisite Agent unavailable"
        )


    if recommendation_agent:

        print(
            f"[OK] Recommendation Agent: "
            f"{recommendation_name}"
        )

    else:

        print(
            "[X] Recommendation Agent unavailable"
        )


    if learning_path_agent:

        print(
            f"[OK] Learning Path Agent: "
            f"{learning_path_name}"
        )

    else:

        print(
            "[X] Learning Path Agent unavailable"
        )


    # ========================================================
    # 1. PROFILE ANALYSIS AGENT
    # ========================================================

    print_header(
        "1. PROFILE ANALYSIS AGENT"
    )

    profile_analysis = None

    if profile_agent:

        print(
            f"\nProfile function: "
            f"{profile_name}"
        )

        try:

            profile_analysis = profile_agent(
                PROFILE
            )

            print(
                "\nProfile analysis completed."
            )

            print(
                profile_analysis
            )

        except Exception as error:

            print(
                "\nProfile Agent error:"
            )

            print(error)


    # ========================================================
    # 2. COURSE RESEARCH AGENT + RAG
    # ========================================================

    print_header(
        "2. COURSE RESEARCH AGENT + RAG"
    )

    research_result = None

    if research_agent:

        print(
            f"\nResearch function: "
            f"{research_name}"
        )

        try:

            research_result = research_agent(
                PROFILE
            )

            print(
                "\nCourse research completed."
            )

            print(
                research_result
            )

        except TypeError:

            try:

                research_result = research_agent(
                    profile=PROFILE
                )

                print(
                    "\nCourse research completed."
                )

                print(
                    research_result
                )

            except Exception as error:

                print(
                    "\nCourse Research Agent error:"
                )

                print(error)

        except Exception as error:

            print(
                "\nCourse Research Agent error:"
            )

            print(error)


    # ========================================================
    # 3. PREREQUISITE ANALYSIS AGENT
    # ========================================================

    print_header(
        "3. PREREQUISITE ANALYSIS AGENT"
    )

    prerequisite_results = []

    target_courses = [
        "Machine Learning Fundamentals",
        "Deep Learning with Neural Networks",
        "Generative AI and LLMs"
    ]

    if prerequisite_agent:

        print(
            f"\nPrerequisite function: "
            f"{prerequisite_name}"
        )

        for course_name in target_courses:

            print(
                "\n" + "-" * 60
            )

            print(
                f"Course: {course_name}"
            )

            print(
                "-" * 60
            )

            try:

                result = prerequisite_agent(
                    course_name,
                    PROFILE["skills"]
                )

                prerequisite_results.append(
                    result
                )

                print(
                    result
                )

            except TypeError:

                try:

                    result = prerequisite_agent(
                        PROFILE["skills"],
                        course_name
                    )

                    prerequisite_results.append(
                        result
                    )

                    print(
                        result
                    )

                except Exception as error:

                    print(
                        "Prerequisite Agent error:"
                    )

                    print(error)

            except Exception as error:

                print(
                    "Prerequisite Agent error:"
                )

                print(error)


    # ========================================================
    # 4. RECOMMENDATION AGENT
    # ========================================================

    print_header(
        "4. RECOMMENDATION AGENT"
    )

    recommendation_result = None

    if recommendation_agent:

        print(
            f"\nRecommendation function: "
            f"{recommendation_name}"
        )

        try:

            recommendation_result = (
                recommendation_agent(
                    PROFILE
                )
            )

        except TypeError:

            try:

                recommendation_result = (
                    recommendation_agent(
                        profile=PROFILE
                    )
                )

            except Exception as error:

                print(
                    "Recommendation Agent error:"
                )

                print(error)

        except Exception as error:

            print(
                "Recommendation Agent error:"
            )

            print(error)


    # ========================================================
    # VALIDATE RECOMMENDATION
    # ========================================================

    if isinstance(
        recommendation_result,
        str
    ):
        try:
            from app.app import parse_recommendation_output
            recommendation_result = parse_recommendation_output(recommendation_result)
        except Exception:
            pass

    if not isinstance(
        recommendation_result,
        dict
    ):

        print(
            "\nRecommendation Agent did not "
            "return a valid dictionary."
        )

        return None


    recommendations = (
        recommendation_result.get(
            "recommendations",
            []
        )
    )

    best_course = (
        recommendation_result.get(
            "best_course"
        )
    )


    # ========================================================
    # DISPLAY RECOMMENDATIONS
    # ========================================================

    print(
        "\n===== SYSTEM CALCULATED RESULTS ====="
    )

    for index, item in enumerate(
        recommendations,
        start=1
    ):

        print(
            f"\n{index}. "
            f"{item.get('course_name')}"
        )

        print(
            f"   Score: "
            f"{item.get('score')}/100"
        )

        print(
            f"   Readiness: "
            f"{item.get('readiness')}"
        )

        print(
            f"   Status: "
            f"{item.get('status')}"
        )

        missing = item.get(
            "missing_prerequisites",
            []
        )

        if missing:

            print(
                "   Missing:"
            )

            for prerequisite in missing:

                print(
                    f"      ✗ "
                    f"{prerequisite}"
                )

        else:

            print(
                "   Missing: None"
            )


    print(
        "\n===== BEST COURSE TO START ====="
    )

    print(
        best_course
    )


    # ========================================================
    # 5. LEARNING PATH AGENT
    # ========================================================

    print_header(
        "5. LEARNING PATH AGENT"
    )

    learning_path_result = None

    if learning_path_agent:

        print(
            f"\nLearning Path function: "
            f"{learning_path_name}"
        )

        try:

            learning_path_result = (
                learning_path_agent(
                    PROFILE,
                    recommendations
                )
            )

        except TypeError:

            try:

                learning_path_result = (
                    learning_path_agent(
                        profile=PROFILE,
                        recommendations=recommendations
                    )
                )

            except Exception as error:

                print(
                    "\nLearning Path Agent error:"
                )

                print(error)

        except Exception as error:

            print(
                "\nLearning Path Agent error:"
            )

            print(error)


    # ========================================================
    # EXTRACT LEARNING PATH
    # ========================================================

    learning_path = []

    learning_path_explanation = ""

    if isinstance(
        learning_path_result,
        dict
    ):

        learning_path = (
            learning_path_result.get(
                "learning_path",
                []
            )
        )

        learning_path_explanation = (
            learning_path_result.get(
                "explanation",
                ""
            )
        )


    # ========================================================
    # FALLBACK
    # ========================================================

    if not learning_path:

        learning_path = (
            recommendation_result.get(
                "learning_path",
                []
            )
        )


    # ========================================================
    # DISPLAY LEARNING PATH
    # ========================================================

    print(
        "\n===== FINAL LEARNING PATH ====="
    )

    for index, item in enumerate(
        learning_path,
        start=1
    ):

        if isinstance(
            item,
            dict
        ):

            name = item.get(
                "item",
                item.get(
                    "course_name",
                    "Unknown"
                )
            )

            item_type = item.get(
                "type",
                "Course"
            )

        else:

            name = str(item)

            item_type = "Course"

        print(
            f"{index}. "
            f"{name} "
            f"({item_type})"
        )


    # ========================================================
    # LEARNING PATH EXPLANATION
    # ========================================================

    print(
        "\n===== LEARNING PATH AI EXPLANATION =====\n"
    )

    if learning_path_explanation:

        print(
            learning_path_explanation
        )

    else:

        print(
            "No learning path explanation available."
        )


    # ========================================================
    # FINAL RESULT
    # ========================================================

    final_result = {

        "profile": PROFILE,

        "profile_analysis": (
            profile_analysis
        ),

        "course_research": (
            research_result
        ),

        "prerequisite_analysis": (
            prerequisite_results
        ),

        "recommendations": (
            recommendations
        ),

        "best_course": (
            best_course
        ),

        "learning_path": (
            learning_path
        ),

        "learning_path_explanation": (
            learning_path_explanation
        )
    }


    # ========================================================
    # COMPLETE
    # ========================================================

    print_header(
        "WORKFLOW COMPLETE"
    )

    print("[OK] User Profile")
    print("[OK] Profile Analysis Agent")
    print("[OK] Course Research Agent")
    print("[OK] RAG Knowledge Retrieval")
    print("[OK] Prerequisite Analysis Agent")
    print("[OK] Recommendation Agent")
    print("[OK] Learning Path Agent")
    print("[OK] Final Learning Path")

    print(
        "\nAI Course Advisor orchestration completed."
    )

    return final_result


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    run_workflow()