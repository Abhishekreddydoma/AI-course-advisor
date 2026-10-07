import os
import sys
import json
import math
import urllib.request
from pathlib import Path

# Setup project root in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

TEST_PROFILE = {
    "education": "B.Tech ECE",
    "skills": ["Python", "Basic SQL", "Basic Cloud"],
    "experience": "Beginner",
    "interests": ["AI", "Cloud Computing"],
    "career_goal": "Cloud Engineer"
}

results = {}

def check(test_num, name, condition, details=""):
    status = "PASS" if condition else "FAIL"
    results[f"{test_num}. {name}"] = (status, details)
    print(f"[{status}] {test_num}. {name}: {details}")
    return condition

print("=" * 70)
print("COMPREHENSIVE END-TO-END VALIDATION SUITE")
print("=" * 70)

# 1. Python Environment
py_ver = sys.version.split()[0]
check(1, "Python Environment", sys.version_info >= (3, 10), f"Python {py_ver} at {sys.executable}")

# 2. Required Packages
required_pkgs = ["streamlit", "langchain", "chromadb", "pydantic", "dotenv"]
missing_pkgs = []
for pkg in required_pkgs:
    try:
        __import__(pkg)
    except ImportError:
        missing_pkgs.append(pkg)
check(2, "Required Packages", len(missing_pkgs) == 0, f"Missing: {missing_pkgs}" if missing_pkgs else "All core packages available")

# 3. Ollama Availability
ollama_ok = False
try:
    with urllib.request.urlopen("http://localhost:11434/api/tags", timeout=5) as resp:
        if resp.status == 200:
            ollama_ok = True
            tags_data = json.loads(resp.read().decode("utf-8"))
except Exception as e:
    tags_data = {"models": []}
check(3, "Ollama Availability", ollama_ok, "Ollama responding on http://localhost:11434" if ollama_ok else "Ollama unreachable")

# 4 & 5. Models: qwen2.5:3b and nomic-embed-text
available_models = [m.get("name", "") for m in tags_data.get("models", [])]
qwen_ok = any("qwen2.5:3b" in m for m in available_models)
nomic_ok = any("nomic-embed-text" in m for m in available_models)
check(4, "qwen2.5:3b Model Availability", qwen_ok, f"Found models: {available_models}")
check(5, "nomic-embed-text Model Availability", nomic_ok, f"Found models: {available_models}")

# 6 & 7. courses.json & Exactly 20 courses
courses_path = PROJECT_ROOT / "data" / "raw" / "courses.json"
courses_json_ok = False
course_count = 0
courses = []
if courses_path.exists():
    try:
        with open(courses_path, "r", encoding="utf-8") as f:
            courses = json.load(f)
        courses_json_ok = isinstance(courses, list)
        course_count = len(courses)
    except Exception as e:
        courses_json_ok = False
check(6, "courses.json Valid JSON", courses_json_ok, f"Path: {courses_path}")
check(7, "Exactly 20 Courses", course_count == 20, f"Found {course_count} courses")

# 8. RAG Ingestion
# We can verify that data/vectorstore/courses_embeddings.json has embeddings for each course
emb_path = PROJECT_ROOT / "data" / "vectorstore" / "courses_embeddings.json"
ingest_ok = False
if emb_path.exists():
    try:
        with open(emb_path, "r", encoding="utf-8") as f:
            embs = json.load(f)
        ingest_ok = len(embs) == 20 and all("embedding" in c and len(c["embedding"]) > 0 for c in embs)
    except Exception:
        ingest_ok = False
check(8, "RAG Ingestion", ingest_ok, f"{len(embs) if 'embs' in locals() else 0} course embeddings stored in {emb_path.name}")

# 9. Vectorstore
check(9, "Vectorstore Existence & Non-Empty", emb_path.exists() and emb_path.stat().st_size > 1000, f"Size: {emb_path.stat().st_size if emb_path.exists() else 0} bytes")

