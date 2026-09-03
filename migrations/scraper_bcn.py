#!/usr/bin/env python3
"""
Scraper BCN (Biblioteca del Congreso Nacional) para senadores/diputados en ejercicio.
Puebla: foto_url (desde imagen de listado), periodo, nombre, apellido_paterno, apellido_materno, partido.
Fuente: https://www.bcn.cl/historiapolitica/resenas_parlamentarias/index.html?categ=en_ejercicio&filtros=2 (senadores) / 3 (diputados)
"""
import os
import re
import time
import urllib.request
import ssl

DB_URL = os.environ.get("DATABASE_URL")
if not DB_URL:
    raise RuntimeError("DATABASE_URL no configurada")

ctx = ssl.create_default_context()
UA = "Mozilla/5.0 (X11; Linux x86_64) RegistroVandalos/1.0"
BASE = "https://www.bcn.cl/historiapolitica/resenas_parlamentarias"


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    return urllib.request.urlopen(req, context=ctx, timeout=20).read().decode("utf-8")


def get_people(filtros):
    """Recorrer páginas (parametro `pagina`) y devolver {slug: (nombre, foto_url)}."""
    people = {}
    page = 1
    while True:
        url = f"{BASE}/index.html?categ=en_ejercicio&filtros={filtros}&pagina={page}&K=1#listado_parlamentarios"
        try:
            html = fetch(url)
        except Exception:
            break
        slugs = re.findall(r'resenas_parlamentarias/wiki/([^"\s<>]+)', html)
        imgs = re.findall(r'src="(getimagenbiografia/[^"]+)"', html)
        names = [re.sub("<[^>]+>", "", n).strip() for n in re.findall(r'<h5 itemprop="name">(.*?)</h5>', html)]
        if not slugs:
            break
        n = min(len(slugs), len(imgs), len(names))
        for i in range(n):
            people.setdefault(slugs[i], (names[i], imgs[i]))

        if re.search(r'pagina=%d' % (page + 1), html):
            page += 1
        else:
            break
        if page > 10:
            break
    return people


def absolutize(img):
    if img.startswith("http"):
        return img
    if img.startswith("getimagenbiografia"):
        return f"{BASE}/{img}"
    if img.startswith("/"):
        return f"https://www.bcn.cl{img}"
    return img


def parse_wiki(html):
    """Extraer el periodo parlamentario más reciente de una página wiki."""
    idx = html.find("Trayectoria Parlamentaria")
    if idx < 0:
        return ""
    seg = html[idx:idx + 4000]
    text = re.sub("<[^>]+>", " ", seg)
    text = re.sub(r"\s+", " ", text)
    per = re.findall(r'(Senador|Senadora|Diputado|Diputada)\s+(\d{4})\s*[-–]\s*(\d{4})', text)
    if per:
        return f"{per[0][1]}-{per[0][2]}"
    return ""


def split_name(nombre_completo):
    parts = nombre_completo.strip().split()
    if len(parts) == 1:
        return nombre_completo, "", ""
    if len(parts) == 2:
        return parts[0], parts[1], ""
    return " ".join(parts[:-2]), parts[-2], parts[-1]


def norm(s):
    """Normalizar: minúsculas y sin acentos."""
    import unicodedata
    s = s.lower()
    s = unicodedata.normalize("NFD", s)
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


def run():
    import psycopg2
    conn = psycopg2.connect(DB_URL, sslmode="require")
    cur = conn.cursor()

    senadores = get_people("2")
    diputados = get_people("3")
    all_people = {**senadores, **diputados}
    print(f"BCN: {len(senadores)} senadores, {len(diputados)} diputados, total {len(all_people)}")

    updated_foto = 0
    updated_periodo = 0
    updated_names = 0
    matched = 0

    # Índice por nombre normalizado (apellido paterno -> lista de (slug, nombre_bcn))
    by_apellido = {}
    for slug, (nombre_bcn, _img) in all_people.items():
        parts = norm(nombre_bcn).split()
        ap = parts[-1] if len(parts) >= 2 else ""
        by_apellido.setdefault(ap, []).append((slug, nombre_bcn))

    cur.execute("SELECT id, nombre_completo, tipo FROM politicos WHERE tipo IN ('senador','diputado')")
    db_rows = cur.fetchall()

    for pid, nombre_db, tipo in db_rows:
        db_parts = norm(nombre_db).split()
        ap = db_parts[-1] if len(db_parts) >= 2 else ""

        cands = by_apellido.get(ap, [])
        if not cands:
            continue

        # Elegir mejor candidato BCN
        best = None
        for slug, nombre_bcn in cands:
            b_parts = norm(nombre_bcn).split()
            # Coincidencia exacta normalizada
            if norm(nombre_bcn) == norm(nombre_db):
                best = (slug, nombre_bcn)
                break
            # Coincidencia por apellido paterno + materno
            if len(db_parts) >= 3 and len(b_parts) >= 3 and b_parts[-1] == ap and b_parts[-2] == db_parts[-2]:
                best = (slug, nombre_bcn)
                break
        if not best and len(cands) == 1:
            best = cands[0]

        if not best:
            continue

        matched += 1
        slug, nombre_bcn = best
        img = all_people[slug][1]
        foto = absolutize(img)

        updates = []
        params = []

        if foto:
            updates.append("foto_url = %s")
            params.append(foto)
            updated_foto += 1

        nb = nombre_bcn.strip()
        nom, ap1, ap2 = split_name(nb)
        cur.execute("SELECT nombre, apellido_paterno FROM politicos WHERE id=%s", (pid,))
        nrow = cur.fetchone()
        if nrow and (not nrow[0] or not nrow[1] or not nrow[0].strip()):
            updates.append("nombre = %s")
            params.append(nom)
            updates.append("apellido_paterno = %s")
            params.append(ap1)
            if ap2:
                updates.append("apellido_materno = %s")
                params.append(ap2)
            updated_names += 1

        # Periodo desde la página wiki
        try:
            import urllib.parse
            wiki_url = f"{BASE}/wiki/{urllib.parse.quote(slug)}"
            wiki_html = fetch(wiki_url)
            periodo = parse_wiki(wiki_html)
            if periodo:
                updates.append("periodo = %s")
                params.append(periodo)
                updated_periodo += 1
        except Exception:
            pass

        if updates:
            params.append(pid)
            cur.execute(f"UPDATE politicos SET {', '.join(updates)}, updated_at=NOW() WHERE id=%s", params)
            conn.commit()
        time.sleep(0.1)

    cur.close()
    conn.close()
    print(f"\n✅ Coincidencias BCN->DB: {matched}")
    print(f"✅ Fotos actualizadas: {updated_foto}")
    print(f"✅ Periodos actualizados: {updated_periodo}")
    print(f"✅ Nombres divididos: {updated_names}")


if __name__ == "__main__":
    run()
