"""Arranca la demo completa con SQLite y datos 100% ficticios."""

import os
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
DATA_DIR = PROJECT_ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)

# Deben definirse antes de importar cualquier módulo de app.
os.environ["DEMO_MODE"] = "true"
os.environ["DATABASE_URL"] = f"sqlite:///{(DATA_DIR / 'demo.db').as_posix()}"

import uvicorn  # noqa: E402

from scripts.seed_demo import seed_demo  # noqa: E402


if __name__ == "__main__":
    result = seed_demo()
    print(f"Demo lista: {result}")
    print("Abre http://127.0.0.1:8000")
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=False)
