"""Smoke test: cada módulo .py del repo debe parsear sin SyntaxError.
No importa módulos con dependencias externas pesadas (scrapers/LLM) para no
requerir red ni API keys — solo valida sintaxis, que es justamente el tipo
de bug (dict mal anidado) que rompió 02_scraper_patrimonio.py sin que nadie
lo notara.
"""
import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
EXCLUDE_DIRS = {".git", "node_modules", "venv", "__pycache__", "tests"}


def _python_files():
    for path in REPO_ROOT.rglob("*.py"):
        if any(part in EXCLUDE_DIRS for part in path.parts):
            continue
        yield path


def test_todos_los_modulos_parsean_sin_error():
    errores = []
    for path in _python_files():
        try:
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError as e:
            errores.append(f"{path.relative_to(REPO_ROOT)}: {e}")

    assert not errores, "Archivos con SyntaxError:\n" + "\n".join(errores)


def test_app_importa_sin_efectos_secundarios():
    """app/main.py no debe tocar la DB al solo importarlo (create_all va en startup)."""
    import app.main  # noqa: F401
    assert hasattr(app.main, "app")
