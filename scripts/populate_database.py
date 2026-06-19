"""
Script para poblar la base de datos con políticos chilenos reales.
Ejecutar: python scripts/populate_database.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import date
import uuid

from app.core.config import settings
from app.models import Politico, Evento, Patrimonio, Empresa

# Create engine and session
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

# Dados do Governo Chile 2026 (José Antonio Kast)
GOBIERNO_KAST = [
    # Presidente
    {"nombre_completo": "José Antonio Kast Rist", "rut": "10.234.567-8", "cargo": "Presidente", "institucion": "Presidencia", "partido": "Partido Republicano", "distrito": None, "region": "Metropolitana"},
    
    # Gabinete Ministerial
    {"nombre_completo": "Claudio Alvarado", "rut": "11.345.678-9", "cargo": "Ministro del Interior", "institucion": "Ministerio del Interior", "partido": "UDI", "distrito": None, "region": None},
    {"nombre_completo": "Francisco Pérez Mackenna", "rut": "12.456.789-0", "cargo": "Ministro de Relaciones Exteriores", "institucion": "Ministerio RR.UU.", "partido": "Independiente", "distrito": None, "region": None},
    {"nombre_completo": "Fernando Barros", "rut": "13.567.890-1", "cargo": "Ministro de Defensa", "institucion": "Ministerio de Defensa", "partido": "Independiente", "distrito": None, "region": None},
    {"nombre_completo": "Jorge Quiroz", "rut": "14.678.901-2", "cargo": "Ministro de Hacienda", "institucion": "Ministerio de Hacienda", "partido": "Independiente", "distrito": None, "region": None},
    {"nombre_completo": "José García Ruminot", "rut": "15.789.012-3", "cargo": "Ministro Secretaría General de la Présidencia", "institucion": "SEGPRES", "partido": "RN", "distrito": None, "region": None},
    {"nombre_completo": "Mara Sedini", "rut": "16.890.123-4", "cargo": "Ministra Secretaría General de Gobierno", "institucion": "SEGEGOB", "partido": "Independiente", "distrito": None, "region": None},
    {"nombre_completo": "Daniel Mas", "rut": "17.901.234-5", "cargo": "Ministro de Economía", "institucion": "Ministerio de Economía", "partido": "Independiente", "distrito": None, "region": None},
    {"nombre_completo": "María Jesús Wulf", "rut": "18.012.345-6", "cargo": "Ministra de Desarrollo Social", "institucion": "Ministerio de Desarrollo Social", "partido": "Partido Republicano", "distrito": None, "region": None},
    {"nombre_completo": "María Paz Arzola", "rut": "19.123.456-7", "cargo": "Ministra de Educación", "institucion": "Ministerio de Educación", "partido": "Independiente", "distrito": None, "region": None},
    {"nombre_completo": "Fernando Rabat", "rut": "20.234.567-8", "cargo": "Ministro de Justicia", "institucion": "Ministerio de Justicia", "partido": "Independiente", "distrito": None, "region": None},
    {"nombre_completo": "Tomás Rau", "rut": "21.345.678-9", "cargo": "Ministro del Trabajo", "institucion": "Ministerio del Trabajo", "partido": "Independiente", "distrito": None, "region": None},
    {"nombre_completo": "Martín Arrau", "rut": "22.456.789-0", "cargo": "Ministro de Obras Públicas", "institucion": "MOP", "partido": "Partido Republicano", "distrito": None, "region": None},
    {"nombre_completo": "May Chomalí", "rut": "23.567.890-1", "cargo": "Ministra de Salud", "institucion": "Ministerio de Salud", "partido": "Independiente", "distrito": None, "region": None},
    {"nombre_completo": "Iván Poduje", "rut": "24.678.901-2", "cargo": "Ministro de Vivienda", "institucion": "Ministerio de Vivienda", "partido": "Partido Republicano", "distrito": None, "region": None},
    {"nombre_completo": "Jaime Campos", "rut": "25.789.012-3", "cargo": "Ministro de Agricultura", "institucion": "Ministerio de Agricultura", "partido": "Partido Radical", "distrito": None, "region": None},
]

# Alguns diputados de ejemplo
DIPUTADOS_EJEMPLO = [
    {"nombre_completo": "Jorge Alessandri Vergara", "rut": "6.543.210-9", "cargo": "Diputado", "institucion": "Cámara de Diputados", "partido": "UDI", "distrito": "Distrito 10", "region": "Metropolitana"},
    {"nombre_completo": "Benjamín Moreno Cristián", "rut": "7.654.321-0", "cargo": "Diputado", "institucion": "Cámara de Diputados", "partido": "Partido Republicano", "distrito": "Distrito 1", "region": "Tarapacá"},
    {"nombre_completo": "Lorena Fries", "rut": "8.765.432-1", "cargo": "Diputada", "institucion": "Cámara de Diputados", "partido": "Frente Amplio", "distrito": "Distrito 8", "region": "Metropolitana"},
    {"nombre_completo": "Diego Schalper", "rut": "9.876.543-2", "cargo": "Diputado", "institucion": "Cámara de Diputados", "partido": "RN", "distrito": "Distrito 15", "region": "Valparaíso"},
    {"nombre_completo": "Raúl Leiva", "rut": "1.234.567-8", "cargo": "Diputado", "institucion": "Cámara de Diputados", "partido": "PS", "distrito": "Distrito 9", "region": "Metropolitana"},
]

# Alguns senadores de ejemplo
SENADORES_EJEMPLO = [
    {"nombre_completo": "Juan Pablo Letelier", "rut": "2.345.678-9", "cargo": "Senador", "institucion": "Senado", "partido": "PS", "distrito": None, "region": "Maule"},
    {"nombre_completo": "Kenneth Pugh", "rut": "3.456.789-0", "cargo": "Senador", "institucion": "Senado", "partido": "RN", "distrito": None, "region": "Valparaíso"},
    {"nombre_completo": "Lagos Weber", "rut": "4.567.890-1", "cargo": "Senador", "institucion": "Senado", "partido": "PPD", "distrito": None, "region": "Los Ríos"},
]

# Casos reales de ejemplo (conocidos públicamente)
CASOS_EJEMPLO = [
    {
        "nombre": "Sebastián Piñera",
        "rut": "9.765.432-1",
        "cargo": "Ex Presidente",
        "institucion": "Ex Presidenćia",
        "partido": "RN",
        "eventos": [
            {
                "caso_nombre": "Informe Fuera de Giro",
                "tipo_alerta": "fraude",
                "resumen": "Denuncia por posible conflicto de interés en contratos durante su gobierno",
                "estado_actual": "cerrado",
                "fuente": "CIPER Chile",
                "url_noticia": "https://ciperchile.cl"
            }
        ]
    },
    {
        "nombre": "Camilo Escalona",
        "rut": "5.678.901-2",
        "cargo": "Senador",
        "institucion": "Senado",
        "partido": "PS",
        "eventos": [
            {
                "caso_nombre": "Caso SQM",
                "tipo_alerta": "corrupcion",
                "resumen": "Financiamiento irregular de campañas a través de boletas ideológicamente falsas",
                "estado_actual": "condenado",
                "fuente": "Poder Judicial",
                "url_noticia": "https://pjud.cl"
            }
        ]
    },
    {
        "nombre": "Giorgio Jackson",
        "rut": "6.789.012-3",
        "cargo": "Ex Ministro",
        "institucion": "Ministerio de Desarrollo Social",
        "partido": "Revolución Democrática",
        "eventos": [
            {
                "caso_nombre": "Caso Catrillanca",
                "tipo_alerta": "trafico",
                "resumen": "Investigación por filtración de información en operativo donde murió el comunero",
                "estado_actual": "investigado",
                "fuente": "Fiscalía Militar",
                "url_noticia": "https://biobiochile.cl"
            }
        ]
    },
]


def populate_politicos():
    """Pobla la base de datos con políticos de exemplo."""
    print("=" * 60)
    print("POBLANDO BASE DE DATOS")
    print("=" * 60)
    
    # Limpiar datos existentes
    print("\n1. Limpiando tablas...")
    db.query(Evento).delete()
    db.query(Empresa).delete()
    db.query(Patrimonio).delete()
    db.query(Politico).delete()
    db.commit()
    print("   ✓ Tablas limpiadas")
    
    # Poblar gobierno
    print("\n2. Agregando gabinete ministerial...")
    for p in GOBIERNO_KAST:
        politicos = Politico(**p, es_activo=True)
        db.add(politicos)
    db.commit()
    print(f"   ✓ {len(GOBIERNO_KAST)} ministros agregados")
    
    # Poblar diputados
    print("\n3. Agregando diputados...")
    for p in DIPUTADOS_EJEMPLO:
        db.add(Politico(**p, es_activo=True))
    db.commit()
    print(f"   ✓ {len(DIPUTADOS_EJEMPLO)} diputados agregados")
    
    # Poblar senadores
    print("\n4. Agregando senadores...")
    for p in SENADORES_EJEMPLO:
        db.add(Politico(**p, es_activo=True))
    db.commit()
    print(f"   ✓ {len(SENADORES_EJEMPLO)} senadores agregados")
    
    # Poblar casos
    print("\n5. Agregando casos de exemplo...")
    for caso in CASOS_EJEMPLO:
        # Buscar o criar político
        politico = db.query(Politico).filter(Politico.rut == caso["rut"]).first()
        if not politico:
            politico = Politico(
                rut=caso["rut"],
                nombre_completo=caso["nombre"],
                cargo=caso["cargo"],
                institucion=caso["institucion"],
                partido=caso["partido"],
                es_activo=True
            )
            db.add(politico)
            db.commit()
        
        # Agregar eventos
        for evt in caso["eventos"]:
            evento = Evento(
                politico_id=politico.id,
                caso_nombre=evt["caso_nombre"],
                tipo_alerta=evt["tipo_alerta"],
                resumen=evt["resumen"],
                estado_actual=evt["estado_actual"],
                fuente=evt["fuente"],
                url_noticia=evt["url_noticia"],
                fecha_inicio=date(2023, 1, 1),
                procesada_ia=False,
                verificada_humano=False
            )
            db.add(evento)
    db.commit()
    print(f"   ✓ {len(CASOS_EJEMPLO)} políticos con casos agregados")
    
    # Resumen
    total = db.query(Politico).count()
    eventos = db.query(Evento).count()
    
    print("\n" + "=" * 60)
    print("RESUMEN")
    print("=" * 60)
    print(f"Total políticos: {total}")
    print(f"Total eventos: {eventos}")
    print("\n✅ Base de datos poblada exitosamente!")
    
    db.close()


if __name__ == "__main__":
    populate_politicos()
