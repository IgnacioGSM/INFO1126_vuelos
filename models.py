from sqlalchemy import Column, String, DateTime, Enum, Integer, ForeignKey
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Vuelo(Base):
    __tablename__ = "vuelos"

    codigo = Column(String, primary_key=True)  # Código único para cada vuelo
    estado = Column(Enum("programado", "emergencia", "retrasado", name="estado_vuelo"))
    hora = Column(DateTime)
    origen = Column(String)
    destino = Column(String)

# Orden de los vuelos
class ListaVueloDB(Base):
    __tablename__ = "lista_vuelos"

    id = Column(Integer, primary_key=True, autoincrement=True)  # Índice interno de la tabla
    codigo_vuelo = Column(String, ForeignKey("vuelos.codigo"), unique=True)
    orden = Column(Integer, nullable=False, unique=True)    # Luego la lista se construira ordenando en base a este campo