# 10. RAG Retrieval
from rag.retriever import retrieve_courses
retrieval_res = retrieve_courses("Cloud computing AWS DevOps", top_k=3)
rag_retrieval_ok = len(retrieval_res) > 0 and all(r.get("similarity", 0) > 0 for r in retrieval_res)
check(10, "RAG Retrieval", rag_retrieval_ok, f"Top match: {retrieval_res[0]['course_name']} (similarity {retrieval_res[0]['similarity']:.4f})")

# 11. Profile Agent
from agents.profile_agent import profile_analysis
profile_res = profile_analysis(TEST_PROFILE)
check(11, "Profile Agent", isinstance(profile_res, str) and len(profile_res) > 20, f"Analysis length: {len(profile_res)} chars")

# 12. Course Research Agent
from agents.course_research_agent import research_courses
research_res = research_courses(TEST_PROFILE)
retrieved_in_research = research_res.get("retrieved_courses", [])
check(12, "Course Research Agent", len(retrieved_in_research) > 0, f"Retrieved {len(retrieved_in_research)} courses, explanation provided")

# 13. Prerequisite Agent
from agents.prerequisite_agent import check_prerequisites, find_course, load_courses, analyze_prerequisites
all_c = load_courses()
py_course = find_course("Python for Beginners", all_c)
py_res = check_prerequisites(py_course, TEST_PROFILE["skills"])
py_sat, py_mis = py_res["satisfied"], py_res["missing"]
cloud_course = find_course("AWS Solutions Architect Fundamentals", all_c)
cl_res = check_prerequisites(cloud_course, TEST_PROFILE["skills"])
cl_sat, cl_mis = cl_res["satisfied"], cl_res["missing"]
analyzed = analyze_prerequisites("AWS Solutions Architect Fundamentals", TEST_PROFILE["skills"])
prereq_ok = len(py_mis) == 0 and "AWS Cloud Foundations" in cl_mis and "readiness" in analyzed
check(13, "Prerequisite Agent", prereq_ok, f"Python prereqs satisfied ({py_sat}). AWS Solutions Architect missing: {cl_mis}")

# 14. Recommendation Agent
from agents.recommendation_agent import recommend_courses
raw_rec = recommend_courses(TEST_PROFILE)
from app.app import parse_recommendation_output, enrich_course
rec_parsed = parse_recommendation_output(raw_rec)
recs = rec_parsed.get("recommendations", [])
# Verify: Python for Beginners is recognized as already known (Skip - Skill Already Present)
py_rec = next((c for c in recs if c.get("course_name") == "Python for Beginners"), None)
py_skipped = py_rec is not None and (py_rec.get("ui_status") == "Skip - Skill Already Present" or py_rec.get("score") == 0)
# Verify relevant cloud courses identified
cloud_recs = [c for c in recs if "Cloud" in c.get("course_name", "") or c.get("category") == "Cloud Computing"]
# Verify readiness separate from score
readiness_separate = all(("ui_readiness" in c or "readiness" in c) and "score" in c for c in recs)
rec_ok = len(recs) == 20 and py_skipped and len(cloud_recs) > 0 and readiness_separate
check(14, "Recommendation Agent", rec_ok, f"Total courses: {len(recs)}, Python skipped: {py_skipped}, Cloud courses: {len(cloud_recs)}, Best: {rec_parsed.get('best_course')}")

# 15. Learning Path Agent
from agents.learning_path_agent import learning_path_agent
enriched_recs = [enrich_course(c, TEST_PROFILE["skills"]) for c in recs]
lp_res = learning_path_agent(TEST_PROFILE, enriched_recs)
lp_items = lp_res.get("learning_path", []) if isinstance(lp_res, dict) else []
# Verify Python for Beginners is NOT in learning path
py_in_lp = any("Python for Beginners" in (item.get("item") if isinstance(item, dict) else str(item)) for item in lp_items)
lp_ok = len(lp_items) > 0 and not py_in_lp
check(15, "Learning Path Agent", lp_ok, f"{len(lp_items)} roadmap items. Python for Beginners excluded: {not py_in_lp}")

