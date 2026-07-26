from sqlalchemy.orm import Session, selectinload
from sqlalchemy import case, func, or_
from typing import List, Optional
from uuid import UUID

from app.models import (
    Politico,
    Evento,
    Empresa,
    Patrimonio,
    Familiar,
    FamiliarEmpresa,
)
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
            normalized_name = func.immutable_unaccent(
                func.lower(Politico.nombre_completo)
            )
            normalized_search = func.immutable_unaccent(func.lower(busqueda))
            query = query.filter(
                or_(
                    normalized_name.contains(normalized_search),
                    func.similarity(normalized_name, normalized_search) >= 0.25,
                )
            )
        
        return query.order_by(Politico.nombre_completo).offset(skip).limit(limit).all()
    
    @staticmethod
    def get_by_id(db: Session, politico_id: UUID) -> Optional[Politico]:
        """Obtiene un político por ID con todos sus datos relacionados."""
        return (
            db.query(Politico)
            .options(
                selectinload(Politico.eventos),
                selectinload(Politico.patrimonios).selectinload(Patrimonio.empresas),
                selectinload(Politico.familiares)
                .selectinload(Familiar.empresas)
                .selectinload(FamiliarEmpresa.empresa),
            )
            .filter(Politico.id == politico_id)
            .first()
        )
    
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
        if not politicos:
            return []

        politico_ids = [p.id for p in politicos]
        event_counts = dict(
            db.query(Evento.politico_id, func.count(Evento.id))
            .filter(Evento.politico_id.in_(politico_ids))
            .group_by(Evento.politico_id)
            .all()
        )
        company_counts = dict(
            db.query(Patrimonio.politico_id, func.count(Empresa.id))
            .join(Empresa, Empresa.patrimonio_id == Patrimonio.id)
            .filter(Patrimonio.politico_id.in_(politico_ids))
            .group_by(Patrimonio.politico_id)
            .all()
        )
        family_counts = dict(
            db.query(Familiar.politico_id, func.count(Familiar.id))
            .filter(Familiar.politico_id.in_(politico_ids))
            .group_by(Familiar.politico_id)
            .all()
        )
        latest_events = {}
        for event in (
            db.query(Evento)
            .filter(Evento.politico_id.in_(politico_ids))
            .order_by(Evento.politico_id, Evento.fecha_inicio.desc().nullslast())
            .all()
        ):
            latest_events.setdefault(event.politico_id, event)

        result = []
        for p in politicos:
            num_eventos = event_counts.get(p.id, 0)
            num_empresas = company_counts.get(p.id, 0)
            num_familiares = family_counts.get(p.id, 0)
            ultimo_evento = latest_events.get(p.id)
            
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
                "num_familiares": num_familiares,
                "estado_riesgo": estado_riesgo
            }
            result.append(data)
        
        return result

    @staticmethod
    def get_graph(
        db: Session,
        limit: int = 100,
        partido: Optional[str] = None,
        region: Optional[str] = None,
    ) -> dict:
        """Construye nodos y aristas solo desde relaciones explícitas en la BD."""
        query = (
            db.query(Politico)
            .options(
                selectinload(Politico.eventos),
                selectinload(Politico.patrimonios).selectinload(Patrimonio.empresas),
                selectinload(Politico.familiares)
                .selectinload(Familiar.empresas)
                .selectinload(FamiliarEmpresa.empresa),
            )
            .filter(Politico.es_activo == True)
        )
        if partido:
            query = query.filter(Politico.partido == partido)
        if region:
            query = query.filter(Politico.region == region)

        total = query.count()
        politicos = query.order_by(Politico.nombre_completo).limit(limit).all()
        nodes = {}
        edges = []

        def add_node(node_id: str, tipo: str, etiqueta: str, metadata: dict):
            nodes.setdefault(
                node_id,
                {"id": node_id, "tipo": tipo, "etiqueta": etiqueta, "metadata": metadata},
            )

        def add_edge(origen: str, destino: str, tipo: str, metadata: dict):
            edges.append({
                "id": f"{tipo}:{origen}:{destino}",
                "origen": origen,
                "destino": destino,
                "tipo": tipo,
                "metadata": metadata,
            })

        for politico in politicos:
            politico_id = f"politico:{politico.id}"
            add_node(politico_id, "politico", politico.nombre_completo, {
                "cargo": politico.cargo,
                "partido": politico.partido,
                "region": politico.region,
            })

            for evento in politico.eventos:
                evento_id = f"evento:{evento.id}"
                add_node(evento_id, "evento", evento.caso_nombre or "Antecedente", {
                    "estado": evento.estado_actual,
                    "tipo_alerta": evento.tipo_alerta,
                    "fuente": evento.fuente,
                    "verificada_humano": bool(evento.verificada_humano),
                })
                add_edge(politico_id, evento_id, "tiene_antecedente", {
                    "fuente": evento.fuente,
                    "url": evento.url_oficial or evento.url_noticia,
                })

            for patrimonio in politico.patrimonios:
                for empresa in patrimonio.empresas:
                    empresa_id = f"empresa:{empresa.id}"
                    add_node(
                        empresa_id,
                        "empresa",
                        empresa.razon_social or empresa.rut_empresa or "Empresa",
                        {"rut": empresa.rut_empresa, "estado": empresa.estado},
                    )
                    add_edge(politico_id, empresa_id, "participa_en", {
                        "rol": empresa.rol,
                        "porcentaje": (
                            float(empresa.porcentaje_participacion)
                            if empresa.porcentaje_participacion is not None else None
                        ),
                        "fuente": patrimonio.fuente,
                        "url": patrimonio.url_detalle,
                    })

            for familiar in politico.familiares:
                familiar_id = f"familiar:{familiar.id}"
                add_node(familiar_id, "familiar", familiar.nombre_completo or "Familiar", {
                    "parentesco": familiar.parentesco,
                    "fuente": familiar.fuente,
                    "verificada_humano": bool(familiar.verificada_humano),
                })
                add_edge(politico_id, familiar_id, "familiar_de", {
                    "parentesco": familiar.parentesco,
                    "fuente": familiar.fuente,
                    "url": familiar.url_fuente,
                })
                for vinculo in familiar.empresas:
                    empresa = vinculo.empresa
                    empresa_id = f"empresa:{empresa.id}"
                    add_node(
                        empresa_id,
                        "empresa",
                        empresa.razon_social or empresa.rut_empresa or "Empresa",
                        {"rut": empresa.rut_empresa, "estado": empresa.estado},
                    )
                    add_edge(familiar_id, empresa_id, "vinculado_a_empresa", {
                        "rol": vinculo.rol_familiar,
                        "vinculo_politico": vinculo.vinculo_politico,
                        "fuente": vinculo.fuente,
                        "url": vinculo.url_fuente,
                        "verificada_humano": bool(vinculo.verificada_humano),
                    })

        return {
            "nodes": list(nodes.values()),
            "edges": edges,
            "total_politicos": total,
            "truncado": total > len(politicos),
        }

    @staticmethod
    def get_som_vectors(db: Session, limit: int = 500) -> dict:
        """Entrega vectores explicables; el entrenamiento SOM ocurre en el cliente."""
        politicos = (
            db.query(Politico)
            .filter(Politico.es_activo == True)
            .order_by(Politico.nombre_completo)
            .limit(limit)
            .all()
        )
        if not politicos:
            return {
                "dimensions": [],
                "items": [],
                "metodologia": "Sin registros suficientes para construir vectores.",
            }

        ids = [p.id for p in politicos]
        event_stats = {
            row[0]: row[1:]
            for row in (
                db.query(
                    Evento.politico_id,
                    func.count(Evento.id),
                    func.sum(case((Evento.estado_actual.in_(
                        ["en_revisión", "investigado"]
                    ), 1), else_=0)),
                    func.sum(case((Evento.estado_actual == "formalizado", 1), else_=0)),
                    func.sum(case((Evento.estado_actual == "condenado", 1), else_=0)),
                    func.sum(case((Evento.verificada_humano == True, 1), else_=0)),
                )
                .filter(Evento.politico_id.in_(ids))
                .group_by(Evento.politico_id)
                .all()
            )
        }
        company_counts = dict(
            db.query(Patrimonio.politico_id, func.count(Empresa.id))
            .join(Empresa, Empresa.patrimonio_id == Patrimonio.id)
            .filter(Patrimonio.politico_id.in_(ids))
            .group_by(Patrimonio.politico_id)
            .all()
        )
        family_counts = dict(
            db.query(Familiar.politico_id, func.count(Familiar.id))
            .filter(Familiar.politico_id.in_(ids))
            .group_by(Familiar.politico_id)
            .all()
        )
        dimensions = [
            "eventos_total",
            "eventos_revision",
            "eventos_formalizados",
            "eventos_condena",
            "eventos_verificados",
            "empresas",
            "familiares",
        ]
        raw_items = []
        for politico in politicos:
            stats = event_stats.get(politico.id, (0, 0, 0, 0, 0))
            values = [
                float(stats[0] or 0),
                float(stats[1] or 0),
                float(stats[2] or 0),
                float(stats[3] or 0),
                float(stats[4] or 0),
                float(company_counts.get(politico.id, 0)),
                float(family_counts.get(politico.id, 0)),
            ]
            raw_items.append((politico, values))

        maxima = [max(values[i] for _, values in raw_items) for i in range(len(dimensions))]
        items = []
        for politico, values in raw_items:
            normalized = [
                value / maxima[i] if maxima[i] else 0.0
                for i, value in enumerate(values)
            ]
            items.append({
                "politico_id": politico.id,
                "nombre_completo": politico.nombre_completo,
                "metadata": {
                    "cargo": politico.cargo,
                    "partido": politico.partido,
                    "region": politico.region,
                },
                "features": dict(zip(dimensions, values)),
                "normalized": normalized,
            })
        return {
            "dimensions": dimensions,
            "items": items,
            "metodologia": (
                "Normalización min-max por dimensión sobre la selección actual. "
                "La proximidad representa similitud de atributos, no vínculos ni culpabilidad."
            ),
        }
