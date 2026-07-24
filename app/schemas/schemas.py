from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime, date
from uuid import UUID


# ============ Politico Schemas ============

class EmpresaBase(BaseModel):
    razon_social: Optional[str] = None
    rut_empresa: Optional[str] = None
    tipo_sociedad: Optional[str] = None
    rol: Optional[str] = None
    porcentaje_participacion: Optional[float] = None
    estado: Optional[str] = None


class EmpresaResponse(EmpresaBase):
    id: UUID

    model_config = ConfigDict(from_attributes=True)


class EventoBase(BaseModel):
    caso_nombre: Optional[str] = None
    tipo_alerta: Optional[str] = None
    resumen: Optional[str] = None
    fecha_inicio: Optional[date] = None
    estado_actual: Optional[str] = None
    url_noticia: Optional[str] = None
    fuente: Optional[str] = None


class EventoResponse(EventoBase):
    id: UUID

    model_config = ConfigDict(from_attributes=True)


class PoliticoBase(BaseModel):
    rut: Optional[str] = None
    nombre_completo: str
    cargo: Optional[str] = None
    institucion: Optional[str] = None
    partido: Optional[str] = None
    coalicion: Optional[str] = None
    distrito: Optional[str] = None
    region: Optional[str] = None
    es_activo: bool = True


class PoliticoResponse(PoliticoBase):
    id: UUID
    created_at: datetime
    num_eventos: int = 0
    num_empresas: int = 0
    estado_riesgo: str = "sin_registros"

    model_config = ConfigDict(from_attributes=True)


class PoliticoDetailResponse(PoliticoBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    patrimonios: List[dict] = []
    eventos: List[EventoResponse] = []
    empresas: List[EmpresaResponse] = []

    model_config = ConfigDict(from_attributes=True)


# ============ Stats Schemas ============

class StatsResponse(BaseModel):
    total_politicos: int
    total_eventos: int
    eventos_activos: int
    politicos_con_eventos: int
    por_estado: dict
    por_tipo_alerta: dict
