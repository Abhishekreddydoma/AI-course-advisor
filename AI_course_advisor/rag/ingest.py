import json
import os
import sys
import urllib.request
from pathlib import Path

# Safe encoding for console output
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

PROJECT_ROOT = Path(__file__).resolve().parent.parent
COURSE_FILE = PROJECT_ROOT / "data" / "raw" / "courses.json"
VECTORSTORE_DIR = PROJECT_ROOT / "data" / "vectorstore"
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

    with urllib.request.urlopen(request, timeout=120) as response:
        result = json.loads(response.read().decode("utf-8"))

    return result["embeddings"][0]


def course_to_text(course):
    return f"""
Course Name: {course['course_name']}
Category: {course['category']}
Difficulty: {course['difficulty']}
Prerequisites: {', '.join(course['prerequisites'])}
Skills: {', '.join(course['skills'])}
Learning Outcomes: {', '.join(course['learning_outcomes'])}
""".strip()


def main():
    with open(COURSE_FILE, "r", encoding="utf-8") as f:
        courses = json.load(f)

    documents = []

    print(f"Found {len(courses)} courses.")
    print("Generating embeddings...")

    for course in courses:
        text = course_to_text(course)

        embedding = get_embedding(text)

        documents.append({
            "course_id": course["course_id"],
            "course_name": course["course_name"],
            "text": text,
            "embedding": embedding
        })

        print(f"[OK] Embedded: {course['course_name']}")

    os.makedirs(VECTORSTORE_DIR, exist_ok=True)

    output_file = VECTORSTORE_DIR / "courses_embeddings.json"

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(documents, f, indent=2)

    print("\nRAG ingestion completed!")
    print(f"Saved to: {output_file}")


if __name__ == "__main__":
    main()