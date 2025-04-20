from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Vuelo, ListaVueloDB
from ListaVuelos import ListaVuelos
from datetime import datetime

app = FastAPI()

@app.post("/vuelos/crear")  # Endpoint para crear un vuelo
def crear_vuelo(codigo:str, estado:str, año:int, mes:int, dia:int, hora:int, minutos:int, origen:str, destino:str, db:Session = Depends(get_db)):
    try:
        # Validar unicidad del código de vuelo
        vuelo_existente = db.query(Vuelo).filter(Vuelo.codigo == codigo).first()
        if vuelo_existente:
            raise HTTPException(status_code=400, detail="El código de vuelo ya existe")

        # Validar el estado del vuelo
        if estado.lower() not in ["programado", "emergencia", "retrasado"]:
            raise HTTPException(status_code=400, detail="Estado de vuelo inválido")

        fecha = datetime(año, mes, dia, hora, minutos)  # Crear objeto datetime
        nuevo_vuelo = Vuelo(codigo=codigo, estado=estado.lower(), hora=fecha, origen=origen, destino=destino)
        db.add(nuevo_vuelo)
        db.commit()
        db.refresh(nuevo_vuelo)
        return {"mensaje": "Vuelo creado exitosamente", "vuelo": nuevo_vuelo}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    
@app.delete("/vuelos/eliminar/{codigo}")  # Endpoint para eliminar un vuelo
def eliminar_vuelo(codigo:str, db:Session = Depends(get_db)):
    try:
        vuelo = db.query(Vuelo).filter(Vuelo.codigo == codigo).first()
        if vuelo is None:
            raise HTTPException(status_code=404, detail="Vuelo no encontrado")
        
        # Eliminar el vuelo de la base de datos
        db.delete(vuelo)
        db.commit()
        return {"mensaje": "Vuelo eliminado exitosamente"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/vuelos") # Endpoint para obtener todos los vuelos
def obtener_vuelos(db:Session = Depends(get_db)):
    try:
        vuelos = db.query(Vuelo).all()
        return {"vuelos": vuelos}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))