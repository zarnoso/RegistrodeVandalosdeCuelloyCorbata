"""
Backend adaptador para Registro de Vándalos
Conecta los datos reales de Neon con el frontend de Codex
Incluye: aliases, relaciones, noticias, grafo de relaciones
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

# ===========================
# ENDPOINTS PRINCIPALES
# ===========================

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

# ===========================
# POLÍTICOS
# ===========================

@app.get("/api/politicos/")
def listar_politicos(skip: int = 0, limit: int = 100, busqueda: str = None):
    conn = get_db()
    cur = conn.cursor()
    
    if busqueda:
        cur.execute("""
            SELECT DISTINCT p.id, p.nombre_completo, p.tipo, p.region
            FROM politicos p
            LEFT JOIN politicos_aliases pa ON p.id = pa.politico_id
            LEFT JOIN relaciones r ON p.id = r.politico_origen_id OR p.id = r.politico_destino_id
            LEFT JOIN politicos p2 ON r.politico_destino_id = p2.id OR r.politico_origen_id = p2.id
            WHERE p.nombre_completo ILIKE %s
               OR pa.alias_nombre ILIKE %s
               OR p2.nombre_completo ILIKE %s
            ORDER BY p.nombre_completo
            LIMIT %s OFFSET %s
        """, (f"%{busqueda}%", f"%{busqueda}%", f"%{busqueda}%", limit, skip))
    else:
        cur.execute("""
            SELECT id, nombre_completo, tipo, region
            FROM politicos
            ORDER BY nombre_completo
            LIMIT %s OFFSET %s
        """, (limit, skip))
    
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [dict(r) for r in rows]

@app.get("/api/politicos/{politico_id}")
def detalle_politico(politico_id: int):
    conn = get_db()
    cur = conn.cursor()
    
    # Datos del político
    cur.execute("SELECT * FROM politicos WHERE id = %s", (politico_id,))
    row = cur.fetchone()
    if not row:
        cur.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Político no encontrado")
    
    # Aliases
    cur.execute("SELECT * FROM politicos_aliases WHERE politico_id = %s", (politico_id,))
    aliases = [dict(a) for a in cur.fetchall()]
    
    # Relaciones
    cur.execute("""
        SELECT r.*, 
               CASE WHEN r.politico_origen_id = %s THEN p2.nombre_completo ELSE p1.nombre_completo END as relacionado_nombre
        FROM relaciones r
        JOIN politicos p1 ON r.politico_origen_id = p1.id
        JOIN politicos p2 ON r.politico_destino_id = p2.id
        WHERE r.politico_origen_id = %s OR r.politico_destino_id = %s
    """, (politico_id, politico_id, politico_id))
    relaciones = [dict(r) for r in cur.fetchall()]
    
    # Casos
    cur.execute("SELECT * FROM casos_corrupcion WHERE responsable ILIKE %s", (f"%{row['nombre_completo']}%",))
    casos = [dict(c) for c in cur.fetchall()]
    
    # Noticias donde se menciona
    cur.execute("""
        SELECT n.* 
        FROM noticias n
        JOIN noticias_menciones nm ON n.id = nm.noticia_id
        WHERE nm.politico_id = %s
        ORDER BY n.fecha_publicacion DESC
        LIMIT 10
    """, (politico_id,))
    noticias = [dict(n) for n in cur.fetchall()]
    
    cur.close()
    conn.close()
    
    return {
        **dict(row),
        "aliases": aliases,
        "relaciones": relaciones,
        "casos": casos,
        "noticias": noticias,
        "estado_riesgo": "alerta_roja" if len(casos) > 2 else ("alerta_naranja" if len(casos) > 0 else "sin_registros")
    }

# ===========================
# ALIASES (amigo de, hermano de, etc.)
# ===========================

@app.get("/api/buscar/alias/")
def buscar_por_alias(tipo: str = None, nombre: str = None):
    conn = get_db()
    cur = conn.cursor()
    
    if not tipo or not nombre:
        cur.close()
        conn.close()
        return {"error": "Parámetros 'tipo' y 'nombre' son requeridos"}
    
    cur.execute("""
        SELECT p.id, p.nombre_completo, p.tipo, p.region, pa.alias_tipo, pa.alias_nombre
        FROM politicos p
        JOIN politicos_aliases pa ON p.id = pa.politico_id
        WHERE pa.alias_tipo = %s AND pa.alias_nombre ILIKE %s
    """, (tipo, f"%{nombre}%"))
    
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [dict(r) for r in rows]

# ===========================
# RELACIONES (grafo)
# ===========================

@app.get("/api/relaciones/")
def listar_relaciones(politico_id: int = None):
    conn = get_db()
    cur = conn.cursor()
    
    if politico_id:
        cur.execute("""
            SELECT r.*, 
                   p1.nombre_completo as origen_nombre,
                   p2.nombre_completo as destino_nombre
            FROM relaciones r
            JOIN politicos p1 ON r.politico_origen_id = p1.id
            JOIN politicos p2 ON r.politico_destino_id = p2.id
            WHERE r.politico_origen_id = %s OR r.politico_destino_id = %s
        """, (politico_id, politico_id))
    else:
        cur.execute("""
            SELECT r.*, 
                   p1.nombre_completo as origen_nombre,
                   p2.nombre_completo as destino_nombre
            FROM relaciones r
            JOIN politicos p1 ON r.politico_origen_id = p1.id
            JOIN politicos p2 ON r.politico_destino_id = p2.id
            LIMIT 100
        """)
    
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [dict(r) for r in rows]

@app.get("/api/grafo/")
def grafo_relaciones():
    conn = get_db()
    cur = conn.cursor()
    
    # Nodos: políticos
    cur.execute("SELECT id, nombre_completo, tipo, region FROM politicos")
    nodos = [{"id": r['id'], "nombre": r['nombre_completo'], "tipo": r['tipo'], "region": r['region']} for r in cur.fetchall()]
    
    # Aristas: relaciones
    cur.execute("""
        SELECT politico_origen_id, politico_destino_id, tipo_relacion
        FROM relaciones
        WHERE activo = true
    """)
    aristas = [{"origen": r['politico_origen_id'], "destino": r['politico_destino_id'], "tipo": r['tipo_relacion']} for r in cur.fetchall()]
    
    cur.close()
    conn.close()
    
    return {"nodos": nodos, "aristas": aristas}

# ===========================
# CASOS DE CORRUPCIÓN
# ===========================

@app.get("/api/casos/")
def listar_casos(skip: int = 0, limit: int = 100):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM casos_corrupcion ORDER BY created_at DESC LIMIT %s OFFSET %s", (limit, skip))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [dict(r) for r in rows]

# ===========================
# NOTICIAS
# ===========================

@app.get("/api/noticias/")
def listar_noticias(skip: int = 0, limit: int = 100, busqueda: str = None):
    conn = get_db()
    cur = conn.cursor()
    
    if busqueda:
        cur.execute("""
            SELECT DISTINCT n.* 
            FROM noticias n
            LEFT JOIN noticias_menciones nm ON n.id = nm.noticia_id
            LEFT JOIN politicos p ON nm.politico_id = p.id
            WHERE n.titulo ILIKE %s
               OR n.contenido ILIKE %s
               OR p.nombre_completo ILIKE %s
            ORDER BY n.created_at DESC
            LIMIT %s OFFSET %s
        """, (f"%{busqueda}%", f"%{busqueda}%", f"%{busqueda}%", limit, skip))
    else:
        cur.execute("SELECT * FROM noticias ORDER BY created_at DESC LIMIT %s OFFSET %s", (limit, skip))
    
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [dict(r) for r in rows]

@app.get("/api/noticias/{noticia_id}")
def detalle_noticia(noticia_id: int):
    conn = get_db()
    cur = conn.cursor()
    
    cur.execute("SELECT * FROM noticias WHERE id = %s", (noticia_id,))
    row = cur.fetchone()
    if not row:
        cur.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Noticia no encontrada")
    
    # Menciones en esta noticia
    cur.execute("""
        SELECT nm.*, p.nombre_completo
        FROM noticias_menciones nm
        JOIN politicos p ON nm.politico_id = p.id
        WHERE nm.noticia_id = %s
    """, (noticia_id,))
    menciones = [dict(m) for m in cur.fetchall()]
    
    cur.close()
    conn.close()
    
    return {**dict(row), "menciones": menciones}

# ===========================
# EXTRACCIÓN DE ENTIDADES (NLP simple)
# ===========================

def extraer_entidades(texto: str) -> List[dict]:
    """Extrae menciones de políticos y relaciones de un texto"""
    if not texto:
        return []
    
    conn = get_db()
    cur = conn.cursor()
    
    entidades = []
    
    # Patrones de búsqueda: "X, hermano de Y", "X, amigo de Y", etc.
    patrones = [
        (r'(\w+(?:\s+\w+){0,3})\s*,\s*(?:hermano|hermana)\s+de\s+(\w+(?:\s+\w+){0,3})', 'familiar'),
        (r'(\w+(?:\s+\w+){0,3})\s*,\s*(?:amigo|amiga)\s+de\s+(\w+(?:\s+\w+){0,3})', 'amistad'),
        (r'(\w+(?:\s+\w+){0,3})\s*,\s*(?:socio|socia)\s+de\s+(\w+(?:\s+\w+){0,3})', 'negocios'),
        (r'(\w+(?:\s+\w+){0,3})\s*,\s*(?:pareja|esposo|esposa)\s+de\s+(\w+(?:\s+\w+){0,3})', 'pareja'),
    ]
    
    for patron, tipo in patrones:
        matches = re.finditer(patron, texto, re.IGNORECASE)
        for match in matches:
            entidades.append({
                "texto_original": match.group(0),
                "persona_1": match.group(1).strip(),
                "persona_2": match.group(2).strip(),
                "tipo_relacion": tipo,
                "posicion": match.span()
            })
    
    cur.close()
    conn.close()
    
    return entidades

@app.get("/api/extraer-entidades/")
def api_extraer_entidades(texto: str):
    """Extrae entidades de un texto"""
    if not texto:
        return {"error": "Parámetro 'texto' requerido"}
    return {"entidades": extraer_entidades(texto)}

# ===========================
# ESTADÍSTICAS
# ===========================

@app.get("/api/stats")
def stats():
    conn = get_db()
    cur = conn.cursor()
    
    stats = {}
    
    cur.execute("SELECT COUNT(*) as total FROM politicos")
    stats["politicos"] = cur.fetchone()['total']
    
    cur.execute("SELECT COUNT(*) as total FROM casos_corrupcion")
    stats["casos"] = cur.fetchone()['total']
    
    cur.execute("SELECT COUNT(*) as total FROM noticias")
    stats["noticias"] = cur.fetchone()['total']
    
    cur.execute("SELECT COUNT(*) as total FROM relaciones")
    stats["relaciones"] = cur.fetchone()['total']
    
    cur.execute("SELECT COUNT(*) as total FROM politicos_aliases")
    stats["aliases"] = cur.fetchone()['total']
    
    cur.execute("SELECT COUNT(*) as total FROM familiares")
    stats["familiares"] = cur.fetchone()['total']
    
    # Por tipo
    cur.execute("SELECT tipo, COUNT(*) as count FROM politicos GROUP BY tipo")
    stats["por_tipo"] = {r['tipo']: r['count'] for r in cur.fetchall()}
    
    # Por tipo de relación
    cur.execute("SELECT tipo_relacion, COUNT(*) as count FROM relaciones GROUP BY tipo_relacion")
    stats["por_relacion"] = {r['tipo_relacion']: r['count'] for r in cur.fetchall()}
    
    cur.close()
    conn.close()
    
    return stats

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8006)
