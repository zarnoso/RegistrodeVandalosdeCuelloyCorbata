"""Backfill relational linkage for the v3 schema.

1. casos_corrupcion.politico_id  <- best single match from responsable by name
2. noticias_menciones            <- from noticias.mencionados[].nombre matched to politicos
Note: queries already Count casos via responsable ILIKE (multi-politico aware).
This backfill populates the FK columns for grafo/som robustness and keeps
menciones in the normalized table.
"""
import os
import re
import psycopg2

DB_URL = os.environ["DATABASE_URL"]

def norm(s):
    return re.sub(r"[^a-z0-9 ]", "", (s or "").lower()).strip()


def main():
    conn = psycopg2.connect(DB_URL, sslmode="require")
    conn.autocommit = False
    cur = conn.cursor()

    cur.execute("SELECT id, nombre_completo FROM politicos")
    politicos = cur.fetchall()
    # build lookup by normalized full name
    by_norm = {}
    for pid, name in politicos:
        by_norm.setdefault(norm(name), []).append((pid, name))
    # also index by normalized first token + last token to catch name variations
    by_firstlast = {}
    for pid, name in politicos:
        parts = norm(name).split()
        if len(parts) >= 2:
            by_firstlast.setdefault((parts[0], parts[-1]), []).append((pid, name))

    # index by each position-prefix of the normalized name, e.g. "luis hermosilla" -> politico
    by_prefix = {}
    for pid, name in politicos:
        parts = norm(name).split()
        if len(parts) >= 2:
            for i in range(1, len(parts)):
                by_prefix.setdefault(tuple(parts[:i]), []).append((pid, name))

    def resolve(raw):
        n = norm(raw)
        if n in by_norm:
            return by_norm[n][0][0]
        parts = n.split()
        if len(parts) >= 2:
            cand = by_firstlast.get((parts[0], parts[-1]))
            if cand and len(cand) == 1:
                return cand[0][0]
            # prefix match: queried name is the leading tokens of a politico full name
            pref = by_prefix.get(tuple(parts))
            if pref and len(pref) == 1:
                return pref[0][0]
            # candidate list may be >1; prefer exact name-length match is ambiguous, skip
        return None

    # 1) casos_corrupcion.politico_id
    cur.execute("SELECT id, responsable FROM casos_corrupcion")
    casos = cur.fetchall()
    linked = 0
    no_match = []
    for cid, responsable in casos:
        pid = None
        if responsable:
            for name in re.split(r"[,\n;]", responsable):
                name = name.strip()
                if not name:
                    continue
                pid = resolve(name)
                if pid:
                    break
        if pid:
            cur.execute("UPDATE casos_corrupcion SET politico_id=%s WHERE id=%s", (pid, cid))
            linked += 1
        else:
            no_match.append((cid, responsable))

    # 2) noticias_menciones from noticias.mencionados[].nombre
    cur.execute("""
        SELECT id, mencionados, titulo FROM noticias
        WHERE mencionados IS NOT NULL AND jsonb_array_length(mencionados) > 0
    """)
    noticias = cur.fetchall()
    menciones = 0
    for nid, mencionados, titulo in noticias:
        for m in mencionados:
            name = m.get("nombre") if isinstance(m, dict) else m
            if not name:
                continue
            for part in re.split(r"[,\n;/]", name):
                part = part.strip()
                if not part:
                    continue
                pid = resolve(part)
                if pid:
                    cur.execute(
                        "SELECT 1 FROM noticias_menciones WHERE noticia_id=%s AND politico_id=%s",
                        (nid, pid),
                    )
                    if cur.fetchone():
                        continue
                    cur.execute(
                        "INSERT INTO noticias_menciones (noticia_id, politico_id, tipo_mencion, contexto) "
                        "VALUES (%s, %s, 'nombre', %s)",
                        (nid, pid, titulo),
                    )
                    menciones += 1

    conn.commit()
    print(f"casos totales: {len(casos)} | con politico_id: {linked} | sin match: {len(no_match)}")
    print(f"noticias_menciones insertadas: {menciones}")
    if no_match:
        print("Casos sin match (muestra):")
        for cid, resp in no_match[:15]:
            print("  id", cid, "->", repr(resp))
    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
