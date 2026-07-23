from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.core.database import get_db
from app.core.limiter import limiter
from app.services.politicos_service import PoliticosService
from app.schemas import PoliticoResponse, PoliticoDetailResponse, StatsResponse

router = APIRouter()


@router.get("/", response_model=List[PoliticoResponse])
@limiter.limit("60/minute")
def get_politicos(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    partido: Optional[str] = None,
    institucion: Optional[str] = None,
    busqueda: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Obtiene lista de políticos con filtros opcionales."""
    politicos = PoliticosService.get_all(
        db, skip=skip, limit=limit,
        partido=partido, institucion=institucion, busqueda=busqueda
    )
    
    # Enriquecer con conteos
    return PoliticosService.enrich_with_counts(db, politicos)


@router.get("/stats", response_model=StatsResponse)
def get_stats(db: Session = Depends(get_db)):
    """Obtiene estadísticas generales."""
    return PoliticosService.get_stats(db)


@router.get("/{politico_id}", response_model=PoliticoDetailResponse)
def get_politico(politico_id: UUID, db: Session = Depends(get_db)):
    """Obtiene detalle de un político con todos sus datos."""
    politico = PoliticosService.get_by_id(db, politico_id)
    
    if not politico:
        raise HTTPException(status_code=404, detail="Político no encontrado")
    
    # Preparar respuesta detallada
    patrimonios_data = []
    for pat in politico.patrimonios:
        patrimonios_data.append({
            "id": str(pat.id),
            "periodo": pat.periodo,
            "patrimonio_total": float(pat.patrimonio_total) if pat.patrimonio_total else None,
            "fuente": pat.fuente,
            "url_detalle": pat.url_detalle,
            "empresas": [
                {
                    "id": str(emp.id),
                    "rut_empresa": emp.rut_empresa,
                    "razon_social": emp.razon_social,
                    "tipo_sociedad": emp.tipo_sociedad,
                    "rol": emp.rol,
                    "porcentaje_participacion": float(emp.porcentaje_participacion) if emp.porcentaje_participacion else None,
                    "estado": emp.estado
                }
                for emp in pat.empresas
            ]
        })
    
    eventos_data = [
        {
            "id": str(e.id),
            "caso_nombre": e.caso_nombre,
            "tipo_alerta": e.tipo_alerta,
            "resumen": e.resumen,
            "fecha_inicio": e.fecha_inicio,
            "estado_actual": e.estado_actual,
            "url_noticia": e.url_noticia,
            "fuente": e.fuente
        }
        for e in politico.eventos
    ]
    
    return {
        "id": politico.id,
        "rut": politico.rut,
        "nombre_completo": politico.nombre_completo,
        "cargo": politico.cargo,
        "institucion": politico.institucion,
        "partido": politico.partido,
        "coalicion": politico.coalicion,
        "distrito": politico.distrito,
        "region": politico.region,
        "es_activo": politico.es_activo,
        "created_at": politico.created_at,
        "updated_at": politico.updated_at,
        "patrimonios": patrimonios_data,
        "eventos": eventos_data,
        "empresas": []  # Empresas ya están en patrimonios
    }


@router.get("/buscar/rut/{rut}")
@limiter.limit("30/minute")
def buscar_por_rut(request: Request, rut: str, db: Session = Depends(get_db)):
    """Busca un político por RUT."""
    politico = PoliticosService.get_by_rut(db, rut)
    
    if not politico:
        raise HTTPException(status_code=404, detail="Político no encontrado")
    
    return {"id": str(politico.id), "nombre_completo": politico.nombre_completo}


@router.get("/buscar/nombre/{nombre}")
@limiter.limit("30/minute")
def buscar_por_nombre(request: Request, nombre: str, limit: int = Query(5, ge=1, le=20), db: Session = Depends(get_db)):
    """Busca políticos por nombre (tolerante a typos/tildes vía pg_trgm).
    Pensado para gente que no tiene el RUT a mano: solo escribe el nombre
    y recibe si el político tiene o no problemas registrados (estado_riesgo).
    Si hay homónimos, devuelve varios resultados con cargo/región/partido
    para desambiguar."""
    politicos = PoliticosService.get_all(db, skip=0, limit=limit, busqueda=nombre)

    if not politicos:
        raise HTTPException(status_code=404, detail="No se encontraron políticos con ese nombre")

    return PoliticosService.enrich_with_counts(db, politicos)
