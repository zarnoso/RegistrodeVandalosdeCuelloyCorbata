"""Recolecta diputados del período vigente y conserva enlaces oficiales de Cámara."""

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path

import requests

PROJECT_ROOT = Path(__file__).resolve().parent.parent
API_URL = "https://conocelos.cl/api/deputies/by-period"


def collect(period_id: int) -> list[dict]:
    response = requests.get(
        API_URL,
        params={"periodId": period_id},
        headers={"User-Agent": "ChileTransparente/1.0"},
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()
    records = []
    for deputy in payload.get("deputies", []):
        raw_name = (deputy.get("name") or "").strip()
        name = re.sub(r"^(Sr\\.?|Sra\\.?)\\s+", "", raw_name).strip()
        if not name:
            continue
        records.append({
            "nombre_completo": name,
            "cargo": "Diputado/a",
            "institucion": "Cámara de Diputadas y Diputados",
            "partido": deputy.get("party"),
            "periodo": f"{deputy.get('desde', '')}-{deputy.get('hasta', '')}",
            "foto_url": deputy.get("image_url"),
            "fuente_id": "camara_diputados",
            "fuente_url": deputy.get("profile_url") or "https://www.camara.cl/diputados/diputados.aspx",
        })
    return records


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--period-id", type=int, default=16)
    parser.add_argument(
        "--output",
        type=Path,
        default=PROJECT_ROOT / "data" / "staging_diputados_oficiales.json",
    )
    args = parser.parse_args()
    records = collect(args.period_id)
    payload = {
        "extraido_en": datetime.now(timezone.utc).isoformat(),
        "period_id": args.period_id,
        "estado": {"camara": {"ok": bool(records), "registros": len(records)}},
        "registros": records,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Staging guardado en {args.output} ({len(records)} registros)")
