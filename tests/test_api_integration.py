"""Tests de integración: llaman los endpoints HTTP reales (TestClient),
usando la sesión de test (Postgres real) inyectada vía dependency override."""
from datetime import date
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import get_db
from app.models import Politico, Evento


@pytest.fixture
def client(db_session):
    app.dependency_overrides[get_db] = lambda: db_session
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def _crear_politico(db, **overrides):
    datos = dict(
        rut="1.111.111-1", nombre_completo="Juan Pérez Soto",
        cargo="Diputado", institucion="Cámara de Diputados",
        partido="UDI", es_activo=True,
    )
    datos.update(overrides)
    p = Politico(**datos)
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


def test_health(client):
    res = client.get("/health")
    assert res.status_code == 200


def test_lista_politicos_vacia(client):
    res = client.get("/api/politicos/")
    assert res.status_code == 200
    assert res.json() == []


def test_lista_politicos_con_datos(client, db_session):
    _crear_politico(db_session, nombre_completo="Ana Torres", rut="1")

    res = client.get("/api/politicos/")

    assert res.status_code == 200
    data = res.json()
    assert len(data) == 1
    assert data[0]["nombre_completo"] == "Ana Torres"
    assert data[0]["estado_riesgo"] == "sin_registros"


def test_busqueda_por_nombre_tolera_tildes(client, db_session):
    _crear_politico(db_session, nombre_completo="José Núñez", rut="2")

    res = client.get("/api/politicos/", params={"busqueda": "jose nunez"})

    assert res.status_code == 200
    assert len(res.json()) == 1


def test_detalle_politico_incluye_eventos(client, db_session):
    p = _crear_politico(db_session, rut="3")
    db_session.add(Evento(
        politico_id=p.id, caso_nombre="Caso Test", tipo_alerta="fraude",
        estado_actual="formalizado", fecha_inicio=date(2024, 1, 1),
    ))
    db_session.commit()

    res = client.get(f"/api/politicos/{p.id}")

    assert res.status_code == 200
    data = res.json()
    assert len(data["eventos"]) == 1
    assert data["eventos"][0]["caso_nombre"] == "Caso Test"


def test_detalle_politico_inexistente_404(client):
    res = client.get("/api/politicos/00000000-0000-0000-0000-000000000000")
    assert res.status_code == 404


def test_buscar_por_rut(client, db_session):
    _crear_politico(db_session, rut="9.999.999-9", nombre_completo="Test Rut")

    res = client.get("/api/politicos/buscar/rut/9.999.999-9")

    assert res.status_code == 200
    assert res.json()["nombre_completo"] == "Test Rut"


def test_buscar_por_rut_inexistente_404(client):
    res = client.get("/api/politicos/buscar/rut/0.000.000-0")
    assert res.status_code == 404


def test_rate_limit_buscar_rut(client):
    # límite: 30/minute. Se dispara la 31.
    for _ in range(30):
        client.get("/api/politicos/buscar/rut/0.000.000-0")

    res = client.get("/api/politicos/buscar/rut/0.000.000-0")
    assert res.status_code == 429
