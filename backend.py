"""
Backend adaptador para Registro de Vándalos
"""

import os
import re
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from typing import List, Optional
import psycopg2
import psycopg2.extras
from datetime import datetime

app = FastAPI(title="Registro de Vándalos API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://neondb_owner:npg_tV5U4lxucCWR@ep-dark-sunset-ah922o3v-pooler.c-3.us-east-1.aws.neon.tech/neondb?sslmode=require"
)

def get_db():
    return psycopg2.connect(DB_URL, sslmode='require', cursor_factory=psycopg2.extras.RealDictCursor)

@app.get("/")
def root():
    frontend_path = os.path.join(os.path.dirname(__file__), "frontend", "index.html")
    if os.path.exists(frontend_path):
        return FileResponse(frontend_path)
    return {"message": "Registro de Vándalos API"}

@app.get("/health")
def health():
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.close()
        conn.close()
        return {"status": "healthy", "database": "ok"}
    except Exception as e:
        return {"status": "unhealthy", "database": str(e)}

@app.get("/api/politicos/")
def listar_politicos(skip: int = 0, limit: int = 500, busqueda: str = None):
    conn = get_db()
    cur = conn.cursor()
    
    if busqueda:
        cur.execute("""
            SELECT DISTINCT p.id, p.nombre_completo, p.tipo, p.region
            FROM politicos p
            LEFT JOIN politicos_aliases pa ON p.id = pa.politico_id
            WHERE p.nombre_completo ILIKE %s OR pa.alias_nombre ILIKE %s
            ORDER BY p.nombre_completo
            LIMIT %s OFFSET %s
        """, (f"%{busqueda}%", f"%{busqueda}%", limit, skip))
    else:
        cur.execute("SELECT id, nombre_completo, tipo, region FROM politicos ORDER BY nombre_completo LIMIT %s OFFSET %s", (limit, skip))
    
    rows = cur.fetchall()
    
    resultado = []
    for r in rows:
        cur.execute("SELECT COUNT(*) as total FROM casos_corrupcion WHERE responsable ILIKE %s", (f"%{r['nombre_completo']}%",))
        casos_count = cur.fetchone()['total'] or 0
        
        if casos_count > 2:
            estado_riesgo = "alerta_roja"
        elif casos_count > 0:
            estado_riesgo = "alerta_naranja"
        else:
            estado_riesgo = "sin_registros"
        
        tipo = (r['tipo'] or "desconocido").lower()
        if "diputado" in tipo:
            cargo = "Diputado"
        elif "senador" in tipo:
            cargo = "Senador"
        elif "investigado" in tipo:
            cargo = "Investigado"
        else:
            cargo = tipo.capitalize()
        
        resultado.append({
            "id": r['id'],
            "nombre_completo": r['nombre_completo'] or "Sin nombre",
            "tipo": r['tipo'],
            "region": r['region'] or "Sin región",
            "institucion": "Congreso",
            "cargo": cargo,
            "partido": "Sin partido",
            "estado_riesgo": estado_riesgo,
            "num_eventos": casos_count,
            "num_empresas": 0,
            "num_familiares": 0,
            "eventos": [],
            "patrimonios": [],
            "fuente_url": None,
            "fecha_extraccion": None,
        })
    
    cur.close()
    conn.close()
    return resultado

@app.get("/api/politicos/grafo")
def grafo_relaciones(limit: int = 250):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, nombre_completo, tipo, region FROM politicos LIMIT %s", (limit,))
    nodos = [{"id": r['id'], "nombre": r['nombre_completo'], "tipo": r['tipo'], "region": r['region']} for r in cur.fetchall()]
    cur.execute("SELECT politico_origen_id, politico_destino_id, tipo_relacion FROM relaciones WHERE activo = true LIMIT 100")
    aristas = [{"origen": r['politico_origen_id'], "destino": r['politico_destino_id'], "tipo": r['tipo_relacion']} for r in cur.fetchall()]
    cur.close()
    conn.close()
    return {"nodos": nodos, "aristas": aristas}

@app.get("/api/politicos/analitica/som")
def som_data(limit: int = 500):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, nombre_completo, tipo, region FROM politicos ORDER BY nombre_completo LIMIT %s", (limit,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    puntos = []
    for r in rows:
        puntos.append({
            "id": int(r['id']),
            "nombre": str(r['nombre_completo'] or "Sin nombre"),
            "tipo": str(r['tipo'] or "desconocido"),
            "region": str(r['region'] or "Sin región"),
            "score_riesgo": 0.5,
            "total_casos": 0
        })
    return {"puntos": puntos}

@app.get("/api/casos/")
def listar_casos(skip: int = 0, limit: int = 100):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM casos_corrupcion ORDER BY created_at DESC LIMIT %s OFFSET %s", (limit, skip))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [dict(r) for r in rows]

@app.get("/api/stats")
def stats():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) as total FROM politicos")
    politicos = cur.fetchone()['total']
    cur.execute("SELECT COUNT(*) as total FROM casos_corrupcion")
    casos = cur.fetchone()['total']
    cur.execute("SELECT COUNT(*) as total FROM noticias")
    noticias = cur.fetchone()['total']
    cur.close()
    conn.close()
    return {"politicos": politicos, "casos": casos, "noticias": noticias}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8006)
