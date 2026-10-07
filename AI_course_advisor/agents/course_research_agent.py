import json
import sys
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError


# ============================================================
# PROJECT PATH
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from rag.retriever import retrieve_courses


# ============================================================
# CONFIGURATION
# ============================================================

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "qwen2.5:3b"


# ============================================================
# OLLAMA HELPER
# ============================================================

def ask_ollama(prompt):
    """
    Send a prompt to the local Ollama model.
    """

    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False
    }

    data = json.dumps(payload).encode("utf-8")

    request = Request(
        OLLAMA_URL,
        data=data,
        headers={
            "Content-Type": "application/json"
        }
    )

    try:
        with urlopen(request, timeout=120) as response:
            result = json.loads(response.read().decode("utf-8"))

        return result.get("response", "").strip()

    except HTTPError as error:
        return f"Ollama HTTP error: {error.code}"

    except URLError:
        return "Ollama is not reachable. Make sure Ollama is running."

    except Exception as error:
        return f"Ollama error: {error}"


# ============================================================
# NORMALIZE RAG RESULT
# ============================================================

def normalize_rag_result(result):
    """
    Convert different possible retriever output formats
    into a consistent course dictionary.
    """

    if isinstance(result, dict):

        course_id = (
            result.get("course_id")
            or result.get("id")
            or result.get("metadata", {}).get("course_id")
        )

        course_name = (
            result.get("course_name")
            or result.get("name")
            or result.get("metadata", {}).get("course_name")
        )

        text = (
            result.get("text")
            or result.get("content")
            or result.get("page_content")
            or ""
        )

        score = (
            result.get("similarity")
            or result.get("score")
            or 0
        )

        return {
            "course_id": course_id,
            "course_name": course_name,
            "text": text,
            "score": score
        }

    if isinstance(result, (list, tuple)):

        if len(result) == 0:
            return {
                "course_id": None,
                "course_name": None,
                "text": "",
                "score": 0
            }

        # Example:
        # [course_id, course_name, text, score]
        if len(result) >= 4:

            return {
                "course_id": result[0],
                "course_name": result[1],
                "text": result[2],
                "score": result[3]
            }

        # Example:
        # [course_id, course_name]
        if len(result) >= 2:

            return {
                "course_id": result[0],
                "course_name": result[1],
                "text": "",
                "score": 0
            }

        return {
            "course_id": None,
            "course_name": str(result[0]),
            "text": "",
            "score": 0
        }

    return {
        "course_id": None,
        "course_name": str(result),
        "text": "",
        "score": 0
    }


# ============================================================
# COURSE RESEARCH AGENT
# ============================================================

def research_courses(profile):
    """
    Research courses using the RAG knowledge base.

    RAG retrieves relevant course documents.
    Ollama explains why those courses are relevant.

    The LLM does not invent courses or prerequisites.
    """

    if not isinstance(profile, dict):
        raise ValueError("Profile must be a dictionary.")

    education = profile.get("education", "")
    skills = profile.get("skills", [])
    experience = profile.get("experience", "")
    interests = profile.get("interests", [])
    career_goal = profile.get("career_goal", "")

    if not isinstance(skills, list):
        skills = [str(skills)]

    if not isinstance(interests, list):
        interests = [str(interests)]

    skill_text = ", ".join(str(x) for x in skills)
    interest_text = ", ".join(str(x) for x in interests)

    # --------------------------------------------------------
    # BUILD RAG QUERY
    # --------------------------------------------------------

    query = (
        f"Find courses suitable for a {career_goal} career path "
        f"for a {education} learner with {skill_text} skills, "
        f"interested in {interest_text}."
    )

    # --------------------------------------------------------
    # RAG RETRIEVAL
    # --------------------------------------------------------

    raw_results = retrieve_courses(query, top_k=6)

    if raw_results is None:
        raw_results = []

    # Safety: ensure iterable
    if not isinstance(raw_results, (list, tuple)):
        raw_results = [raw_results]

    normalized_results = []

    for item in raw_results:

        normalized = normalize_rag_result(item)

        if (
            normalized["course_id"]
            or normalized["course_name"]
        ):
            normalized_results.append(normalized)

    # Remove duplicates
    unique_results = []
    seen_ids = set()

    for course in normalized_results:

        course_id = course.get("course_id")

        if course_id:
            if course_id in seen_ids:
                continue

            seen_ids.add(course_id)

        unique_results.append(course)

    # --------------------------------------------------------
    # PREPARE CONTEXT
    # --------------------------------------------------------

    context_parts = []

    for course in unique_results:

        context_parts.append(
            f"""
Course ID: {course.get("course_id")}
Course Name: {course.get("course_name")}
Similarity Score: {course.get("score")}

Course Information:
{course.get("text", "")}
"""
        )

    context = "\n".join(context_parts)

    # --------------------------------------------------------
    # LLM EXPLANATION
    # --------------------------------------------------------

    if context.strip():

        prompt = f"""
You are the Course Research Agent in an AI Course Advisor.

Learner profile:

Education:
{education}

Skills:
{skill_text}

Experience:
{experience}

Interests:
{interest_text}

Career Goal:
{career_goal}

The RAG system retrieved the following course information:

{context}

Your task:

1. Identify the most relevant retrieved courses.
2. Explain why each course is relevant.
3. Mention the course difficulty if available.
4. Mention prerequisites only when they are present in the retrieved information.
5. Do not invent courses.
6. Do not invent prerequisites.
7. Do not invent skills.
8. Do not change the retrieved course information.

Return a concise research summary.
"""

        explanation = ask_ollama(prompt)

    else:

        explanation = (
            "RAG did not return course documents. "
            "The recommendation agent can continue using the structured course knowledge base."
        )

    # --------------------------------------------------------
    # FINAL RESULT
    # --------------------------------------------------------

    return {
        "query": query,
        "retrieved_courses": unique_results,
        "explanation": explanation
    }


# ============================================================
# TEST
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

    print("=" * 70)
    print("COURSE RESEARCH AGENT")
    print("=" * 70)

    print("\nRAG Query:")
    print(
        "Find courses suitable for an AI/ML Engineer "
        "career path for a B.Tech ECE learner."
    )

    print("\nRetrieving courses from RAG...\n")

    try:

        result = research_courses(profile)

        print("===== RETRIEVED COURSES =====")

        courses = result.get("retrieved_courses", [])

        if not courses:

            print("No courses retrieved.")

        else:

            for index, course in enumerate(courses, start=1):

                print(
                    f"{index}. "
                    f"{course.get('course_name')} "
                    f"({course.get('course_id')})"
                )

                print(
                    f"   Similarity: "
                    f"{course.get('score', 0)}"
                )

        print("\n===== AI RESEARCH EXPLANATION =====")
        print(result.get("explanation", ""))

        print("\n[OK] Course Research Agent completed.")

    except Exception as error:

        print(
            f"\nCourse Research Agent error: {error}"
        )