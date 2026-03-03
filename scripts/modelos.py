# modelos.py

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, LargeBinary
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime
from sqlalchemy.dialects.mysql import LONGBLOB

Base = declarative_base()

# ---------------------
# Modelo Usuario
# ---------------------
class Usuario(Base):
    __tablename__ = 'usuarios'

    userID = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(100))
    email = Column(String(100))
    username = Column(String(50), unique=True, nullable=False)
    password = Column(String(100), nullable=False)
    rol = Column(String(50))
    user_status = Column(String(50))

    parametros = relationship("Parametro", back_populates="usuario", cascade="all, delete-orphan")

# ---------------------
# Modelo Parametro
# ---------------------
class Parametro(Base):
    __tablename__ = 'parametros'

    parametroID = Column(Integer, primary_key=True, autoincrement=True)
    usuario_id = Column(Integer, ForeignKey('usuarios.userID'), nullable=True)
    nombre_preset = Column(String(100))
    descripcion = Column(String(255))
    fecha = Column(DateTime, default=datetime.utcnow)

    # Campos técnicos    

    # Telemetria
    velocidad_lineal = Column(Float)
    velocidad_angular = Column(Float)

    # Captura de nubes
    num_steps = Column(Integer)
    max_range = Column(Integer)
    min_range = Column(Integer)
    fov_angel = Column(Integer)
    prefijo = Column(String(100))

    # preprocesamiento
    vecinos = Column(Integer)
    dev_std = Column(Integer)
    z_max = Column(Integer)
    z_min = Column(Integer)
    voxel_size = Column(Float)

    # procesamiento
    num_planos = Column(Integer)
    distancia = Column(Float)
    iteraciones = Column(Integer)

    # alineacion
    voxel_size_ali = Column(Float)
    normal_rad = Column(Float)
    normal_max_nn = Column(Integer)
    fpfh_rad = Column(Integer)
    fpfh_max_nn = Column(Integer)    

    usuario = relationship("Usuario", back_populates="parametros")

# ---------------------
# Modelo Nube de Puntos
# ---------------------
class NubeDePuntos(Base):
    __tablename__ = 'nubes_de_puntos'

    nubeID = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(100))
    descripcion = Column(String(255))
    archivo_tipo = Column(String(10))
    nombre_archivo = Column(String(255))    
    nube_datos = Column(LONGBLOB)
    parametroID = Column(Integer, ForeignKey("parametros.parametroID"), nullable=True)
    fecha = Column(DateTime, default=datetime.utcnow)