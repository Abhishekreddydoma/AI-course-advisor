import ast
import re
import sys
from pathlib import Path
from collections import Counter

app_file = Path("app/app.py")
content = app_file.read_text(encoding="utf-8")

# 1. Check duplicate widget keys
keys = re.findall(r'key\s*=\s*["\']([^"\']+)["\']', content)
counts = Counter(keys)
dups = {k: v for k, v in counts.items() if v > 1}
print("Duplicate widget keys:", dups)

# 2. Check all files for undefined variables or broken AST
for py_file in Path(".").rglob("*.py"):
    if ".venv" in str(py_file):
        continue
    code = py_file.read_text(encoding="utf-8")
    try:
        tree = ast.parse(code, filename=str(py_file))
    except SyntaxError as e:
        print(f"SyntaxError in {py_file}: {e}")

print("AST parse check complete.")
