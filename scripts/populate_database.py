"""Reinicia una base de desarrollo con datos completamente ficticios."""

import os
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models import Empresa, Evento, Patrimonio, Politico


POLITICOS_DEMO = [
    {
        "nombre_completo": "Persona Demostración Norte",
        "rut": None,
        "cargo": "Cargo ficticio",
        "institucion": "Institución de demostración",
        "partido": "Partido de ejemplo",
        "region": "Región ficticia",
        "es_activo": True,
    },
    {
        "nombre_completo": "Persona Demostración Sur",
        "rut": None,
        "cargo": "Cargo ficticio",
        "institucion": "Institución de demostración",
        "partido": "Independiente",
        "region": "Región ficticia",
        "es_activo": True,
    },
]


def _validate_demo_database() -> None:
    if os.environ.get("ALLOW_DESTRUCTIVE_DEMO_DATA", "").lower() != "true":
        raise RuntimeError(
            "Operación bloqueada. Define ALLOW_DESTRUCTIVE_DEMO_DATA=true "
            "solo para una base local de desarrollo o pruebas."
        )

    database_name = (make_url(settings.DATABASE_URL).database or "").lower()
    if not any(marker in database_name for marker in ("test", "dev", "local", "demo")):
        raise RuntimeError(
            "Operación bloqueada: el nombre de la base debe contener "
            "'test', 'dev', 'local' o 'demo'."
        )


def populate_politicos() -> None:
    """Borra las tablas de la aplicación y carga un conjunto ficticio mínimo."""
    _validate_demo_database()

    engine = create_engine(settings.DATABASE_URL)
    session_factory = sessionmaker(bind=engine)
    db = session_factory()

    try:
        # El orden respeta las claves foráneas.
        db.query(Evento).delete()
        db.query(Empresa).delete()
        db.query(Patrimonio).delete()
        db.query(Politico).delete()

        politicos = [Politico(**data) for data in POLITICOS_DEMO]
        db.add_all(politicos)
        db.flush()

        db.add(
            Evento(
                politico_id=politicos[0].id,
                caso_nombre="Caso completamente ficticio",
                tipo_alerta="demostracion",
                resumen=(
                    "Registro sintético para probar la interfaz. "
                    "No representa hechos ni personas reales."
                ),
                estado_actual="en_revisión",
                fuente="Datos ficticios locales",
                fecha_inicio=date(2024, 1, 1),
                procesada_ia=False,
                verificada_humano=False,
            )
        )
        db.commit()
        print("Base de demostración reiniciada con datos ficticios.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
        engine.dispose()


if __name__ == "__main__":
    populate_politicos()
