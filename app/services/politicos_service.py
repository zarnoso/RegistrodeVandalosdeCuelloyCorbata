from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from uuid import UUID

from app.models import Politico, Evento, Empresa, Patrimonio
from app.schemas import PoliticoBase, StatsResponse


class PoliticosService:
    
    @staticmethod
    def get_all(db: Session, skip: int = 0, limit: int = 100, 
                 partido: Optional[str] = None, institucion: Optional[str] = None,
                 busqueda: Optional[str] = None) -> List[Politico]:
        """Obtiene lista de políticos con filtros."""
        query = db.query(Politico).filter(Politico.es_activo == True)
        
        if partido:
            query = query.filter(Politico.partido == partido)
        
        if institucion:
            query = query.filter(Politico.institucion == institucion)
        
        if busqueda:
            query = query.filter(
                Politico.nombre_completo.ilike(f"%{busqueda}%")
            )
        
        return query.order_by(Politico.nombre_completo).offset(skip).limit(limit).all()
    
    @staticmethod
    def get_by_id(db: Session, politico_id: UUID) -> Optional[Politico]:
        """Obtiene un político por ID con todos sus datos relacionados."""
        return db.query(Politico).filter(Politico.id == politico_id).first()
    
    @staticmethod
    def get_by_rut(db: Session, rut: str) -> Optional[Politico]:
        """Obtiene un político por RUT."""
        return db.query(Politico).filter(Politico.rut == rut).first()
    
    @staticmethod
    def create(db: Session, politico: PoliticoBase) -> Politico:
        """Crea un nuevo político."""
        db_politico = Politico(**politico.model_dump())
        db.add(db_politico)
        db.commit()
        db.refresh(db_politico)
        return db_politico
    
    @staticmethod
    def create_bulk(db: Session, politicos: List[dict]) -> int:
        """Crea múltiples políticos de forma eficiente."""
        db.add_all([Politico(**p) for p in politicos])
        db.commit()
        return len(politicos)
    
    @staticmethod
    def get_stats(db: Session) -> StatsResponse:
        """Obtiene estadísticas generales."""
        total = db.query(Politico).filter(Politico.es_activo == True).count()
        
        total_eventos = db.query(Evento).count()
        eventos_activos = db.query(Evento).filter(
            Evento.estado_actual.in_(["en_revisión", "formalizado", "investigado"])
        ).count()
        
        # Contar políticos con eventos
        politicos_con_eventos = db.query(Evento.politico_id).distinct().count()
        
        # Distribución por estado
        por_estado = dict(
            db.query(Evento.estado_actual, func.count(Evento.id))
            .group_by(Evento.estado_actual).all()
        )
        
        # Distribución por tipo de alerta
        por_tipo = dict(
            db.query(Evento.tipo_alerta, func.count(Evento.id))
            .group_by(Evento.tipo_alerta).all()
        )
        
        return StatsResponse(
            total_politicos=total,
            total_eventos=total_eventos,
            eventos_activos=eventos_activos,
            politicos_con_eventos=politicos_con_eventos,
            por_estado=por_estado,
            por_tipo_alerta=por_tipo
        )
    
    @staticmethod
    def enrich_with_counts(db: Session, politicos: List[Politico]) -> List[dict]:
        """Agrega conteos de eventos y empresas a cada político."""
        result = []
        for p in politicos:
            num_eventos = db.query(Evento).filter(Evento.politico_id == p.id).count()
            num_empresas = db.query(Empresa).join(Patrimonio).filter(
                Patrimonio.politico_id == p.id
            ).count()
            
            # Determinar estado de riesgo
            ultimo_evento = db.query(Evento).filter(
                Evento.politico_id == p.id
            ).order_by(Evento.fecha_inicio.desc()).first()
            
            if num_eventos == 0:
                estado_riesgo = "sin_registros"
            elif ultimo_evento and ultimo_evento.estado_actual in ["formalizado", "condenado"]:
                estado_riesgo = "alerta_roja"
            elif ultimo_evento and ultimo_evento.estado_actual in ["en_revisión", "investigado"]:
                estado_riesgo = "alerta_naranja"
            else:
                estado_riesgo = "sin_problemas"
            
            data = {
                "id": p.id,
                "rut": p.rut,
                "nombre_completo": p.nombre_completo,
                "cargo": p.cargo,
                "institucion": p.institucion,
                "partido": p.partido,
                "distrito": p.distrito,
                "region": p.region,
                "es_activo": p.es_activo,
                "created_at": p.created_at,
                "num_eventos": num_eventos,
                "num_empresas": num_empresas,
                "estado_riesgo": estado_riesgo
            }
            result.append(data)
        
        return result
