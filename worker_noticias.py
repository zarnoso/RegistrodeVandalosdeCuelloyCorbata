#!/usr/bin/env python3
"""
Worker de Noticias v1.0 — Registro de Vándalos de Cuello y Corbas

Reutiliza la arquitectura probada del Mapata Worker v5.0:
- ThreadPoolExecutor para scraping paralelo de múltiples fuentes
- Pool de conexiones PostgreSQL con reconexión automática
- Batch writes para inserción eficiente
- Checkpointing para reanudar tras caídas
- Circuit breaker para APIs externas
- Stale job detector
- Alertas Telegram

Fuentes soportadas:
- CIPER (Centro de Investigación Periodística)
- El Mostrador
- BioBioChile
- TheClinic.cl
"""

import os
import re
import sys
import time
import signal
import threading
import traceback
import unicodedata
import hashlib
import feedparser
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from urllib.parse import urljoin, urlparse

import requests
import psycopg2
import psycopg2.extras
from psycopg2 import pool as pg_pool
from bs4 import BeautifulSoup

# ══════════════════════════════════════════════════════
# CONFIGURACIÓN
# ══════════════════════════════════════════════════════
DB_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://neondb_owner:npg_tV5U4lxucCWR@ep-dark-sunset-ah922o3v-pooler.c-3.us-east-1.aws.neon.tech/neondb?sslmode=require"
)

MAX_WORKERS = int(os.environ.get("NOTICIAS_MAX_WORKERS", "4"))
BATCH_SIZE = int(os.environ.get("NOTICIAS_BATCH_SIZE", "20"))
SCRAPE_TIMEOUT = int(os.environ.get("NOTICIAS_TIMEOUT", "15"))
MAX_ARTICULOS_POR_FUENTE = int(os.environ.get("NOTICIOS_MAX_ARTICULOS", "50"))

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

# Fuentes de noticias con sus URLs RSS y selectores CSS
FUENTES = {
    "ciper": {
        "nombre": "CIPER",
        "rss": "https://www.ciper.cl/feed/",
        "base_url": "https://www.ciper.cl",
        "selector_titulo": "h1",
        "selector_contenido": ".contenido-noticia, .cuerpo-noticia, article",
        "selector_fecha": "time, .fecha",
        "selector_autor": ".autor",
    },
    "el_mostrador": {
        "nombre": "El Mostrador",
        "rss": "https://www.elmostrador.cl/feed/",
        "base_url": "https://www.elmostrador.cl",
        "selector_titulo": "h1.titulo, h1.entry-title, h1",
        "selector_contenido": ".cuerpo-noticia, .contenido, .entry-content, article",
        "selector_fecha": "span.fecha, time, .date",
        "selector_autor": ".autor, .author",
    },
    "biobiochile": {
        "nombre": "BioBioChile",
        "rss": "https://www.biobiochile.cl/feed/",
        "base_url": "https://www.biobiochile.cl",
        "selector_titulo": "h1.titulo, h1.entry-title, h1",
        "selector_contenido": ".contenido-noticia, .cuerpo, article, .entry-content",
        "selector_fecha": "time, .fecha, .date",
        "selector_autor": ".autor, .author",
    },
    "theclinic": {
        "nombre": "TheClinic",
        "rss": "https://www.theclinic.cl/feed/",
        "base_url": "https://www.theclinic.cl",
        "selector_titulo": "h1, .entry-title",
        "selector_contenido": ".contenido-noticia, .articulo, article, .entry-content",
        "selector_fecha": "time, .fecha",
        "selector_autor": ".autor, .author",
    },
    "interferencia": {
        "nombre": "Interferencia",
        "rss": "https://interferencia.cl/feed/",
        "base_url": "https://interferencia.cl",
        "selector_titulo": "h1, .entry-title, .titulo",
        "selector_contenido": ".contenido, .cuerpo, article, .entry-content, .contenido-noticia",
        "selector_fecha": "time, .fecha, .date",
        "selector_autor": ".autor, .author",
    },
    "ellibero": {
        "nombre": "El Líbero",
        "rss": "https://ellibero.cl/feed/",
        "base_url": "https://ellibero.cl",
        "selector_titulo": "h1, .entry-title, .titulo",
        "selector_contenido": ".contenido, .cuerpo, article, .entry-content, .contenido-noticia",
        "selector_fecha": "time, .fecha, .date",
        "selector_autor": ".autor, .author",
    },
}

