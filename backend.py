"""
Backend adaptador para Registro de Vándalos
Conecta los datos reales de Neon con el frontend de Codex
"""

import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional
import psycopg2
import psycopg2.extras
from datetime import datetime

app = FastAPI(title="Registro de Vándalos API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Conexión a Neon
DB_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://neondb_owner:npg_tV5U4lxucCWR@ep-dark-sunset-ah922o3v-pooler.c-3.us-east-1.aws.neon.tech/neondb?sslmode=require"
)

def get_db():
    return psycopg2.connect(DB_URL, sslmode='require', cursor_factory=psycopg2.extras.RealDictCursor)

# Modelos
class Politico(BaseModel):
    id: int
    nombre_completo: str
    nombre: Optional[str] = None
    apellido_paterno: Optional[str] = None
    apellido_materno: Optional[str] = None
    email: Optional[str] = None
    tipo: Optional[str] = None
    region: Optional[str] = None
    periodo: Optional[str] = None
    fuente: Optional[str] = None
    datos_json: Optional[dict] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    fuente_url: Optional[str] = None
    fecha_extraccion: Optional[str] = None
    fecha_verificacion: Optional[str] = None

class Noticia(BaseModel):
    id: int
    titulo: str
    url: Optional[str] = None
    fuente: Optional[str] = None
    fecha_publicacion: Optional[str] = None
    contenido: Optional[str] = None
    mencionados: Optional[list] = None
    tags: Optional[list] = None
    relevante: Optional[bool] = None
    fuente_url: Optional[str] = None
    fecha_extraccion: Optional[str] = None

class CasoCorrupcion(BaseModel):
    id: int
    nombre: str
    monto: Optional[str] = None
    año: Optional[str] = None
    responsable: Optional[str] = None
    sector: Optional[str] = None
    partido: Optional[str] = None
    año_inicio: Optional[str] = None
    año_fin: Optional[str] = None
    comuna: Optional[str] = None
    posición: Optional[str] = None
    delitos: Optional[str] = None
    estado: Optional[str] = None
    sentencia: Optional[str] = None
    condena: Optional[str] = None
    conclusión: Optional[str] = None
    fuentes: Optional[list] = None
    fuente_url: Optional[str] = None
    fecha_extraccion: Optional[str] = None

# Endpoints API

@app.get("/")
def root():
    frontend_path = os.path.join(os.path.dirname(__file__), "frontend", "index.html")
    if os.path.exists(frontend_path):
        return FileResponse(frontend_path)
    return {"message": "Registro de Vándalos API", "docs": "/docs"}

@app.get("/health")
def health():
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.close()
        conn.close()
        return {"status": "healthy", "database": "ok", "timestamp": datetime.now().isoformat()}
    except Exception as e:
        return {"status": "unhealthy", "database": str(e)}

# =============================================
# POLÍTICOS (orden: estáticas antes que dinámicas)
# =============================================

@app.get("/api/politicos/stats")
def stats_politicos():
    conn = get_db()
    cur = conn.cursor()
    
    cur.execute("SELECT COUNT(*) as total FROM politicos")
    total = cur.fetchone()['total']
    
    cur.execute("SELECT tipo, COUNT(*) as count FROM politicos GROUP BY tipo")
    por_tipo = {r['tipo']: r['count'] for r in cur.fetchall()}
    
    cur.execute("SELECT region, COUNT(*) as count FROM politicos WHERE region IS NOT NULL GROUP BY region")
    por_region = {r['region']: r['count'] for r in cur.fetchall()}
    
    cur.close()
    conn.close()
    
    return {
        "total": total,
        "por_tipo": por_tipo,
        "por_region": por_region
    }

