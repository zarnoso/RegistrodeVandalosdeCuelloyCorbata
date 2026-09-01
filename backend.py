"""
Backend Registro de Vándalos v3
"""
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import psycopg2
import psycopg2.extras
import json

app = FastAPI(title="Registro de Vándalos API v3")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_URL = os.environ.get("DATABASE_URL")
if not DB_URL:
    raise RuntimeError("DATABASE_URL no configurada")

def get_db():
    return psycopg2.connect(DB_URL, sslmode='require', cursor_factory=psycopg2.extras.RealDictCursor)

def calcular_riesgo(casos_count):
    if casos_count > 2:
        return "alerta_roja"
    elif casos_count > 0:
        return "alerta_naranja"
    return "sin_registros"

@app.get("/")
def root():
    frontend_path = os.path.join(os.path.dirname(__file__), "frontend", "index.html")
    if os.path.exists(frontend_path):
        return FileResponse(frontend_path)
    return {"message": "API OK"}

@app.get("/health")
def health():
    try:
        conn = get_db()
        conn.close()
        return {"status": "healthy"}
    except:
        return {"status": "unhealthy"}

@app.get("/api/politicos/")
def listar_politicos(limit: int = 500, skip: int = 0):
    conn = get_db()
    cur = conn.cursor()
    
    # Consulta simple sin JOIN problemático
    cur.execute("""
        SELECT id, nombre_completo, tipo, region
        FROM politicos
        ORDER BY nombre_completo
        LIMIT %s OFFSET %s
    """, (limit, skip))
    
    rows = cur.fetchall()
    
    resultado = []
    for r in rows:
        # Contar casos por separado
        cur.execute("""
            SELECT COUNT(*) as total 
            FROM casos_corrupcion 
            WHERE responsable ILIKE %s
        """, (f"%{r['nombre_completo']}%",))
        casos_count = cur.fetchone()['total'] or 0
        
        # Contar familiares
        cur.execute("SELECT COUNT(*) as total FROM familiares WHERE politico_id = %s", (r['id'],))
        fam_count = cur.fetchone()['total'] or 0
        
        # Contar patrimonio
        cur.execute("SELECT COUNT(*) as total FROM patrimonio WHERE politico_id = %s", (r['id'],))
        pat_count = cur.fetchone()['total'] or 0
        
        # Determinar estado de riesgo
        estado_riesgo = calcular_riesgo(casos_count)
        
        # Mapear tipo a cargo
        tipo = (r['tipo'] or "").lower()
        if "diputado" in tipo:
            cargo = "Diputado"
        elif "senador" in tipo:
            cargo = "Senador"
        elif "investigado" in tipo:
            cargo = "Investigado"
        else:
            cargo = tipo.capitalize() if tipo else "Otro"
        
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
            "num_empresas": pat_count,
            "num_familiares": fam_count,
            "eventos": [],
            "patrimonios": [],
        })
    
    cur.close()
    conn.close()
    return resultado

@app.get("/api/politicos/grafo")
def grafo(limit: int = 250):
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
def som(limit: int = 500):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, nombre_completo, tipo, region FROM politicos LIMIT %s", (limit,))
    rows = cur.fetchall()
    puntos = []
    for r in rows:
        cur.execute("SELECT COUNT(*) as total FROM casos_corrupcion WHERE responsable ILIKE %s", (f"%{r['nombre_completo']}%",))
        casos = cur.fetchone()['total'] or 0
        puntos.append({
            "id": r['id'],
            "nombre": r['nombre_completo'],
            "tipo": r['tipo'],
            "region": r['region'],
            "score_riesgo": min(1.0, casos * 0.3),
            "total_casos": casos
        })
    cur.close()
    conn.close()
    return {"puntos": puntos}

@app.get("/api/casos/")
def casos(limit: int = 100, skip: int = 0):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM casos_corrupcion ORDER BY created_at DESC LIMIT %s OFFSET %s", (limit, skip))
    rows = [dict(r) for r in cur.fetchall()]
    cur.close()
    conn.close()
    return rows

@app.get("/api/stats")
def stats():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) as total FROM politicos")
    p = cur.fetchone()['total']
    cur.execute("SELECT COUNT(*) as total FROM casos_corrupcion")
    c = cur.fetchone()['total']
    cur.execute("SELECT COUNT(*) as total FROM noticias")
    n = cur.fetchone()['total']
    cur.execute("SELECT COUNT(*) as total FROM relaciones")
    rel = cur.fetchone()['total']
    cur.execute("SELECT COUNT(*) as total FROM familiares")
    fam = cur.fetchone()['total']
    cur.close()
    conn.close()
    return {"politicos": p, "casos": c, "noticias": n, "relaciones": rel, "familiares": fam}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8006)
