import json
import urllib.request


def ask_ollama(prompt):
    data = json.dumps({
        "model": "qwen2.5:3b",
        "prompt": prompt,
        "stream": False
    }).encode("utf-8")

    request = urllib.request.Request(
        "http://localhost:11434/api/generate",
        data=data,
        headers={"Content-Type": "application/json"}
    )

    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            result = json.loads(response.read().decode("utf-8"))
        return result.get("response", "").strip()
    except Exception as e:
        return f"AI profile analysis unavailable: {e}"


def profile_analysis(profile):
    prompt = f"""
You are the Profile Analysis Agent of an AI Course Advisor.

Analyze the learner profile below.

Learner Profile:
{json.dumps(profile, indent=2)}

Identify:
1. Current skills
2. Education background
3. Experience level
4. Interests
5. Career goal
6. Missing or weak skills
7. Suitable learning direction

Give a clear and concise analysis.
"""

    return ask_ollama(prompt)


if __name__ == "__main__":

    profile = {
        "education": "B.Tech ECE",
        "skills": ["Python", "Basic SQL", "Basic Cloud"],
        "experience": "Beginner",
        "interests": ["AI", "Cloud Computing"],
        "career_goal": "AI/ML Engineer"
    }

    result = profile_analysis(profile)

    print("\n===== PROFILE ANALYSIS =====\n")
    print(result)