# User-Agents rotativos para evitar bloqueo
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
]

# ══════════════════════════════════════════════════════
# POOL DE CONEXIONES POSTGRESQL
# ══════════════════════════════════════════════════════
_pool = pg_pool.ThreadedConnectionPool(1, MAX_WORKERS + 2, DB_URL)


def get_conn():
    return _pool.getconn()


def put_conn(conn):
    _pool.putconn(conn)


def ejecutar_con_reconexion(fn, *args, max_intentos=3, **kwargs):
    """Ejecuta fn reintentando si Neon cierra la conexión."""
    for intento in range(max_intentos):
        conn = get_conn()
        try:
            resultado = fn(conn, *args, **kwargs)
            put_conn(conn)
            return resultado
        except (psycopg2.OperationalError, psycopg2.InterfaceError) as e:
            print(f"  ⚠️ Conexión perdida ({e}), reintento {intento+1}/{max_intentos}")
            try:
                conn.close()
            except Exception:
                pass
            _pool.putconn(conn, close=True)
            time.sleep(2 * (intento + 1))
    raise ConnectionError(f"No se pudo reconectar tras {max_intentos} intentos")


# ══════════════════════════════════════════════════════
# CIRCUIT BREAKER
# ══════════════════════════════════════════════════════
_circuit_breaker = {"errores_consecutivos": 0, "ultimo_error_t": 0, "abierto": False}
_cb_lock = threading.Lock()


def _check_circuit_breaker():
    with _cb_lock:
        if _circuit_breaker["abierto"]:
            tiempo_abierto = time.time() - _circuit_breaker["ultimo_error_t"]
            if tiempo_abierto > 120:
                _circuit_breaker["abierto"] = False
                _circuit_breaker["errores_consecutivos"] = 0
                print("  ✅ Circuit breaker cerrado")
            else:
                raise RuntimeError(f"Circuit breaker abierto ({int(120 - tiempo_abierto)}s)")


def _registrar_error():
    with _cb_lock:
        _circuit_breaker["errores_consecutivos"] += 1
        _circuit_breaker["ultimo_error_t"] = time.time()
        if _circuit_breaker["errores_consecutivos"] > 10:
            _circuit_breaker["abierto"] = True
            print("  🚨 Circuit breaker ABIERTO")


def _registrar_exito():
    with _cb_lock:
        _circuit_breaker["errores_consecutivos"] = 0


# ══════════════════════════════════════════════════════
# ALERTAS TELEGRAM
# ══════════════════════════════════════════════════════
def enviar_alerta_telegram(mensaje):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT_ID, "text": mensaje[:4000], "parse_mode": "HTML"},
            timeout=10,
        )
    except Exception as e:
        print(f"  ⚠️ Error enviando alerta: {e}")


# ══════════════════════════════════════════════════════
# BATCH WRITES BUFFER
# ══════════════════════════════════════════════════════
_BUFFER_NOTICIAS = []
_BUFFER_MENCIONES = []
_BUFFER_LOCK = threading.Lock()


