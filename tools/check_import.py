import importlib, traceback, sys
from pathlib import Path

# Ensure repository root is on sys.path when running this helper from tools/
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

try:
    importlib.import_module('app.main')
    print('import ok')
except Exception:
    traceback.print_exc()
