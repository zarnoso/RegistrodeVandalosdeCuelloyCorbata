from difflib import SequenceMatcher
import unicodedata

from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

engine_options = {"pool_pre_ping": True}
if settings.DATABASE_URL.startswith("sqlite"):
    engine_options["connect_args"] = {"check_same_thread": False}
else:
    engine_options.update({"pool_size": 5, "max_overflow": 10})

engine = create_engine(settings.DATABASE_URL, **engine_options)


if settings.DATABASE_URL.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def register_demo_search_functions(dbapi_connection, connection_record):
        """Equivalentes locales de unaccent/similarity usados por PostgreSQL."""
        def normalize(value):
            if value is None:
                return ""
            return "".join(
                char for char in unicodedata.normalize("NFKD", value.lower())
                if not unicodedata.combining(char)
            )

        def similarity(left, right):
            return SequenceMatcher(None, normalize(left), normalize(right)).ratio()

        dbapi_connection.create_function(
            "immutable_unaccent", 1, normalize, deterministic=True
        )
        dbapi_connection.create_function("similarity", 2, similarity, deterministic=True)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()


def get_db():
    """Dependency to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
