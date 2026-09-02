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

def calcular_riesgo_heredado(casos_propios, casos_familiares):
    """Punto 6: el entorno (familiares con casos) sube el score aunque
    el político no tenga antecedentes directos — visibiliza a quien 'pasa piola'."""
    score = casos_propios + 0.5 * casos_familiares
    if score > 2:
        return "alerta_roja"
    elif score > 0:
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

    # Un solo query con JOINs agregados — evita N+1 (antes: hasta 3 queries x 289 políticos)
    # Suma casos_familiares (punto 6: riesgo heredado del entorno)
    cur.execute("""
        SELECT
            p.id, p.nombre_completo, p.tipo, p.region, p.partido,
            COALESCE(cc.casos_count, 0) AS casos_count,
            COALESCE(fam.fam_count, 0) AS fam_count,
            COALESCE(pat.pat_count, 0) AS pat_count,
            COALESCE(fam_casos.casos_familiares, 0) AS casos_familiares
        FROM politicos p
        LEFT JOIN (
            SELECT responsable, COUNT(*) AS casos_count
            FROM casos_corrupcion
            GROUP BY responsable
        ) cc ON p.nombre_completo ILIKE '%%' || cc.responsable || '%%'
        LEFT JOIN (
            SELECT politico_id, COUNT(*) AS fam_count
            FROM familiares
            GROUP BY politico_id
        ) fam ON fam.politico_id = p.id
        LEFT JOIN (
            SELECT politico_id, COUNT(*) AS pat_count
            FROM patrimonio
            GROUP BY politico_id
        ) pat ON pat.politico_id = p.id
        LEFT JOIN (
            SELECT f.politico_id, COUNT(*) AS casos_familiares
            FROM familiares f
            JOIN casos_corrupcion cc2 ON cc2.responsable ILIKE '%%' || f.nombre_completo || '%%'
            GROUP BY f.politico_id
        ) fam_casos ON fam_casos.politico_id = p.id
        ORDER BY p.nombre_completo
        LIMIT %s OFFSET %s
    """, (limit, skip))

    rows = cur.fetchall()

    resultado = []
    for r in rows:
        casos_count = r['casos_count']
        casos_familiares = r['casos_familiares']
        estado_riesgo = calcular_riesgo_heredado(casos_count, casos_familiares)

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
            "partido": r['partido'] or "Sin partido",
            "estado_riesgo": estado_riesgo,
            "num_eventos": casos_count,
            "num_empresas": r['pat_count'],
            "num_familiares": r['fam_count'],
            "casos_familiares": casos_familiares,
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

    cur.execute("""
        SELECT p.id, p.nombre_completo, p.tipo, p.region,
               COALESCE(cc.casos_count, 0) AS casos_count
        FROM politicos p
        LEFT JOIN (
            SELECT responsable, COUNT(*) AS casos_count
            FROM casos_corrupcion
            GROUP BY responsable
        ) cc ON p.nombre_completo ILIKE '%%' || cc.responsable || '%%'
        LIMIT %s
    """, (limit,))
    politico_rows = cur.fetchall()

    nodes = [{
        "id": f"politico:{r['id']}",
        "tipo": "politico",
        "etiqueta": r['nombre_completo'],
        "metadata": {"region": r['region'], "estado": "condenado" if r['casos_count'] > 2 else ("abierto" if r['casos_count'] > 0 else "sin_estado")},
    } for r in politico_rows]
    politico_ids = [r['id'] for r in politico_rows]

    edges = []

    # Relaciones declaradas entre políticos (tabla relaciones — hoy vacía, listo para cuando se pueble)
    cur.execute("SELECT politico_origen_id, politico_destino_id, tipo_relacion FROM relaciones WHERE activo = true LIMIT 200")
    for r in cur.fetchall():
        edges.append({"origen": f"politico:{r['politico_origen_id']}", "destino": f"politico:{r['politico_destino_id']}", "tipo": r['tipo_relacion']})

    # Familiares como nodos propios + arista al político — dato que sí existe hoy
    if politico_ids:
        cur.execute("""
            SELECT id, politico_id, nombre_completo, parentesco
            FROM familiares
            WHERE politico_id = ANY(%s)
        """, (politico_ids,))
        for f in cur.fetchall():
            fam_node_id = f"familiar:{f['id']}"
            cur.execute("SELECT COUNT(*) AS total FROM casos_corrupcion WHERE responsable ILIKE %s", (f"%{f['nombre_completo']}%",))
            fam_casos = cur.fetchone()['total'] or 0
            nodes.append({
                "id": fam_node_id,
                "tipo": "familiar",
                "etiqueta": f['nombre_completo'],
                "metadata": {"parentesco": f['parentesco'], "estado": "condenado" if fam_casos > 2 else ("abierto" if fam_casos > 0 else "sin_estado")},
            })
            edges.append({"origen": f"politico:{f['politico_id']}", "destino": fam_node_id, "tipo": f['parentesco'] or "familiar"})

    cur.close()
    conn.close()
    return {"nodes": nodes, "edges": edges}