# 16. Orchestrator
from agents.orchestrator_agent import run_workflow
print("\nRunning Orchestrator Agent verification...")
from agents.orchestrator_agent import load_agent
p_name, p_func = load_agent("agents.profile_agent", ["profile_analysis", "analyze_profile"])
r_name, r_func = load_agent("agents.course_research_agent", ["research_courses"])
pr_name, pr_func = load_agent("agents.prerequisite_agent", ["analyze_prerequisites"])
rec_name, rec_func = load_agent("agents.recommendation_agent", ["recommend_courses"])
lp_name, lp_func = load_agent("agents.learning_path_agent", ["learning_path_agent", "generate_learning_path"])
orch_ok = all(f is not None for f in [p_func, r_func, pr_func, rec_func, lp_func])
check(16, "Orchestrator Agent Integrity", orch_ok, f"All 5 agents dynamically resolved: {[p_name, r_name, pr_name, rec_name, lp_name]}")

# 17. Streamlit Application
from streamlit.testing.v1 import AppTest
at = AppTest.from_file(str(PROJECT_ROOT / "app" / "app.py"), default_timeout=30)
at.run()
st_ok = len(at.exception) == 0
text_inputs = [ti.key for ti in at.text_input]
selectboxes = [sb.key for sb in at.selectbox]
multiselects = [ms.key for ms in at.multiselect]
# Check exact single active inputs
single_inputs = (
    text_inputs.count("learner_education") == 1 and
    selectboxes.count("learner_experience") == 1 and
    selectboxes.count("learner_career_goal") == 1 and
    multiselects.count("learner_skills") == 1 and
    multiselects.count("learner_interests") == 1
)
check(17, "Streamlit Application", st_ok and single_inputs, f"Exceptions: {len(at.exception)}, Unique widgets validated: {single_inputs}")

# 18. End-to-End Workflow with Test Profile
print("\nValidating End-to-End Streamlit Workflow with specified profile...")
at.text_input(key="learner_education").input(TEST_PROFILE["education"])
at.selectbox(key="learner_experience").select(TEST_PROFILE["experience"])
at.selectbox(key="learner_career_goal").select(TEST_PROFILE["career_goal"])
at.multiselect(key="learner_skills").select(TEST_PROFILE["skills"])
at.multiselect(key="learner_interests").select(TEST_PROFILE["interests"])
at.run()

# Click generate
gen_btn = next((b for b in at.button if b.key in ("btn_generate_sidebar", "btn_generate_main")), None)
gen_btn.click().run(timeout=300)

e2e_ok = (
    len(at.exception) == 0 and
    "advisor_result" in at.session_state and
    at.session_state["advisor_result"] is not None
)

if e2e_ok:
    adv = at.session_state["advisor_result"]
    adv_profile = adv.get("profile", {})
    adv_recs = adv.get("recommendations", [])
    adv_best = adv.get("recommendation_result", {}).get("best_course")
    details = f"Best course: '{adv_best}', Total recommendations: {len(adv_recs)}, Profile saved: {adv_profile.get('career_goal')}"
else:
    details = f"Exceptions: {at.exception}"
check(18, "End-to-End Generate Course Roadmap", e2e_ok, details)

print("\n" + "=" * 70)
print("FINAL SUMMARY OF 18 VALIDATION CRITERIA:")
print("=" * 70)
all_pass = all(v[0] == "PASS" for v in results.values())
for k, v in results.items():
    print(f"{k:45}: {v[0]} ({v[1]})")

print("\nOVERALL PROJECT STATUS:", "WORKING" if all_pass else "FAILURES DETECTED")
