"""Publica identidades oficiales desde staging sin borrar registros existentes."""

import argparse
import json
from pathlib import Path
import sys

from sqlalchemy import or_

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.database import SessionLocal  # noqa: E402
from app.models import Politico  # noqa: E402


def import_records(input_path: Path) -> dict[str, int]:
    payload = json.loads(input_path.read_text(encoding="utf-8"))
    records = payload.get("registros", [])
    db = SessionLocal()
    inserted = updated = skipped = 0
    try:
        for record in records:
            name = (record.get("nombre_completo") or "").strip()
            if not name:
                skipped += 1
                continue
            institution = record.get("institucion")
            existing = db.query(Politico).filter(
                Politico.nombre_completo.ilike(name),
                or_(Politico.institucion == institution, Politico.institucion.is_(None)),
            ).first()
            fields = {
                key: record.get(key)
                for key in (
                    "nombre_completo", "cargo", "institucion", "partido",
                    "distrito", "region", "foto_url",
                )
                if record.get(key) is not None
            }
            fields["es_activo"] = True
            if existing:
                for key, value in fields.items():
                    setattr(existing, key, value)
                updated += 1
            else:
                db.add(Politico(**fields))
                inserted += 1
        db.commit()
        return {"inserted": inserted, "updated": updated, "skipped": skipped}
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        type=Path,
        default=PROJECT_ROOT / "data" / "staging_fuentes_oficiales.json",
    )
    args = parser.parse_args()
    print(import_records(args.input))
