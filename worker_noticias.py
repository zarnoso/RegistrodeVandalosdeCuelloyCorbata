#!/usr/bin/env python3
"""
Worker de Noticias v1.2 — Registro de Vándalos de Cuello y Corbata

Fuentes: BioBioChile, Interferencia, TheClinic, El Mostrador, CIPER, El Líbero
"""

import os, re, time, signal, threading, traceback, hashlib, unicodedata
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from urllib.parse import urljoin

import requests, feedparser, psycopg2, psycopg2.extras
from psycopg2 import pool as pg_pool
from bs4 import BeautifulSoup

DB_URL = os.environ.get("DATABASE_URL", "postgresql://neondb_owner:npg_tV5U4lxucCWR@ep-dark-sunset-ah922o3v-pooler.c-3.us-east-1.aws.neon.tech/neondb?sslmode=require")
MAX_WORKERS = int(os.environ.get("NOTICIAS_MAX_WORKERS", "4"))
BATCH_SIZE = int(os.environ.get("NOTICIAS_BATCH_SIZE", "20"))
SCRAPE_TIMEOUT = int(os.environ.get("NOTICIAS_TIMEOUT", "15"))
MAX_ARTICULOS = int(os.environ.get("NOTICIOS_MAX_ARTICULOS", "50"))

FUENTES = {
    "biobiochile": {
        "nombre": "BioBioChile",
        "rss": "https://feeds.feedburner.com/radiobiobio/NNeJ",
        "base_url": "https://www.biobiochile.cl",
        "selector_contenido": ".contenido-noticia, .cuerpo, article, .entry-content",
    },
    "interferencia": {
        "nombre": "Interferencia",
        "rss": "https://interferencia.cl/rss.xml",
        "base_url": "https://interferencia.cl",
        "selector_contenido": ".contenido, .cuerpo, article, .entry-content",
    },
    "theclinic": {
        "nombre": "TheClinic",
        "rss": "https://www.theclinic.cl/feed/",
        "base_url": "https://www.theclinic.cl",
        "selector_contenido": ".contenido-noticia, .articulo, article",
    },
    "el_mostrador": {
        "nombre": "El Mostrador",
        "base_url": "https://www.elmostrador.cl",
        "scrapear_links": True,
        "base_links": [
            "https://www.elmostrador.cl/noticias/",
            "https://www.elmostrador.cl/reportajes/",
        ],
    },
    "ciper": {
        "nombre": "CIPER",
        "base_url": "https://www.ciper.cl",
        "scrapear_links": True,
        "base_links": [
            "https://www.ciper.cl/investigaciones/",
            "https://www.ciper.cl/noticias/",
            "https://www.ciper.cl/reportajes/",
        ],
    },
    "ellibero": {
        "nombre": "El Líbero",
        "base_url": "https://ellibero.cl",
        "wp_api": True,
        "wp_api_url": "https://ellibero.cl/wp-json/wp/v2/posts",
        "selector_contenido": ".contenido, .cuerpo, article",
    },
}

_pool = pg_pool.ThreadedConnectionPool(1, MAX_WORKERS + 2, DB_URL)
BUFFER_NOTICIAS, BUFFER_MENCIONES, BUFFER_LOCK = [], [], threading.Lock()
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
]

def get_conn(): return _pool.getconn()
def put_conn(c): _pool.putconn(c)

def ejecutar_con_reconexion(fn, *args, max_intentos=3, **kwargs):
    for i in range(max_intentos):
        conn = get_conn()
        try:
            r = fn(conn, *args, **kwargs)
            put_conn(conn)
            return r
        except (psycopg2.OperationalError, psycopg2.InterfaceError):
            try: conn.close()
            except: pass
            _pool.putconn(conn, close=True)
            time.sleep(2 * (i + 1))
    raise ConnectionError(f"No se pudo reconectar tras {max_intentos} intentos")

def get_ua(): return USER_AGENTS[int(time.time() * 1000) % len(USER_AGENTS)]