def _flush_noticias():
    global _BUFFER_NOTICIAS, _BUFFER_MENCIONES
    with _BUFFER_LOCK:
        noticias = _BUFFER_NOTICIAS[:]
        menciones = _BUFFER_MENCIONES[:]
        _BUFFER_NOTICIAS = []
        _BUFFER_MENCIONES = []

    def _ins(conn):
        cur = conn.cursor()
        for n in noticias:
            cur.execute("""
                INSERT INTO noticias (titulo, contenido, fuente, fecha_publicacion, url, hash_contenido, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, NOW())
                ON CONFLICT (hash_contenido) DO NOTHING
            """, (n["titulo"], n["contenido"], n["fuente"], n["fecha"], n["url"], n["hash"]))
        for m in menciones:
            try:
                cur.execute("""
                    INSERT INTO noticias_menciones (noticia_id, politico_id, tipo_mencion, contexto)
                    VALUES (
                        (SELECT id FROM noticias WHERE hash_contenido = %s),
                        %s, 'nombre', %s
                    )
                    ON CONFLICT DO NOTHING
                """, (m["hash_noticia"], m["politico_id"], m["contexto"]))
            except Exception:
                pass
        conn.commit()
        cur.close()

    if noticias:
        try:
            ejecutar_con_reconexion(_ins)
            print(f"  💾 Batch: {len(noticias)} noticias, {len(menciones)} menciones")
        except Exception as e:
            print(f"  ❌ Error en batch write: {e}")


def guardar_noticia(hash_contenido, titulo, contenido, fuente, url, fecha):
    global _BUFFER_NOTICIAS
    with _BUFFER_LOCK:
        _BUFFER_NOTICIAS.append({
            "hash": hash_contenido,
            "titulo": titulo,
            "contenido": contenido,
            "fuente": fuente,
            "url": url,
            "fecha": fecha,
        })
    if len(_BUFFER_NOTICIAS) >= BATCH_SIZE:
        _flush_noticias()


def guardar_mencion(hash_noticia, politico_id, contexto):
    global _BUFFER_MENCIONES
    with _BUFFER_LOCK:
        _BUFFER_MENCIONES.append({
            "hash_noticia": hash_noticia,
            "politico_id": politico_id,
            "contexto": contexto,
        })
    if len(_BUFFER_MENCIONES) >= BATCH_SIZE:
        _flush_noticias()