@app.get("/api/politicos/analitica/som")
def som(limit: int = 500):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT p.id, p.nombre_completo, p.tipo, p.region,
               COALESCE(cc.casos_count, 0) AS casos_count,
               COALESCE(fam.fam_count, 0) AS fam_count
        FROM politicos p
        LEFT JOIN (
            SELECT responsable, COUNT(*) AS casos_count
            FROM casos_corrupcion
            GROUP BY responsable
        ) cc ON p.nombre_completo ILIKE '%%' || cc.responsable || '%%'
        LEFT JOIN (
            SELECT politico_id, COUNT(*) AS fam_count
            FROM familiares
            GROUP BY politico_id
        ) fam ON fam.politico_id = p.id
        LIMIT %s
    """, (limit,))
    rows = cur.fetchall()
    max_casos = max((r['casos_count'] for r in rows), default=1) or 1
    max_fam = max((r['fam_count'] for r in rows), default=1) or 1
    items = []
    for r in rows:
        items.append({
            "politico_id": r['id'],
            "nombre": r['nombre_completo'],
            "tipo": r['tipo'],
            "region": r['region'],
            "score_riesgo": min(1.0, r['casos_count'] * 0.3),
            "total_casos": r['casos_count'],
            # normalized: features en [0,1] para el entrenamiento SOM del frontend
            "normalized": [r['casos_count'] / max_casos, r['fam_count'] / max_fam],
        })
    cur.close()
    conn.close()
    return {"items": items}

@app.get("/api/politicos/{politico_id}")
def detalle_politico(politico_id: int):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT id, nombre_completo, tipo, region, partido FROM politicos WHERE id = %s", (politico_id,))
    p = cur.fetchone()
    if not p:
        cur.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Político no encontrado")

    cur.execute("""
        SELECT caso_nombre, fecha_inicio, estado_actual, resumen, fuente
        FROM casos_corrupcion
        WHERE responsable ILIKE %s
        ORDER BY fecha_inicio DESC
    """, (f"%{p['nombre_completo']}%",))
    eventos = [dict(row) for row in cur.fetchall()]

    cur.execute("""
        SELECT nombre_completo, parentesco, fuente_url, notas
        FROM familiares
        WHERE politico_id = %s
    """, (politico_id,))
    familiares = [dict(row) for row in cur.fetchall()]

    # Punto 2/6: casos de corrupción de cada familiar — red cercana visible
    for f in familiares:
        cur.execute("""
            SELECT caso_nombre, fecha_inicio, estado_actual, resumen, fuente
            FROM casos_corrupcion
            WHERE responsable ILIKE %s
            ORDER BY fecha_inicio DESC
        """, (f"%{f['nombre_completo']}%",))
        f['casos'] = [dict(row) for row in cur.fetchall()]

    cur.execute("""
        SELECT alias_tipo, alias_nombre, fuente_url, verificado
        FROM politicos_aliases
        WHERE politico_id = %s
    """, (politico_id,))
    aliases = [dict(row) for row in cur.fetchall()]

    cur.execute("""
        SELECT *
        FROM patrimonio
        WHERE politico_id = %s
    """, (politico_id,))
    try:
        patrimonios = [dict(row) for row in cur.fetchall()]
    except Exception:
        patrimonios = []

    cur.close()
    conn.close()

    casos_count = len(eventos)
    casos_familiares = sum(len(f['casos']) for f in familiares)
    return {
        "id": p['id'],
        "nombre_completo": p['nombre_completo'],
        "tipo": p['tipo'],
        "region": p['region'] or "Sin región",
        "partido": p['partido'] or "Sin partido",
        "estado_riesgo": calcular_riesgo_heredado(casos_count, casos_familiares),
        "num_eventos": casos_count,
        "num_familiares": len(familiares),
        "num_empresas": len(patrimonios),
        "casos_familiares": casos_familiares,
        "eventos": eventos,
        "familiares": familiares,
        "aliases": aliases,
        "patrimonios": patrimonios,
    }

@app.get("/api/buscar/alias/")
def buscar_por_alias(nombre: str, tipo: str = None):
    """Punto 3: buscar por apodo/alias, no solo nombre legal (ej. el Tati)."""
    conn = get_db()
    cur = conn.cursor()

    if tipo:
        cur.execute("""
            SELECT pa.politico_id, pa.alias_tipo, pa.alias_nombre, pa.verificado,
                   p.nombre_completo, p.region, p.tipo AS cargo_tipo
            FROM politicos_aliases pa
            JOIN politicos p ON p.id = pa.politico_id
            WHERE pa.alias_nombre ILIKE %s AND pa.alias_tipo = %s
        """, (f"%{nombre}%", tipo))
    else:
        cur.execute("""
            SELECT pa.politico_id, pa.alias_tipo, pa.alias_nombre, pa.verificado,
                   p.nombre_completo, p.region, p.tipo AS cargo_tipo
            FROM politicos_aliases pa
            JOIN politicos p ON p.id = pa.politico_id
            WHERE pa.alias_nombre ILIKE %s
        """, (f"%{nombre}%",))

    resultado = [dict(row) for row in cur.fetchall()]
    cur.close()
    conn.close()
    return resultado

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
    cur.execute("SELECT COUNT(*) as total FROM funcionarios_gobierno")
    fun = cur.fetchone()['total']
    cur.close()
    conn.close()
    return {"politicos": p, "casos": c, "noticias": n, "relaciones": rel, "familiares": fam, "funcionarios": fun}

# =============================================================================
# PUNTO 4: Endpoints de Funcionarios de Gobierno
# =============================================================================
@app.get("/api/funcionarios/")
def listar_funcionarios(institucion: str = None, limit: int = 100, skip: int = 0):
    conn = get_db()
    cur = conn.cursor()
    
    # Total count
    cur.execute("SELECT COUNT(*) as total FROM funcionarios_gobierno")
    total_count = cur.fetchone()['total']
    
    # Query con filtro opcional
    if institucion:
        cur.execute("""
            SELECT * FROM funcionarios_gobierno
            WHERE institucion ILIKE %s
            ORDER BY nombre_completo
            LIMIT %s OFFSET %s
        """, (f"%{institucion}%", limit, skip))
    else:
        cur.execute("""
            SELECT * FROM funcionarios_gobierno
            ORDER BY nombre_completo
            LIMIT %s OFFSET %s
        """, (limit, skip))
    
    rows = cur.fetchall()
    cur.close()
    conn.close()
    
    return {
        "data": [dict(r) for r in rows],
        "total": total_count,
        "limit": limit,
        "skip": skip
    }

@app.get("/api/funcionarios/{funcionario_id}")
def detalle_funcionario(funcionario_id: int):
    conn = get_db()
    cur = conn.cursor()
    
    cur.execute("SELECT * FROM funcionarios_gobierno WHERE id = %s", (funcionario_id,))
    row = cur.fetchone()
    
    if not row:
        cur.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Funcionario no encontrado")
    
    result = dict(row)
    
    # Si el funcionario está vinculado a un político, incluir info de casos
    if row['politico_id']:
        cur.execute("SELECT * FROM casos_corrupcion WHERE politico_id = %s", (row['politico_id'],))
        result['casos_propios'] = [dict(c) for c in cur.fetchall()]
    else:
        result['casos_propios'] = []
    
    # Buscar casos por nombre del funcionario
    cur.execute("""
        SELECT caso_nombre, fecha_inicio, estado_actual, resumen, fuente
        FROM casos_corrupcion
        WHERE responsable ILIKE %s
    """, (f"%{row['nombre_completo']}%",))
    result['casos_menciones'] = [dict(c) for c in cur.fetchall()]
    
    # Casos de familiares (si está vinculado a político)
    result['familiares'] = []
    if row['politico_id']:
        cur.execute("""
            SELECT nombre_completo, parentesco, fuente_url
            FROM familiares
            WHERE politico_id = %s
        """, (row['politico_id'],))
        result['familiares'] = [dict(f) for f in cur.fetchall()]
    
    cur.close()
    conn.close()
    return result

@app.get("/api/funcionarios/instituciones/")
def lista_instituciones():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT DISTINCT institucion, COUNT(*) as total
        FROM funcionarios_gobierno
        GROUP BY institucion
        ORDER BY total DESC
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [{"institucion": r['institucion'], "total": r['total']} for r in rows]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8006)