def _flush():
    global BUFFER_NOTICIAS, BUFFER_MENCIONES
    with BUFFER_LOCK:
        ns, ms = BUFFER_NOTICIAS[:], BUFFER_MENCIONES[:]
        BUFFER_NOTICIAS, BUFFER_MENCIONES = [], []
    if not ns: return
    def _ins(c):
        cur = c.cursor()
        for n in ns:
            cur.execute("""INSERT INTO noticias (titulo, contenido, fuente, fecha_publicacion, url, hash_contenido, created_at)
                VALUES (%s,%s,%s,%s,%s,%s,NOW()) ON CONFLICT (hash_contenido) DO NOTHING""",
                (n["titulo"], n["contenido"], n["fuente"], n["fecha"], n["url"], n["h"]))
        for m in ms:
            try:
                cur.execute("""INSERT INTO noticias_menciones (noticia_id, politico_id, tipo_mencion, contexto)
                    VALUES ((SELECT id FROM noticias WHERE hash_contenido=%s),%s,'nombre',%s) ON CONFLICT DO NOTHING""",
                    (m["h"], m["pid"], m["ctx"]))
            except: pass
        c.commit(); cur.close()
    try: ejecutar_con_reconexion(_ins); print(f"  💾 Batch: {len(ns)} noticias, {len(ms)} menciones")
    except Exception as e: print(f"  ❌ Error batch: {e}")

def guardar(titulo, contenido, fuente, url, fecha):
    global BUFFER_NOTICIAS, BUFFER_MENCIONES
    h = hashlib.md5(f"{titulo}{fuente}".encode()).hexdigest()
    with BUFFER_LOCK:
        BUFFER_NOTICIAS.append({"h": h, "titulo": titulo, "contenido": contenido, "fuente": fuente, "url": url, "fecha": fecha})
    if len(BUFFER_NOTICIAS) >= BATCH_SIZE: _flush()

def guardar_mencion(h, pid, ctx):
    global BUFFER_MENCIONES
    with BUFFER_LOCK: BUFFER_MENCIONES.append({"h": h, "pid": pid, "ctx": ctx})
    if len(BUFFER_MENCIONES) >= BATCH_SIZE: _flush()

def cargar_indice():
    conn = get_conn(); cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT id, nombre_completo FROM politicos WHERE LENGTH(nombre_completo) > 5")
    rows = cur.fetchall(); cur.close(); put_conn(conn)
    idx = {}
    for r in rows:
        for palabra in r["nombre_completo"].split():
            p = palabra.lower().strip()
            if len(p) < 3: continue
            idx.setdefault(p, set()).add((r["id"], r["nombre_completo"]))
    return idx

def normalizar(s):
    if not s: return ""
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower().strip()
    return re.sub(r"\s+", " ", s)

def detectar(texto, indice):
    if not texto: return []
    txt = normalizar(texto)
    palabras = txt.split()
    matches, vistos = [], set()
    for lng in [3, 2, 1]:
        for i in range(len(palabras) - lng + 1):
            ng = " ".join(palabras[i:i+lng])
            if ng in indice:
                for pid, nom in indice[ng]:
                    if pid not in vistos:
                        vistos.add(pid)
                        ini, fin = max(0, i-10), min(len(palabras), i+lng+10)
                        matches.append({"politico_id": pid, "nombre": nom, "contexto": " ".join(palabras[ini:fin])})
    return matches

def scrapear_estandar(fuente, headers=None):
    headers = headers or {"User-Agent": get_ua()}
    resp = requests.get(fuente["rss"], headers=headers, timeout=SCRAPE_TIMEOUT)
    if resp.status_code != 200: return []
    feed = feedparser.parse(resp.text)
    articulos = []
    for entry in feed.entries[:MAX_ARTICULOS]:
        titulo = getattr(entry, "title", "")
        if not titulo: continue
        articulos.append({
            "titulo": titulo, "url": getattr(entry, "link", ""),
            "fecha": getattr(entry, "published", ""),
            "contenido": getattr(entry, "summary", ""),
            "fuente": fuente["nombre"],
        })
    return articulos

def scrapear_links(fuente, headers=None):
    headers = headers or {"User-Agent": get_ua()}
    articulos = []
    for url_sec in fuente.get("base_links", []):
        try:
            resp = requests.get(url_sec, headers=headers, timeout=SCRAPE_TIMEOUT)
            if resp.status_code != 200: continue
            soup = BeautifulSoup(resp.text, "html.parser")
            for a in soup.find_all("a", href=True):
                href, title = a["href"], a.get_text(strip=True)
                if len(title) > 30 and ("/noticias/" in href or "/reportajes/" in href or "/investigacion/" in href):
                    if not href.startswith("http"): href = urljoin(fuente["base_url"], href)
                    articulos.append({"titulo": title[:200], "url": href, "fecha": "", "contenido": "", "fuente": fuente["nombre"]})
        except: continue
    vistos, unicos = set(), []
    for a in articulos:
        if a["url"] not in vistos and len(unicos) < MAX_ARTICULOS:
            vistos.add(a["url"]); unicos.append(a)
    return unicos

