import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from streamlit.testing.v1 import AppTest

print("--- 1. Testing Default Initial Render ---")
at = AppTest.from_file(str(PROJECT_ROOT / "app" / "app.py"), default_timeout=30)
at.run()
print("Initial exceptions:", len(at.exception))
assert len(at.exception) == 0

print("\n--- 2. Testing Reset Profile Button ---")
reset_btn = next((b for b in at.button if b.key == "btn_reset_main"), None)
if reset_btn:
    reset_btn.click().run()
    print("Reset run exceptions:", len(at.exception))
    assert len(at.exception) == 0

print("\n--- 3. Testing Custom Career Goal Flow ---")
at.selectbox(key="learner_career_goal").select("Other (Custom Role)")
at.run()
print("After selecting Other (Custom Role), exceptions:", len(at.exception))
assert len(at.exception) == 0

custom_input = next((ti for ti in at.text_input if ti.key == "learner_custom_career"), None)
print("Custom career text input mounted:", custom_input is not None)
assert custom_input is not None

custom_input.input("Robotics Specialist").run()
print("After entering custom role, exceptions:", len(at.exception))
assert len(at.exception) == 0

print("\n--- 4. Testing Empty / Minimal Inputs ---")
at.text_input(key="learner_education").input("")
at.selectbox(key="learner_experience").select("Beginner")
at.selectbox(key="learner_career_goal").select("Cloud Engineer")
at.multiselect(key="learner_skills").select([])
at.multiselect(key="learner_interests").select([])
at.run()
print("Empty inputs exceptions:", len(at.exception))
assert len(at.exception) == 0

print("\n--- 5. Testing Custom Skills & Interests with Comma Separated Strings ---")
at.text_input(key="learner_custom_skills").input("FastAPI, PyTorch, Kubernetes").run()
at.text_input(key="learner_custom_interests").input("Edge AI, Autonomous Vehicles").run()
print("Custom comma-separated inputs exceptions:", len(at.exception))
assert len(at.exception) == 0

print("\n--- ALL STREAMLIT APPTEST FLOWS PASSED WITH 0 EXCEPTIONS ---")
