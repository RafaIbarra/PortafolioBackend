from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from database import Base
from datetime import datetime
from sqlalchemy.orm import relationship


class SesionActiva(Base):
    __tablename__ = "SesionActiva"
    
    id = Column(Integer, primary_key=True, index=True)
    DataSesion = Column(String(150), index=True)

class Proyectos(Base):
    __tablename__ = "Proyectos"
    
    id = Column(Integer, primary_key=True, index=True)
    Sistema = Column(String(150), index=True)
    Descripcion = Column(String(200), nullable=False)
    Logo = Column(String(100), nullable=True)
    fecha_registro = Column(DateTime, default=datetime.utcnow)
    
    detalle_backend = relationship("DetalleBackend", back_populates="proyecto", cascade="all, delete-orphan")
    detalle_frontend = relationship("DetalleFrontend", back_populates="proyecto", cascade="all, delete-orphan")
    detalle_movil = relationship("DetalleMovil", back_populates="proyecto", cascade="all, delete-orphan")
    detalle_tags = relationship("ProyectosTags", back_populates="proyecto", cascade="all, delete-orphan")

class ProyectosTags(Base):
    __tablename__ = "ProyectosTags"
    
    id = Column(Integer, primary_key=True, index=True)
    Tag = Column(String(200))
    proyecto_id = Column(Integer, ForeignKey("Proyectos.id"))
    proyecto = relationship("Proyectos", back_populates="detalle_tags")

class DetalleBackend(Base):
    __tablename__ = "DetalleBackend"
    
    id = Column(Integer, primary_key=True, index=True)
    Repositorio = Column(String(200))
    Framework = Column(String(100))
    Lenguaje = Column(String(100))  # Corregí "Lenguage" a "Lenguaje"
    BaseDatos = Column(String(100))
    Alojamiento = Column(String(100))
    SO = Column(String(100))
    Urls = Column(Text)  # Cambiado a Text para URLs largas
    ServidorWeb = Column(String(100))
    proyecto_id = Column(Integer, ForeignKey("Proyectos.id"))
    
    proyecto = relationship("Proyectos", back_populates="detalle_backend")

class DetalleFrontend(Base):  # Cambiado de "Fronted" a "Frontend"
    __tablename__ = "DetalleFrontend"
    
    id = Column(Integer, primary_key=True, index=True)
    Repositorio = Column(String(200))
    Framework = Column(String(100))
    Lenguaje = Column(String(100))
    Alojamiento = Column(String(100))
    SO = Column(String(100))
    Urls = Column(Text)
    ServidorWeb = Column(String(100))
    proyecto_id = Column(Integer, ForeignKey("Proyectos.id"))
    
    proyecto = relationship("Proyectos", back_populates="detalle_frontend")

class DetalleMovil(Base):
    __tablename__ = "DetalleMovil"
    
    id = Column(Integer, primary_key=True, index=True)
    Repositorio = Column(String(200))
    Framework = Column(String(100))
    Lenguaje = Column(String(100))
    VersionAndroid = Column(String(100))
    VersioniOS = Column(String(100))
    EnlaceDescarga = Column(Text)  # Text para enlaces largos
    proyecto_id = Column(Integer, ForeignKey("Proyectos.id"))
    
    proyecto = relationship("Proyectos", back_populates="detalle_movil")