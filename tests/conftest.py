"""
Fixtures de pytest. Requiere una Postgres real (el esquema usa UUID nativo
de Postgres, incompatible con SQLite) — se apunta a una DB de test separada
vía la env var TEST_DATABASE_URL, nunca a la DB de producción.
"""
import os
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

os.environ.setdefault(
    "DATABASE_URL",
    os.environ.get(
        "TEST_DATABASE_URL",
        "postgresql://postgres:testpass@localhost:5432/chile_transparente_test",
    ),
)

from app.core.database import Base  # noqa: E402
from app.models import Politico, Evento, Patrimonio, Empresa  # noqa: E402,F401

TEST_DATABASE_URL = os.environ["DATABASE_URL"]


@pytest.fixture(scope="session")
def engine():
    eng = create_engine(TEST_DATABASE_URL)
    with eng.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS unaccent"))
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
