from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, Numeric, Date
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.core.database import Base


class Politico(Base):
    __tablename__ = "politicos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rut = Column(String(12), unique=True, nullable=True)
    nombre_completo = Column(String(255), nullable=False)
    nombres = Column(String(100))
    apellido_paterno = Column(String(100))
    apellido_materno = Column(String(100))
    cargo = Column(String(100))
    institucion = Column(String(100))
    partido = Column(String(100))
    coalicion = Column(String(100))
    distrito = Column(String(50))
    region = Column(String(50))
    periodo = Column(String(20))
    es_activo = Column(Boolean, default=True)
    foto_url = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    patrimonios = relationship("Patrimonio", back_populates="politico", cascade="all, delete-orphan")
    eventos = relationship("Evento", back_populates="politico", cascade="all, delete-orphan")
    familiares = relationship("Familiar", back_populates="politico", cascade="all, delete-orphan")


class Patrimonio(Base):
    __tablename__ = "patrimonio"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    politico_id = Column(UUID(as_uuid=True), ForeignKey("politicos.id", ondelete="CASCADE"))
    periodo = Column(String(20))
    patrimonio_total = Column(Numeric(15, 2))
    fuente = Column(String(100))
    url_detalle = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    politico = relationship("Politico", back_populates="patrimonios")
    empresas = relationship("Empresa", back_populates="patrimonio", cascade="all, delete-orphan")


class Empresa(Base):
    __tablename__ = "empresas"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patrimonio_id = Column(UUID(as_uuid=True), ForeignKey("patrimonio.id", ondelete="CASCADE"))
    rut_empresa = Column(String(20))
    razon_social = Column(String(255))
    tipo_sociedad = Column(String(50))
    rol = Column(String(50))
    porcentaje_participacion = Column(Numeric(5, 2))
    estado = Column(String(20))
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    patrimonio = relationship("Patrimonio", back_populates="empresas")


class Evento(Base):
    __tablename__ = "eventos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    politico_id = Column(UUID(as_uuid=True), ForeignKey("politicos.id", ondelete="CASCADE"))
    caso_nombre = Column(String(255))
    tipo_alerta = Column(String(50))  # corrupcion, colusion, fraude, cohecho, malversacion, otro
    subtipo = Column(String(100))
    resumen = Column(Text)
    fecha_inicio = Column(Date)
    fecha_termino = Column(Date)
    estado_actual = Column(String(50))  # en_revisión, formalizado, condenado, sobreseido, absuelto
    url_noticia = Column(Text)
    cita_textual = Column(Text)
    fuente = Column(String(100))
    confianza = Column(String(20))  # ALTA, MEDIA, BAJA
    procesada_ia = Column(Boolean, default=False)
    verificada_humano = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    politico = relationship("Politico", back_populates="eventos")


class Familiar(Base):
    __tablename__ = "familiares"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    politico_id = Column(UUID(as_uuid=True), ForeignKey("politicos.id", ondelete="CASCADE"))
    parentesco = Column(String(50))
    nombre_completo = Column(String(255))
    rut = Column(String(12))
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    politico = relationship("Politico", back_populates="familiares")
