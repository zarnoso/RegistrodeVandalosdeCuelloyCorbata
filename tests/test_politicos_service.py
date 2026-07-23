from datetime import date
from app.models import Politico, Evento, Patrimonio, Empresa
from app.services.politicos_service import PoliticosService


def _crear_politico(db, **overrides):
    datos = dict(
        rut="1.111.111-1",
        nombre_completo="Juan Pérez Soto",
        cargo="Diputado",
        institucion="Cámara de Diputados",
        partido="UDI",
        es_activo=True,
    )
    datos.update(overrides)
    p = Politico(**datos)
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


class TestGetAll:
    def test_solo_devuelve_activos(self, db_session):
        _crear_politico(db_session, nombre_completo="Activo Uno", rut="1")
        _crear_politico(db_session, nombre_completo="Inactivo Uno", rut="2", es_activo=False)

        resultado = PoliticosService.get_all(db_session)

        nombres = [p.nombre_completo for p in resultado]
        assert "Activo Uno" in nombres
        assert "Inactivo Uno" not in nombres

    def test_filtro_por_partido(self, db_session):
        _crear_politico(db_session, nombre_completo="A", rut="1", partido="UDI")
        _crear_politico(db_session, nombre_completo="B", rut="2", partido="PS")

        resultado = PoliticosService.get_all(db_session, partido="PS")

        assert len(resultado) == 1
        assert resultado[0].partido == "PS"

    def test_busqueda_por_nombre_ignora_mayusculas(self, db_session):
        _crear_politico(db_session, nombre_completo="María González", rut="1")

        resultado = PoliticosService.get_all(db_session, busqueda="maria gonz")

        assert len(resultado) == 1
        assert resultado[0].nombre_completo == "María González"

    def test_busqueda_sin_coincidencias_devuelve_vacio(self, db_session):
        _crear_politico(db_session, nombre_completo="María González", rut="1")

        resultado = PoliticosService.get_all(db_session, busqueda="nombre_que_no_existe")

        assert resultado == []


class TestGetByRut:
    def test_encuentra_por_rut_exacto(self, db_session):
        _crear_politico(db_session, rut="12.345.678-9", nombre_completo="Test")

        resultado = PoliticosService.get_by_rut(db_session, "12.345.678-9")

        assert resultado is not None
        assert resultado.nombre_completo == "Test"

    def test_rut_inexistente_devuelve_none(self, db_session):
        assert PoliticosService.get_by_rut(db_session, "0.000.000-0") is None


class TestEnrichWithCounts:
    def test_sin_eventos_es_sin_registros(self, db_session):
        p = _crear_politico(db_session, rut="1")

        enriquecido = PoliticosService.enrich_with_counts(db_session, [p])

        assert enriquecido[0]["estado_riesgo"] == "sin_registros"
        assert enriquecido[0]["num_eventos"] == 0

    def test_evento_formalizado_es_alerta_roja(self, db_session):
        p = _crear_politico(db_session, rut="1")
        db_session.add(Evento(
            politico_id=p.id, caso_nombre="Caso X", tipo_alerta="corrupcion",
            estado_actual="formalizado", fecha_inicio=date(2024, 1, 1),
        ))
        db_session.commit()

        enriquecido = PoliticosService.enrich_with_counts(db_session, [p])

        assert enriquecido[0]["estado_riesgo"] == "alerta_roja"
        assert enriquecido[0]["num_eventos"] == 1

    def test_evento_en_revision_es_alerta_naranja(self, db_session):
        p = _crear_politico(db_session, rut="1")
        db_session.add(Evento(
            politico_id=p.id, caso_nombre="Caso Y", tipo_alerta="fraude",
            estado_actual="en_revisión", fecha_inicio=date(2024, 1, 1),
        ))
        db_session.commit()

        enriquecido = PoliticosService.enrich_with_counts(db_session, [p])

        assert enriquecido[0]["estado_riesgo"] == "alerta_naranja"

    def test_cuenta_empresas_via_patrimonio(self, db_session):
        p = _crear_politico(db_session, rut="1")
        pat = Patrimonio(politico_id=p.id, periodo="2024")
        db_session.add(pat)
        db_session.commit()
        db_session.add(Empresa(patrimonio_id=pat.id, razon_social="Empresa X SpA"))
        db_session.commit()

        enriquecido = PoliticosService.enrich_with_counts(db_session, [p])

        assert enriquecido[0]["num_empresas"] == 1
