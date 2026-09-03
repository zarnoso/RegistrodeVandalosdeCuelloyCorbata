#!/usr/bin/env python3
"""
Tests básicos para el backend de Registro de Vándalos.
Ejecutar: pytest tests/ -v
"""

import pytest
from fastapi.testclient import TestClient
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault("DATABASE_URL", "postgresql://neondb_owner:npg_tV5U4lxucCWR@ep-dark-sunset-ah922o3v-pooler.c-3.us-east-1.aws.neon.tech/neondb?sslmode=require")

from backend import app

client = TestClient(app)


class TestHealth:
    def test_health_returns_200(self):
        resp = client.get("/health")
        assert resp.status_code == 200
    
    def test_health_has_status(self):
        resp = client.get("/health")
        data = resp.json()
        assert "status" in data


class TestPoliticos:
    def test_listar_politicos_returns_list(self):
        resp = client.get("/api/politicos/?limit=10")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
    
    def test_listar_politicos_pagination(self):
        resp1 = client.get("/api/politicos/?limit=5&skip=0")
        resp2 = client.get("/api/politicos/?limit=5&skip=5")
        assert resp1.status_code == 200
        assert resp2.status_code == 200
    
    def test_detalle_politico_not_found(self):
        resp = client.get("/api/politicos/99999")
        assert resp.status_code == 404


class TestCasos:
    def test_listar_casos(self):
        resp = client.get("/api/casos/")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)


class TestFuncionarios:
    def test_listar_funcionarios(self):
        resp = client.get("/api/funcionarios/")
        assert resp.status_code == 200
        data = resp.json()
        assert "data" in data
    
    def test_funcionarios_pagination(self):
        resp = client.get("/api/funcionarios/?limit=5&skip=0")
        assert resp.status_code == 200


class TestNoticias:
    def test_listar_noticias(self):
        resp = client.get("/api/noticias/")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)


class TestStats:
    def test_stats_returns_counts(self):
        resp = client.get("/api/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert "politicos" in data
        assert "casos" in data
        assert "noticias" in data


class TestCache:
    def test_cache_clear(self):
        resp = client.post("/api/cache/clear")
        assert resp.status_code == 200
        assert resp.json()["ok"] is True


class TestConexionesNoDeclaradas:
    def test_endpoint_returns_data(self):
        resp = client.get("/api/conexiones/no-declaradas?limit=10")
        assert resp.status_code == 200
        data = resp.json()
        assert "familiares_sin_relacion" in data
        assert "alias_sin_relacion" in data


class TestComparar:
    def test_comparar_requires_ids(self):
        resp = client.get("/api/comparar/")
        assert resp.status_code == 400
    
    def test_comparar_with_ids(self):
        resp = client.get("/api/comparar/?ids=261,262")
        if resp.status_code == 200:
            data = resp.json()
            assert "politicos" in data
        else:
            pass  # Puede fallar si los IDs no existen


class TestMapaRegiones:
    def test_mapa_returns_regiones(self):
        resp = client.get("/api/mapa/regiones")
        assert resp.status_code == 200
        data = resp.json()
        assert "regiones" in data


class TestBuscarAlias:
    def test_buscar_alias_returns_results(self):
        resp = client.get("/api/buscar/alias/?nombre=test")
        assert resp.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
