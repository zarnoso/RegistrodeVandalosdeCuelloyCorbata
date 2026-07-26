"""Recolecta fuentes oficiales hacia staging; nunca publica automáticamente."""

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
import sys
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

CAMARA_ENDPOINT = (
    "https://opendata.camara.cl/wspublico/wsdiputados.asmx/"
    "retornarDiputadosPeriodoActual"
)
BCN_LIST = (
    "https://www.bcn.cl/historiapolitica/resenas_parlamentarias/"
    "index.html?categ=en_ejercicio&filtros=3&pagina={page}&K=1"
)
SENADO_LIST = (
    "https://www.senado.cl/senadoras-y-senadores/"
    "listado-de-senadoras-y-senadores"
)


class SourceUnavailable(RuntimeError):
    pass


def fetch(session: requests.Session, url: str) -> requests.Response:
    response = session.get(url, timeout=30)
    response.raise_for_status()
    return response


def collect_camara(session: requests.Session) -> list[dict]:
    response = fetch(session, CAMARA_ENDPOINT)
    content_type = response.headers.get("content-type", "").lower()
    if "html" in content_type or b"Temporalmente en Mantenci" in response.content:
        raise SourceUnavailable(
            "Cámara Datos Abiertos respondió con su página de mantención."
        )
    soup = BeautifulSoup(response.content, "xml")
    records = []
    for item in soup.find_all(["Diputado", "diputado"]):
        def value(*names):
            for name in names:
                tag = item.find(name)
                if tag and tag.get_text(strip=True):
                    return tag.get_text(strip=True)
            return None

        names = value("nombre", "Nombres") or ""
        paternal = value("apellidoPaterno", "ApellidoPaterno") or ""
        maternal = value("apellidoMaterno", "ApellidoMaterno") or ""
        records.append({
            "nombre_completo": " ".join(
                part for part in (names, paternal, maternal) if part
            ),
            "nombres": names or None,
            "apellido_paterno": paternal or None,
            "apellido_materno": maternal or None,
            "cargo": "Diputado/a",
            "institucion": "Cámara de Diputadas y Diputados",
            "partido": value("partido", "Partido"),
            "distrito": value("distrito", "Distrito"),
            "region": value("region", "Region"),
            "fuente_id": "camara_datos_abiertos",
            "fuente_url": CAMARA_ENDPOINT,
        })
    if not records:
        raise SourceUnavailable("La respuesta de Cámara no contenía registros reconocibles.")
    return records


def collect_bcn(session: requests.Session, pages: list[int]) -> list[dict]:
    records = {}
    for page in pages:
        url = BCN_LIST.format(page=page)
        soup = BeautifulSoup(fetch(session, url).text, "html.parser")
        for anchor in soup.find_all("a", href=True):
            href = anchor["href"]
            if "/historiapolitica/resenas_parlamentarias/wiki/" not in href:
                continue
            name = anchor.get_text(" ", strip=True)
            if not name:
                continue
            profile_url = urljoin("https://www.bcn.cl", href)
            records[profile_url] = {
                "nombre_completo": name,
                "cargo": "Diputado/a",
                "institucion": "Congreso Nacional",
                "fuente_id": "bcn_resenas",
                "fuente_url": profile_url,
                "pagina_origen": url,
            }
    return list(records.values())


def collect_senado(session: requests.Session) -> list[dict]:
    response = fetch(session, SENADO_LIST)
    response.encoding = "utf-8"
    soup = BeautifulSoup(response.text, "html.parser")
    records = []
    pattern = re.compile(
        r"Circunscripci[oó]n\s+(\d+)\s+Regi[oó]n(?:\s+de|\s+del)?\s+(.+?)\s+"
        r"Partido\s+(.+?)(?:\s+Comit[eé]\s+(.+))?$",
        re.IGNORECASE,
    )
    for card in soup.select(".card--people"):
        heading = card.select_one("h3")
        if not heading:
            continue
        name = heading.get_text(" ", strip=True)
        text = card.get_text(" ", strip=True)
        details = text[len(name):].strip()
        match = pattern.search(details)
        if not match:
            # Las dos tarjetas de Mesa Directiva se repiten luego en el listado.
            continue
        circunscripcion, region, partido, committee = match.groups()
        image = card.select_one("img")
        records.append({
            "nombre_completo": name,
            "cargo": "Senador/a",
            "institucion": "Senado de la República",
            "partido": partido.strip(),
            "distrito": f"Circunscripción {circunscripcion}",
            "region": region.strip(),
            "comite": committee.strip() if committee else None,
            "foto_url": urljoin(SENADO_LIST, image.get("src")) if image else None,
            "fuente_id": "senado_listado",
            "fuente_url": SENADO_LIST,
        })
    if not records:
        raise SourceUnavailable("El listado del Senado no contenía tarjetas reconocibles.")
    return records


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source",
        choices=["camara", "senado", "bcn", "all"],
        default="all",
    )
    parser.add_argument("--pages", nargs="+", type=int, default=[1, 2, 3, 4])
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--output",
        type=Path,
        default=PROJECT_ROOT / "data" / "staging_fuentes_oficiales.json",
    )
    args = parser.parse_args()
    session = requests.Session()
    session.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 Chrome/126 Safari/537.36"
        ),
        "Accept-Language": "es-CL,es;q=0.9",
    })
    payload = {
        "extraido_en": datetime.now(timezone.utc).isoformat(),
        "estado": {},
        "registros": [],
    }
    if args.source in ("camara", "all"):
        try:
            records = collect_camara(session)
            payload["registros"].extend(records)
            payload["estado"]["camara"] = {"ok": True, "registros": len(records)}
        except Exception as exc:
            payload["estado"]["camara"] = {"ok": False, "error": str(exc)}
    if args.source in ("bcn", "all"):
        try:
            records = collect_bcn(session, args.pages)
            payload["registros"].extend(records)
            payload["estado"]["bcn"] = {"ok": True, "registros": len(records)}
        except Exception as exc:
            payload["estado"]["bcn"] = {"ok": False, "error": str(exc)}
    if args.source in ("senado", "all"):
        try:
            records = collect_senado(session)
            payload["registros"].extend(records)
            payload["estado"]["senado"] = {"ok": True, "registros": len(records)}
        except Exception as exc:
            payload["estado"]["senado"] = {"ok": False, "error": str(exc)}

    if args.dry_run:
        print(json.dumps(payload["estado"], ensure_ascii=False, indent=2))
        print(f"Total staging: {len(payload['registros'])}")
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"Staging guardado en {args.output}")
    return 0 if payload["registros"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
