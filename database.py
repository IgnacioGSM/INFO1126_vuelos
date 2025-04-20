from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from models import Base

# Configuracion del motor y la sesion de SQLAlchemy
engine = create_engine("sqlite:///vuelos.db")
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():   # Entrega una sesion de SQLAlchemy para interactuar con la base de datos
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_database():
    # Crear todas las tablas en la base de datos
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    create_database()  # Crear la base de datos y las tablas al ejecutar este script directamente