@app.get("/api/politicos/buscar/{nombre}")
def buscar_por_nombre(nombre: str):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT * FROM politicos 
        WHERE nombre_completo ILIKE %s OR apellido_paterno ILIKE %s
        LIMIT 20
    """, (f"%{nombre}%", f"%{nombre}%"))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [dict(r) for r in rows]

@app.get("/api/politicos/grafo")
def grafo_relaciones():
    """Retorna nodos y aristas para el grafo de relaciones"""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, nombre_completo, tipo, region FROM politicos")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    
    nodos = []
    for r in rows:
        nodos.append({
            "id": int(r['id']),
            "nombre": str(r['nombre_completo'] or "Sin nombre"),
            "tipo": str(r['tipo'] or "desconocido"),
            "region": str(r['region'] or "Sin región")
        })
    
    return {"nodos": nodos, "aristas": []}

@app.get("/api/politicos/analitica/som")
def som_data():
    """Datos para el mapa SOM (Self-Organizing Map)"""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, nombre_completo, tipo, region FROM politicos ORDER BY nombre_completo")
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

@app.get("/api/politicos/", response_model=List[dict])
def listar_politicos(skip: int = 0, limit: int = 100):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, nombre_completo, nombre, apellido_paterno, apellido_materno,
               email, tipo, region, periodo, fuente, datos_json, created_at,
               updated_at, fuente_url, fecha_extraccion, fecha_verificacion
        FROM politicos ORDER BY nombre_completo LIMIT %s OFFSET %s
    """, (limit, skip))
    rows = cur.fetchall()
    
    # Contar casos - simplificado (sin relación directa por ID)
    # El campo 'responsable' tiene el nombre, pero no es confiable para join
    # Por ahora asumimos 0 casos, se puede mejorar después con tabla de relación
    casos_count = {}
    cur.close()
    conn.close()
    
    resultado = []
    for r in rows:
        tipo = (r['tipo'] or "desconocido").lower()
        num_eventos = casos_count.get(r['id'], 0)
        
        # Determinar estado de riesgo
        if num_eventos > 2:
            estado_riesgo = "alerta_roja"
        elif num_eventos > 0:
            estado_riesgo = "alerta_naranja"
        else:
            estado_riesgo = "sin_registros"
        
        # Mapear tipo a cargo
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
            "nombre": r['nombre'],
            "apellido_paterno": r['apellido_paterno'],
            "apellido_materno": r['apellido_materno'],
            "email": r['email'],
            "tipo": r['tipo'],
            "region": r['region'] or "Sin región",
            "periodo": r['periodo'],
            "fuente": r['fuente'],
            "institucion": "Congreso",  # Asignado por defecto
            "cargo": cargo,
            "partido": "Sin partido",  # No hay campo partido en la DB
            "estado_riesgo": estado_riesgo,
            "num_eventos": num_eventos,
            "num_empresas": 0,  # No hay tabla de empresas
            "num_familiares": 0,  # No hay tabla de familiares
            "eventos": [],  # Se cargan en la ficha individual
            "patrimonios": [],
            "datos_json": r['datos_json'],
            "fuente_url": r['fuente_url'],
            "fecha_extraccion": str(r['fecha_extraccion']) if r['fecha_extraccion'] else None,
        })
    
    return resultado

@app.get("/api/politicos/{politico_id}")
def detalle_politico(politico_id: int):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM politicos WHERE id = %s", (politico_id,))
    row = cur.fetchone()
    if not row:
        cur.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Político no encontrado")
    
    # Obtener casos del político
    cur.execute("SELECT * FROM casos_corrupcion WHERE responsable ILIKE %s", (f"%{row['nombre_completo']}%",))
    casos = [dict(c) for c in cur.fetchall()]
    
    cur.close()
    conn.close()
    
    resultado = {
        "id": row['id'],
        "nombre_completo": row['nombre_completo'] or "Sin nombre",
        "nombre": row['nombre'],
        "apellido_paterno": row['apellido_paterno'],
        "apellido_materno": row['apellido_materno'],
        "email": row['email'],
        "tipo": row['tipo'],
        "region": row['region'] or "Sin región",
        "periodo": row['periodo'],
        "fuente": row['fuente'],
        "institucion": "Congreso",
        "cargo": row['tipo'].capitalize() if row['tipo'] else "Cargo no informado",
        "partido": "Sin partido",
        "estado_riesgo": "alerta_roja" if len(casos) > 2 else ("alerta_naranja" if len(casos) > 0 else "sin_registros"),
        "num_eventos": len(casos),
        "num_empresas": 0,
        "num_familiares": 0,
        "eventos": casos,
        "patrimonios": [],
        "datos_json": row['datos_json'],
        "fuente_url": row['fuente_url'],
        "fecha_extraccion": str(row['fecha_extraccion']) if row['fecha_extraccion'] else None,
    }
    return resultado

@app.get("/api/casos/", response_model=List[dict])
def listar_casos(skip: int = 0, limit: int = 100):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT c.*, p.nombre_completo as politico_nombre
        FROM casos_corrupcion c
        LEFT JOIN politicos p ON c.responsable ILIKE '%%' || p.nombre_completo || '%%'
        ORDER BY c.created_at DESC LIMIT %s OFFSET %s
    """, (limit, skip))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [dict(r) for r in rows]

@app.get("/api/casos/{caso_id}")
def detalle_caso(caso_id: int):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM casos_corrupcion WHERE id = %s", (caso_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Caso no encontrado")
    return dict(row)

@app.get("/api/noticias/", response_model=List[dict])
def listar_noticias(skip: int = 0, limit: int = 100):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT * FROM noticias ORDER BY created_at DESC LIMIT %s OFFSET %s
    """, (limit, skip))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [dict(r) for r in rows]

# =============================================
# CASOS (orden: estáticas antes que dinámicas)
# =============================================

@app.get("/api/casos/", response_model=List[dict])
def listar_casos(skip: int = 0, limit: int = 100):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT * FROM casos_corrupcion ORDER BY created_at DESC LIMIT %s OFFSET %s
    """, (limit, skip))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [dict(r) for r in rows]

@app.get("/api/casos/{caso_id}")
def detalle_caso(caso_id: int):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM casos_corrupcion WHERE id = %s", (caso_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Caso no encontrado")
    return dict(row)

# =============================================
# NOTICIAS
# =============================================

@app.get("/api/noticias/", response_model=List[dict])
def listar_noticias(skip: int = 0, limit: int = 100):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT * FROM noticias ORDER BY created_at DESC LIMIT %s OFFSET %s
    """, (limit, skip))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [dict(r) for r in rows]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
