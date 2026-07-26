from fastapi import APIRouter, Request

from app.core.limiter import limiter
from app.services.sources_service import SourcesService


router = APIRouter()


@router.get("/fuentes")
@limiter.limit("30/minute")
def get_sources(request: Request):
    """Catálogo de fuentes y reglas de procedencia de la plataforma."""
    return SourcesService.list_sources()
