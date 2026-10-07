from streamlit.testing.v1 import AppTest

at = AppTest.from_file("../app/app.py", default_timeout=20)
at.run()

# Inject dummy advisor_result into session state to test post-generation rendering
at.session_state["advisor_result"] = {
    "profile": {
        "education": "Bachelor's Degree",
        "experience_level": "Beginner",
        "skills": ["Python", "SQL"],
        "interests": ["Cloud", "AI"],
        "career_goal": "Cloud Solutions Architect"
    },
    "research_result": {
        "retrieved_courses": [
            {"course_name": "AWS Cloud Foundations", "score": 0.72},
            {"course_name": "AWS Solutions Architect Fundamentals", "score": 0.70},
            {"course_name": "DevOps Fundamentals", "score": 0.68},
            {"course_name": "Cloud Security Fundamentals", "score": 0.66},
            {"course_name": "AWS DevOps Fundamentals", "score": 0.66}
        ]
    },
    "prerequisite_result": {
        "verified_recommendations": [
            {
                "course_name": "AWS Cloud Foundations",
                "score": 92,
                "readiness": "Ready",
                "status": "Recommended Now",
                "difficulty": "Beginner",
                "category": "Cloud Computing",
                "satisfied_prerequisites": ["Basic Mathematics"],
                "missing_prerequisites": []
            },
            {
                "course_name": "AWS Solutions Architect Fundamentals",
                "score": 88,
                "readiness": "Partially Ready",
                "status": "Prepare First",
                "difficulty": "Intermediate",
                "category": "Cloud Architecture",
                "satisfied_prerequisites": [],
                "missing_prerequisites": ["AWS Cloud Foundations"]
            }
        ]
    },
    "recommendation_result": {
        "explanation": "Recommendations aligned with career goals and skill gap minimization."
    },
    "learning_path_result": {
        "learning_path": [
            {
                "item": "Basic Mathematics",
                "type": "Preparation",
                "difficulty": "Foundation",
                "why": "This preparation is required before Machine Learning Fundamentals."
            },
            {
                "item": "Basic Statistics",
                "type": "Preparation",
                "difficulty": "Foundation",
                "why": "This preparation is required before Machine Learning Fundamentals."
            },
            {
                "item": "Machine Learning Fundamentals",
                "type": "Course",
                "difficulty": "Beginner",
                "why": "This course follows the preparation modules."
            }
        ],
        "explanation": "Sequenced from baseline preparation to advanced career specialization."
    }
}

at.run()
assert len(at.exception) == 0, f"Exceptions encountered: {at.exception}"

raw_code_blocks = []
for md in at.markdown:
    # Check if any markdown rendered as an indented code block or contains raw html tags inside code syntax
    val = md.value
    if val.startswith("```") and ("<div" in val or "saas-timeline" in val):
        raw_code_blocks.append(val)

print(f"Post-generation render exceptions: {len(at.exception)}")
print(f"Raw code blocks found: {len(raw_code_blocks)}")
assert len(raw_code_blocks) == 0, f"Found raw code blocks in markdown: {raw_code_blocks}"

print("=== ALL CHECKS PASSED SUCCESSFULLY ===")
