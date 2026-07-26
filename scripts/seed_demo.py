"""Datos sintéticos coherentes para la demo local.

Todos los nombres, instituciones, casos y empresas de este archivo son
ficticios. No deben combinarse con una base de producción.
"""

from datetime import date, datetime
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.database import Base, SessionLocal, engine
from app.models import (
    Empresa,
    Evento,
    Familiar,
    FamiliarEmpresa,
    Patrimonio,
    Politico,
)


PEOPLE = [
    ("Amalia Torres Norte", "Diputada", "Alianza Cívica", "Antofagasta"),
    ("Bruno Salas Costa", "Alcalde", "Movimiento Regional", "Valparaíso"),
    ("Carla Méndez Ríos", "Senadora", "Frente Democrático", "Metropolitana"),
    ("Diego Vera Campos", "Diputado", "Alianza Cívica", "Metropolitana"),
    ("Elena Fuentes Mar", "Consejera regional", "Independiente", "O'Higgins"),
    ("Felipe Araya Sol", "Senador", "Frente Democrático", "Maule"),
    ("Gabriela Soto Valle", "Diputada", "Movimiento Regional", "Ñuble"),
    ("Hernán Lagos Sur", "Alcalde", "Independiente", "Biobío"),
    ("Inés Molina Bosque", "Diputada", "Alianza Cívica", "Los Ríos"),
    ("Javier Peña Austral", "Senador", "Frente Democrático", "Magallanes"),
    ("Karla Rojas Desierto", "Consejera regional", "Independiente", "Atacama"),
    ("Lucas Vidal Lagos", "Diputado", "Movimiento Regional", "Los Lagos"),
]

EVENTS = [
    (1, "Auditoría municipal de demostración", "administrativo", "en_revisión"),
    (2, "Revisión de declaración ficticia", "patrimonio", "investigado"),
    (2, "Contrato público sintético", "contratacion", "sobreseido"),
    (3, "Expediente judicial de demostración", "judicial", "formalizado"),
    (5, "Investigación administrativa ficticia", "administrativo", "en_revisión"),
    (7, "Causa cerrada de demostración", "judicial", "absuelto"),
    (8, "Sentencia sintética", "judicial", "condenado"),
    (10, "Revisión de compras ficticia", "contratacion", "investigado"),
]


def seed_demo(reset: bool = False) -> dict:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(Politico).count() and not reset:
            return {
                "politicos": db.query(Politico).count(),
                "eventos": db.query(Evento).count(),
                "estado": "existente",
            }

        if reset:
            db.query(FamiliarEmpresa).delete()
            db.query(Evento).delete()
            db.query(Familiar).delete()
            db.query(Empresa).delete()
            db.query(Patrimonio).delete()
            db.query(Politico).delete()
            db.flush()

        politicos = []
        for index, (nombre, cargo, partido, region) in enumerate(PEOPLE):
            politico = Politico(
                nombre_completo=nombre,
                cargo=cargo,
                institucion=(
                    "Cámara de Demostración" if "Diputad" in cargo
                    else "Senado de Demostración" if "Senad" in cargo
                    else "Institución territorial ficticia"
                ),
                partido=partido,
                region=region,
                distrito=f"Zona demo {index + 1}",
                periodo="2026–2030",
                es_activo=True,
            )
            db.add(politico)
            politicos.append(politico)
        db.flush()

        for offset, (person_index, title, event_type, status) in enumerate(EVENTS):
            db.add(Evento(
                politico_id=politicos[person_index].id,
                caso_nombre=title,
                tipo_alerta=event_type,
                resumen=(
                    "Antecedente completamente sintético utilizado para demostrar "
                    "cronologías, filtros y relaciones. No describe hechos reales."
                ),
                fecha_inicio=date(2023 + offset % 3, 2 + offset, 10 + offset),
                estado_actual=status,
                fuente="Archivo público ficticio",
                url_noticia=f"https://example.test/demo/noticia-{offset + 1}",
                url_oficial=f"https://example.test/demo/expediente-{offset + 1}",
                rit_ruc=f"DEMO-{2026}-{offset + 1:04d}",
                tribunal="Tribunal ficticio de demostración",
                confianza="ALTA",
                procesada_ia=offset % 2 == 0,
                verificada_humano=offset % 3 != 0,
                fecha_verificacion=datetime(2026, 7, 20) if offset % 3 != 0 else None,
            ))

        companies = []
        for index, politico in enumerate(politicos[:9]):
            patrimonio = Patrimonio(
                politico_id=politico.id,
                periodo="2025",
                patrimonio_total=10_000_000 + index * 2_750_000,
                fuente="Declaración patrimonial ficticia",
                url_detalle=f"https://example.test/demo/declaracion-{index + 1}",
            )
            db.add(patrimonio)
            db.flush()
            empresa = Empresa(
                patrimonio_id=patrimonio.id,
                rut_empresa=None,
                razon_social=f"Empresa Demostración {index + 1} SpA",
                tipo_sociedad="SpA ficticia",
                rol="Socio declarado",
                porcentaje_participacion=5 + index * 2.5,
                estado="Activa",
            )
            db.add(empresa)
            companies.append(empresa)
        db.flush()

        relatives = []
        for index, politico in enumerate(politicos[1:8:2]):
            familiar = Familiar(
                politico_id=politico.id,
                parentesco=("cónyuge" if index % 2 == 0 else "hermana"),
                nombre_completo=f"Familiar Demostración {index + 1}",
                rut=None,
                fuente="Declaración de intereses ficticia",
                url_fuente=f"https://example.test/demo/familiar-{index + 1}",
                verificada_humano=True,
            )
            db.add(familiar)
            relatives.append(familiar)
        db.flush()

        for index, familiar in enumerate(relatives):
            db.add(FamiliarEmpresa(
                familiar_id=familiar.id,
                empresa_id=companies[(index + 2) % len(companies)].id,
                rol_familiar="Representante ficticio",
                vinculo_politico="Vínculo declarado para demostración",
                fuente="Declaración de intereses ficticia",
                url_fuente=f"https://example.test/demo/vinculo-{index + 1}",
                verificada_humano=True,
            ))

        db.commit()
        return {
            "politicos": len(politicos),
            "eventos": len(EVENTS),
            "empresas": len(companies),
            "familiares": len(relatives),
            "estado": "creado",
        }
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print(seed_demo(reset=True))
