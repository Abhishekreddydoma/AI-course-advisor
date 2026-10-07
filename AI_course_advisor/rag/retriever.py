import json
import urllib.request
import math
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
VECTORSTORE_FILE = PROJECT_ROOT / "data" / "vectorstore" / "courses_embeddings.json"
EMBEDDING_MODEL = "nomic-embed-text"


def get_embedding(text):
    data = json.dumps({
        "model": EMBEDDING_MODEL,
        "input": text
    }).encode("utf-8")

    request = urllib.request.Request(
        "http://localhost:11434/api/embed",
        data=data,
        headers={"Content-Type": "application/json"}
    )

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            result = json.loads(response.read().decode("utf-8"))
        return result["embeddings"][0]
    except Exception as e:
        print(f"Warning: Failed to get embedding from Ollama: {e}")
        return []


def cosine_similarity(a, b):
    if not a or not b:
        return 0

    dot_product = sum(x * y for x, y in zip(a, b))

    magnitude_a = math.sqrt(sum(x * x for x in a))
    magnitude_b = math.sqrt(sum(x * x for x in b))

    if magnitude_a == 0 or magnitude_b == 0:
        return 0

    return dot_product / (magnitude_a * magnitude_b)


def retrieve_courses(query, top_k=3):
    if not VECTORSTORE_FILE.exists():
        print(f"Warning: Vectorstore file not found at {VECTORSTORE_FILE}")
        return []

    try:
        with open(VECTORSTORE_FILE, "r", encoding="utf-8") as f:
            courses = json.load(f)
    except Exception as e:
        print(f"Warning: Failed to load vectorstore: {e}")
        return []

    query_embedding = get_embedding(query)
    if not query_embedding:
        # Fallback keyword match if embedding unavailable
        query_words = set(query.lower().split())
        results = []
        for course in courses:
            text_words = set(course.get("text", "").lower().split())
            overlap = len(query_words & text_words) / max(len(query_words), 1)
            results.append({
                "course_id": course["course_id"],
                "course_name": course["course_name"],
                "text": course["text"],
                "similarity": overlap
            })
        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results[:top_k]

    results = []

    for course in courses:
        similarity = cosine_similarity(
            query_embedding,
            course.get("embedding", [])
        )

        results.append({
            "course_id": course["course_id"],
            "course_name": course["course_name"],
            "text": course["text"],
            "similarity": similarity
        })

    results.sort(
        key=lambda x: x["similarity"],
        reverse=True
    )

    return results[:top_k]


if __name__ == "__main__":
    query = "I want to learn AI and machine learning"

    results = retrieve_courses(query, top_k=3)

    print("\nQuery:", query)
    print("\nTop relevant courses:\n")

    for result in results:
        print(
            f"{result['course_id']} | "
            f"{result['course_name']} | "
            f"Similarity: {result['similarity']:.4f}"
        )