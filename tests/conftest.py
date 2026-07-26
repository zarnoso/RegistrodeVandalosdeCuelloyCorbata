"""
Fixtures de pytest. Requiere una Postgres real (el esquema usa UUID nativo
de Postgres, incompatible con SQLite) — se apunta a una DB de test separada
vía la env var TEST_DATABASE_URL, nunca a la DB de producción.
"""
import os
import pytest
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL")
if not TEST_DATABASE_URL:
    raise RuntimeError(
        "TEST_DATABASE_URL es obligatoria. Los tests nunca usan DATABASE_URL."
    )

test_database_name = make_url(TEST_DATABASE_URL).database or ""
if "test" not in test_database_name.lower():
    raise RuntimeError(
        "TEST_DATABASE_URL debe apuntar a una base cuyo nombre contenga 'test'."
    )

# app.core.database lee DATABASE_URL al importarse. Se sobrescribe de forma
# deliberada después de validar la URL de test; nunca se conserva la de producción.
os.environ["DATABASE_URL"] = TEST_DATABASE_URL

from app.core.database import Base, engine as app_engine  # noqa: E402
from app.models import (  # noqa: E402,F401
    Politico,
    Evento,
    Patrimonio,
    Empresa,
    Familiar,
    FamiliarEmpresa,
)


@pytest.fixture(scope="session")
def engine():
    eng = app_engine
    if eng.dialect.name == "postgresql":
        with eng.connect() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS unaccent"))
            conn.execute(text("""
                CREATE OR REPLACE FUNCTION immutable_unaccent(text)
                RETURNS text
                LANGUAGE sql
                IMMUTABLE
                PARALLEL SAFE
                STRICT
                AS $$ SELECT unaccent('unaccent', $1) $$
            """))
            conn.commit()
    return eng


@pytest.fixture(autouse=True)
def db_session(engine):
    """Crea tablas limpias antes de cada test y las destruye después."""
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
