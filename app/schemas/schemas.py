from pydantic import BaseModel, Field
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

    class Config:
        from_attributes = True


class EventoBase(BaseModel):
    caso_nombre: Optional[str] = None
    tipo_alerta: Optional[str] = None
    resumen: Optional[str] = None
    fecha_inicio: Optional[date] = None
    estado_actual: Optional[str] = None
    url_noticia: Optional[str] = None
    fuente: Optional[str] = None
    url_oficial: Optional[str] = None
    rit_ruc: Optional[str] = None
    tribunal: Optional[str] = None
    confianza: Optional[str] = None
    procesada_ia: bool = False
    verificada_humano: bool = False


class EventoResponse(EventoBase):
    id: UUID

    class Config:
        from_attributes = True


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
    num_familiares: int = 0
    estado_riesgo: str = "sin_registros"

    class Config:
        from_attributes = True


class PoliticoDetailResponse(PoliticoBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    patrimonios: List[dict] = Field(default_factory=list)
    eventos: List[EventoResponse] = Field(default_factory=list)
    empresas: List[EmpresaResponse] = Field(default_factory=list)
    familiares: List[dict] = Field(default_factory=list)

    class Config:
        from_attributes = True


# ============ Stats Schemas ============

class StatsResponse(BaseModel):
    total_politicos: int
    total_eventos: int
    eventos_activos: int
    politicos_con_eventos: int
    por_estado: dict
    por_tipo_alerta: dict


class GraphNode(BaseModel):
    id: str
    tipo: str
    etiqueta: str
    metadata: dict = Field(default_factory=dict)


class GraphEdge(BaseModel):
    id: str
    origen: str
    destino: str
    tipo: str
    metadata: dict = Field(default_factory=dict)


class GraphResponse(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]
    total_politicos: int
    truncado: bool = False


class SomItem(BaseModel):
    politico_id: UUID
    nombre_completo: str
    metadata: dict
    features: dict[str, float]
    normalized: List[float]


class SomResponse(BaseModel):
    dimensions: List[str]
    items: List[SomItem]
    metodologia: str