def scrapear_wp(fuente, headers=None):
    headers = headers or {}
    url = fuente.get("wp_api_url", "")
    if not url: return []
    try:
        resp = requests.get(url, headers=headers, params={"per_page": MAX_ARTICULOS}, timeout=SCRAPE_TIMEOUT)
        if resp.status_code != 200: return []
        posts = resp.json(); articulos = []
        for post in posts:
            titulo = re.sub(r"<[^>]+>", "", post.get("title", {}).get("rendered", "")).strip()
            contenido = re.sub(r"<[^>]+>", "", post.get("excerpt", {}).get("rendered", "")).strip()
            if titulo:
                articulos.append({
                    "titulo": titulo[:200], "url": post.get("link", ""),
                    "fecha": post.get("date", ""), "contenido": contenido[:2000],
                    "fuente": fuente["nombre"],
                })
        return articulos
    except: return []

def extraer_contenido(url, fuente):
    if not url: return ""
    try:
        resp = requests.get(url, headers={"User-Agent": get_ua()}, timeout=SCRAPE_TIMEOUT)
        if resp.status_code != 200: return ""
        soup = BeautifulSoup(resp.text, "html.parser")
        for sel in fuente.get("selector_contenido", "").split(","):
            el = soup.select_one(sel.strip())
            if el: return el.get_text(strip=True)[:5000]
    except: pass
    return ""

def procesar(articulo, fuente, indice):
    if not articulo["titulo"]: return None
    contenido = articulo["contenido"]
    if len(contenido) < 200 and articulo["url"]:
        c = extraer_contenido(articulo["url"], fuente)
        if c: contenido = c
    if not contenido: contenido = articulo["titulo"]
    menciones = detectar(f"{articulo['titulo']} {contenido}", indice)
    if not menciones: return None
    h = hashlib.md5(f"{articulo['titulo']}{articulo['fuente']}".encode()).hexdigest()
    fecha = None
    if articulo.get("fecha"):
        try:
            from dateutil.parser import parse as pd
            fecha = pd(articulo["fecha"]).date()
        except: fecha = datetime.now().date()
    guardar(articulo["titulo"], contenido[:5000], articulo["fuente"], articulo.get("url", ""), fecha)
    for m in menciones: guardar_mencion(h, m["politico_id"], m["contexto"])
    return {"titulo": articulo["titulo"], "n": len(menciones), "politicos": [m["nombre"] for m in menciones]}

def run():
    print("=" * 60)
    print("🗞️ WORKER DE NOTICIAS v1.2")
    print("=" * 60)
    
    print("📂 Cargando índice...")
    indice = cargar_indice()
    print(f"✅ {len(indice)} palabras indexadas\n")
    
    todos = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futures = {}
        for key, fuente in FUENTES.items():
            if fuente.get("wp_api"): futures[ex.submit(scrapear_wp, fuente, {})] = key
            elif fuente.get("scrapear_links"): futures[ex.submit(scrapear_links, fuente, {})] = key
            else: futures[ex.submit(scrapear_estandar, fuente, {})] = key
        for f in as_completed(futures):
            key = futures[f]
            try:
                arts = f.result()
                print(f"  ✅ {FUENTES[key]['nombre']}: {len(arts)}")
                for a in arts: a["_fuente"] = FUENTES[key]
                todos.extend(arts)
            except Exception as e: print(f"  ❌ Error {key}: {e}")
    
    print(f"\n📰 Total: {len(todos)} artículos")
    resultados = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futures = {ex.submit(procesar, a, a.pop("_fuente"), indice): a for a in todos}
        for f in as_completed(futures):
            try:
                r = f.result()
                if r: resultados.append(r)
            except: pass
    
    _flush()
    
    print("\n" + "=" * 60)
    print(f"📊 Procesados: {len(todos)} | Con menciones: {len(resultados)}")
    politicos = set()
    for r in resultados: politicos.update(r["politicos"])
    print(f"👤 Políticos: {len(politicos)}")
    return len(resultados)

if __name__ == "__main__":
    try: run()
    except Exception as e: print(f"❌ {e}"); traceback.print_exc()
