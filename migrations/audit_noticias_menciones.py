"""Auditoría y reproceso de noticias_menciones con el matching corregido.

Contexto: el worker de noticias indexaba antes cada palabra del nombre por
separado (incluyendo apellidos comunes como González, Muñoz, Silva) y
aceptaba coincidencias de una sola palabra. Esto generó riesgo real de
falsos positivos en las 3,670 menciones ya guardadas: una noticia que
mencionara solo un apellido común, sin relación real con el político,
pudo haber quedado registrada como mención suya.

Este script:
1. Reconstruye qué política(s) matchean el contexto guardado de cada
   mención, usando la lógica nueva (mínimo nombre + apellido juntos).
2. Si el político registrado en la mención NO aparece entre los matches
   de la lógica nueva sobre su propio contexto guardado, la marca como
   sospechosa (columna `revisada = false` se deja intacta; se usa una
   columna nueva `valida_v2` para no destruir el dato original).
3. Modo por defecto: solo reporta (dry-run). Con --apply, además
   AGREGA la columna `valida_v2` si no existe y actualiza los valores,
   sin borrar ninguna fila — la decisión de ocultar/eliminar queda para
   una revisión manual posterior, filtrando por valida_v2 = false.

Uso:
    python3 migrations/audit_noticias_menciones.py            # solo reporta
    python3 migrations/audit_noticias_menciones.py --apply    # marca en BD
"""
import os
import re
import sys
import unicodedata
import psycopg2
import psycopg2.extras

DB_URL = os.environ["DATABASE_URL"]


def normalizar(s):
    if not s:
        return ""
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower().strip()
    return re.sub(r"\s+", " ", s)


def cargar_indice(cur):
    """Mismo criterio que worker_noticias.py: nombre completo + bigramas
    consecutivos, nunca una palabra sola."""
    cur.execute("SELECT id, nombre_completo FROM politicos WHERE LENGTH(nombre_completo) > 5")
    idx = {}
    for row in cur.fetchall():
        pid, nombre = row["id"], row["nombre_completo"]
        palabras = [p.lower().strip() for p in nombre.split() if len(p.strip()) >= 3]
        combinaciones = set()
        if len(palabras) >= 2:
            combinaciones.add(" ".join(palabras))
            for i in range(len(palabras) - 1):
                combinaciones.add(f"{palabras[i]} {palabras[i+1]}")
        for combo in combinaciones:
            idx.setdefault(combo, set()).add(pid)
    return idx


def matches_en_texto(texto, indice):
    txt = normalizar(texto)
    palabras = txt.split()
    max_lng = max((len(k.split()) for k in indice), default=2)
    encontrados = set()
    for lng in range(max_lng, 1, -1):
        for i in range(len(palabras) - lng + 1):
            ng = " ".join(palabras[i:i + lng])
            if ng in indice:
                encontrados |= indice[ng]
    return encontrados


def main():
    apply_changes = "--apply" in sys.argv

    conn = psycopg2.connect(DB_URL, sslmode="require", cursor_factory=psycopg2.extras.RealDictCursor)
    cur = conn.cursor()

    indice = cargar_indice(cur)
    print(f"Índice cargado: {len(indice)} combinaciones de nombre.")

    cur.execute("""
        SELECT nm.id, nm.politico_id, nm.contexto, p.nombre_completo
        FROM noticias_menciones nm
        JOIN politicos p ON p.id = nm.politico_id
    """)
    filas = cur.fetchall()
    print(f"Menciones a revisar: {len(filas)}")

    sospechosas, validas = [], []
    for f in filas:
        contexto = f["contexto"] or ""
        matches = matches_en_texto(contexto, indice)
        if f["politico_id"] in matches:
            validas.append(f["id"])
        else:
            sospechosas.append((f["id"], f["politico_id"], f["nombre_completo"], contexto[:120]))

    print(f"\nVálidas con la lógica nueva: {len(validas)}")
    print(f"Sospechosas (posible falso positivo, apellido suelto u otra causa): {len(sospechosas)}")

    if sospechosas:
        print("\nMuestra de sospechosas (hasta 20):")
        for mid, pid, nombre, ctx in sospechosas[:20]:
            print(f"  mención #{mid} -> político #{pid} ({nombre}): \"{ctx}...\"")

    if not apply_changes:
        print("\nModo dry-run (no se modificó la BD). Ejecuta con --apply para marcar en la tabla.")
        cur.close()
        conn.close()
        return

    cur.execute("""
        ALTER TABLE noticias_menciones
        ADD COLUMN IF NOT EXISTS valida_v2 BOOLEAN
    """)
    conn.commit()

    if validas:
        cur.execute("UPDATE noticias_menciones SET valida_v2 = true WHERE id = ANY(%s)", (validas,))
    if sospechosas:
        ids_sospechosas = [s[0] for s in sospechosas]
        cur.execute("UPDATE noticias_menciones SET valida_v2 = false WHERE id = ANY(%s)", (ids_sospechosas,))
    conn.commit()

    print(f"\nColumna valida_v2 actualizada: {len(validas)} true, {len(sospechosas)} false.")
    print("Revisa manualmente antes de decidir si eliminar las marcadas false:")
    print("  SELECT * FROM noticias_menciones WHERE valida_v2 = false;")

    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