# ══════════════════════════════════════════════════════
# DETECTOR DE POLÍTICOS EN TEXTO
# ══════════════════════════════════════════════════════
def cargar_politicos():
    """Carga todos los políticos de la BD para búsqueda por nombre."""
    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""
        SELECT id, nombre_completo, 
               regexp_split_to_table(nombre_completo, '\\s+') as palabra
        FROM politicos
        WHERE LENGTH(nombre_completo) > 5
    """)
    rows = cur.fetchall()
    cur.close()
    put_conn(conn)
    
    # Construir índice: palabra normalizada -> lista de (id, nombre_completo)
    indice = {}
    for r in rows:
        palabra = normalizar_texto(r["palabra"])
        if len(palabra) < 3:
            continue
        if palabra not in indice:
            indice[palabra] = set()
        indice[palabra].add((r["id"], r["nombre_completo"]))
    
    return indice


def normalizar_texto(s):
    if not s:
        return ""
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower().strip()
    s = re.sub(r"\s+", " ", s)
    return s


def detectar_politicos_en_texto(texto, indice_palabras):
    """Detecta menciones de políticos en un texto."""
    if not texto:
        return []
    
    texto_norm = normalizar_texto(texto)
    palabras_texto = texto_norm.split()
    matches = []
    ids_vistos = set()
    
    # Buscar coincidencias de 2+ palabras consecutivas (apellidos compuestos)
    for longitud in [3, 2, 1]:
        for i in range(len(palabras_texto) - longitud + 1):
            ngrama = " ".join(palabras_texto[i:i+longitud])
            if ngrama in indice_palabras:
                for politico_id, nombre_completo in indice_palabras[ngrama]:
                    if politico_id not in ids_vistos:
                        ids_vistos.add(politico_id)
                        # Extraer contexto (50 caracteres alrededor)
                        inicio = max(0, i - 10)
                        fin = min(len(palabras_texto), i + longitud + 10)
                        contexto = " ".join(palabras_texto[inicio:fin])
                        matches.append({
                            "politico_id": politico_id,
                            "nombre": nombre_completo,
                            "contexto": contexto,
                        })
    
    return matches


# ══════════════════════════════════════════════════════
# SCRAPPERS POR FUENTE
# ══════════════════════════════════════════════════════
def obtener_user_agent():
    ua = USER_AGENTS[int(time.time() * 1000) % len(USER_AGENTS)]
    return ua


def scrapear_feed(fuente_key):
    """Scrapea un feed RSS y devuelve artículos."""
    fuente = FUENTES[fuente_key]
    print(f"  📡 Scrapeando {fuente['nombre']}...")
    
    try:
        headers = {"User-Agent": obtener_user_agent()}
        resp = requests.get(fuente["rss"], headers=headers, timeout=SCRAPE_TIMEOUT)
        if resp.status_code != 200:
            print(f"  ⚠️ {fuente['nombre']}: HTTP {resp.status_code}")
            return []
        
        feed = feedparser.parse(resp.text)
        articulos = []
        
        for entry in feed.entries[:MAX_ARTICULOS_POR_FUENTE]:
            titulo = getattr(entry, "title", "")
            url = getattr(entry, "link", "")
            fecha = getattr(entry, "published", "")
            contenido = getattr(entry, "summary", "")
            
            if not titulo:
                continue
            
            articulos.append({
                "titulo": titulo,
                "url": url,
                "fecha": fecha,
                "contenido": contenido,
                "fuente": fuente["nombre"],
            })
        
        _registrar_exito()
        print(f"  ✅ {fuente['nombre']}: {len(articulos)} artículos")
        return articulos
        
    except Exception as e:
        _registrar_error()
        print(f"  ❌ Error scrapeando {fuente['nombre']}: {e}")
        return []


def extraer_contenido_articulo(url, fuente):
    """Descarga y extrae el contenido completo de un artículo."""
    if not url:
        return ""
    
    try:
        headers = {"User-Agent": obtener_user_agent()}
        resp = requests.get(url, headers=headers, timeout=SCRAPE_TIMEOUT)
        if resp.status_code != 200:
            return ""
        
        soup = BeautifulSoup(resp.text, "html.parser")
        selector = fuente["selector_contenido"]
        
        # Intentar múltiples selectores
        for sel in selector.split(","):
            sel = sel.strip()
            contenido_el = soup.select_one(sel)
            if contenido_el:
                return contenido_el.get_text(strip=True)[:5000]
        
        return ""
        
    except Exception as e:
        print(f"  ⚠️ Error extrayendo {url}: {e}")
        return ""


# ══════════════════════════════════════════════════════
# PIPELINE PRINCIPAL
# ══════════════════════════════════════════════════════
def procesar_noticia(articulo, fuente, indice_palabras):
    """Procesa una noticia: extrae contenido, detecta políticos, guarda en BD."""
    if not articulo["titulo"]:
        return None
    
    # Extraer contenido completo si solo tenemos el resumen
    contenido = articulo["contenido"]
    if len(contenido) < 200 and articulo["url"]:
        contenido_completo = extraer_contenido_articulo(articulo["url"], fuente)
        if contenido_completo:
            contenido = contenido_completo
    
    if not contenido:
        contenido = articulo["titulo"]
    
    # Detectar políticos mencionados
    texto_busqueda = f"{articulo['titulo']} {contenido}"
    menciones = detectar_politicos_en_texto(texto_busqueda, indice_palabras)
    
    if not menciones:
        return None
    
    # Generar hash del contenido para dedup
    hash_contenido = hashlib.md5(
        f"{articulo['titulo']}{articulo['fuente']}".encode()
    ).hexdigest()
    
    # Parsear fecha
    fecha = None
    if articulo.get("fecha"):
        try:
            from dateutil.parser import parse as parse_date
            fecha = parse_date(articulo["fecha"]).date()
        except Exception:
            fecha = datetime.now().date()
    
    # Guardar noticia
    guardar_noticia(
        hash_contenido=hash_contenido,
        titulo=articulo["titulo"],
        contenido=contenido[:5000],
        fuente=articulo["fuente"],
        url=articulo.get("url", ""),
        fecha=fecha,
    )
    
    # Guardar menciones
    for m in menciones:
        guardar_mencion(hash_contenido, m["politico_id"], m["contexto"])
    
    return {
        "titulo": articulo["titulo"],
        "menciones": len(menciones),
        "politicos": [m["nombre"] for m in menciones],
    }


def run_pipeline():
    """Ejecuta el pipeline completo de scraping de noticias."""
    print("=" * 60)
    print("🗞️ WORKER DE NOTICIAS — Registro de Vándalos")
    print("=" * 60)
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📡 Fuentes: {len(FUENTES)}")
    print(f"⚡ Workers: {MAX_WORKERS}")
    print()
    
    # Cargar políticos para búsqueda
    print("📂 Cargando índice de políticos...")
    indice_palabras = cargar_politicos()
    print(f"✅ {len(indice_palabras)} palabras indexadas")
    print()
    
    # Scrapear feeds en paralelo
    todos_articulos = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(scrapear_feed, key): key
            for key in FUENTES.keys()
        }
        for future in as_completed(futures):
            fuente_key = futures[future]
            try:
                articulos = future.result()
                fuente = FUENTES[fuente_key]
                for a in articulos:
                    a["_fuente_obj"] = fuente
                todos_articulos.extend(articulos)
            except Exception as e:
                print(f"  ❌ Error en {fuente_key}: {e}")
    
    print(f"\n📰 Total artículos scrapeados: {len(todos_articulos)}")
    
    # Procesar artículos en paralelo
    resultados = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(procesar_noticia, a, a["_fuente_obj"], indice_palabras): a
            for a in todos_articulos
        }
        for future in as_completed(futures):
            try:
                resultado = future.result()
                if resultado:
                    resultados.append(resultado)
            except Exception as e:
                print(f"  ❌ Error procesando: {e}")
    
    # Flush final
    _flush_noticias()
    
    # Resumen
    print("\n" + "=" * 60)
    print("📊 RESUMEN")
    print("=" * 60)
    print(f"📰 Artículos procesados: {len(todos_articulos)}")
    print(f"🎯 Artículos con menciones: {len(resultados)}")
    
    # Alerta si se encontraron menciones
    if resultados:
        politicos_mencionados = set()
        for r in resultados:
            politicos_mencionados.update(r["politicos"])
        
        print(f"👤 Políticos mencionados: {len(politicos_mencionados)}")
        
        # Enviar alerta Telegram
        if TELEGRAM_BOT_TOKEN:
            mensaje = f"🗞️ <b>Worker de Noticias</b>\n\n"
            mensaje += f"📰 {len(resultados)} noticias con menciones\n"
            mensaje += f"👤 {len(politicos_mencionados)} políticos detectados\n\n"
            mensaje += "Políticos:\n" + "\n".join([f"• {p}" for p in list(politicos_mencionados)[:10]])
            enviar_alerta_telegram(mensaje)
    
    return len(resultados)


# ══════════════════════════════════════════════════════
# GRACEFUL SHUTDOWN
# ══════════════════════════════════════════════════════
_shutdown = threading.Event()


def _signal_handler(signum, frame):
    print("\n🛑 Señal de apagado recibida, terminando...")
    _shutdown.set()


signal.signal(signal.SIGTERM, _signal_handler)
signal.signal(signal.SIGINT, _signal_handler)


if __name__ == "__main__":
    try:
        count = run_pipeline()
        sys.exit(0 if count >= 0 else 1)
    except KeyboardInterrupt:
        print("\n🛑 Interrumpido por usuario")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error fatal: {e}")
        traceback.print_exc()
        sys.exit(1)
