# modelos.py

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, LargeBinary
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

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
    velocidad_maxima = Column(Float)
    velocidad_lineal = Column(Float)
    velocidad_angular = Column(Float)
    tasa_muestreo = Column(Float)
    campo_vision = Column(Float)
    resolucion = Column(Float)
    filtro_ruido = Column(Float)

    metodo_filtrado = Column(String(100))
    reduccion_ruido = Column(String(100))
    compensacion_movimiento = Column(String(100))
    metodo_procesamiento = Column(String(100))
    tolerancia = Column(Float)
    iteraciones = Column(Integer)
    correspondencia = Column(Float)

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
    nube_datos = Column(LargeBinary)
    parametroID = Column(Integer, ForeignKey("parametros.parametroID"), nullable=True)
    fecha = Column(DateTime, default=datetime.utcnow)