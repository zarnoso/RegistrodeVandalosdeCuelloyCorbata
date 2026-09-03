#!/usr/bin/env python3
"""
Batch-fetches Wikipedia thumbnails for politicians.
Uses Wikipedia API search to find articles, then extracts thumbnail.
"""
import os
import json
import urllib.request
import urllib.parse
import ssl
import time

DB_URL = os.environ.get("DATABASE_URL")
ctx = ssl.create_default_context()
UA = "RegistroVandalos/1.0 (https://registrodevandalos.likay.cl)"


def wiki_thumbnail(nombre):
    """Search Wikipedia and return thumbnail URL if found."""
    try:
        # Try direct page lookup first
        encoded = urllib.parse.quote(nombre.replace(" ", "_"))
        url = f"https://es.wikipedia.org/api/rest_v1/page/summary/{encoded}"
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, context=ctx, timeout=8) as resp:
            data = json.loads(resp.read())
            thumb = data.get("thumbnail", {}).get("source")
            if thumb and "svg" not in thumb.lower():
                return thumb
    except Exception:
        pass

    try:
        # Fallback: search API
        search_url = f"https://es.wikipedia.org/w/api.php?action=query&list=search&srsearch={urllib.parse.quote(nombre)}&format=json&srlimit=1"
        req = urllib.request.Request(search_url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, context=ctx, timeout=8) as resp:
            data = json.loads(resp.read())
            results = data.get("query", {}).get("search", [])
            if results:
                title = results[0]["title"]
                page_url = f"https://es.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(title)}"
                req2 = urllib.request.Request(page_url, headers={"User-Agent": UA})
                with urllib.request.urlopen(req2, context=ctx, timeout=8) as resp2:
                    data2 = json.loads(resp2.read())
                    thumb = data2.get("thumbnail", {}).get("source")
                    if thumb and "svg" not in thumb.lower():
                        return thumb
    except Exception:
        pass

    return None


def run():
    import psycopg2
    conn = psycopg2.connect(DB_URL, sslmode="require")
    cur = conn.cursor()

    # Prioritize senators and diputados first, then others
    cur.execute("""
        SELECT id, nombre_completo, tipo 
        FROM politicos 
        WHERE foto_url IS NULL 
        ORDER BY 
            CASE tipo WHEN 'senador' THEN 1 WHEN 'diputado' THEN 2 
                      WHEN 'ex_senador' THEN 3 WHEN 'ex_diputado' THEN 4 
                      WHEN 'ministro' THEN 5 WHEN 'ex_ministro' THEN 6
                      ELSE 7 END,
            nombre_completo
    """)
    rows = cur.fetchall()
    print(f"Procesando {len(rows)} políticos sin foto...")

    found = 0
    for i, (pid, nombre, tipo) in enumerate(rows):
        photo = wiki_thumbnail(nombre)
        if photo:
            cur.execute("UPDATE politicos SET foto_url = %s WHERE id = %s", (photo, pid))
            found += 1
            if tipo in ("senador", "diputado"):
                print(f"  ✓ {nombre} ({tipo})")
        else:
            if tipo in ("senador", "diputado"):
                print(f"  ✗ {nombre} ({tipo}) — sin foto")

        if (i + 1) % 10 == 0:
            conn.commit()
            print(f"  ...{i+1}/{len(rows)} procesados ({found} fotos)")

        time.sleep(0.25)

    conn.commit()
    cur.close()
    conn.close()
    print(f"\n✅ Total fotos: {found}/{len(rows)}")


if __name__ == "__main__":
    run()
