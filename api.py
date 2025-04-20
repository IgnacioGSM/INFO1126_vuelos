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
    
@app.get("/vuelos/total")   # Endpoint para obtener el total de vuelos
def obtener_total_vuelos_lista(db:Session = Depends(get_db)):
    try:
        lista_vuelos = ListaVuelos(db)
        lista_vuelos.cargar_db()
        return {"total de vuelos en la lista": len(lista_vuelos)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/vuelos/proximo") # Endpoint para el primer vuelo de la lista
def obtener_proximo_vuelo(db:Session = Depends(get_db)):
    try:
        lista_vuelos = ListaVuelos(db)
        lista_vuelos.cargar_db()
        vuelo = lista_vuelos.obtener_primero()
        if vuelo is None:
            raise HTTPException(status_code=404, detail="No hay vuelos en la lista")
        return {"proximo vuelo": vuelo}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@app.get("/vuelos/ultimo") # Endpoint para el último vuelo de la lista
def obtener_ultimo_vuelo(db:Session = Depends(get_db)):
    try:
        lista_vuelos = ListaVuelos(db)
        lista_vuelos.cargar_db()
        vuelo = lista_vuelos.obtener_ultimo()
        if vuelo is None:
            raise HTTPException(status_code=404, detail="No hay vuelos en la lista")
        return {"ultimo vuelo": vuelo}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/vuelos/insertar/frente")    # Endpoint para insertar un vuelo al frente de la lista
def insertar_frente(codigo:str, db:Session = Depends(get_db)):
    try:
        vuelo = db.query(Vuelo).filter(Vuelo.codigo == codigo).first()
        if vuelo is None:
            raise HTTPException(status_code=404, detail="Vuelo no encontrado")
        
        # Verificar si el vuelo ya está en la lista
        vuelo_lista = db.query(ListaVueloDB).filter(ListaVueloDB.codigo_vuelo == codigo).first()
        if vuelo_lista:
            raise HTTPException(status_code=400, detail="El vuelo ya está en la lista")
        
        lista_vuelos = ListaVuelos(db)
        lista_vuelos.cargar_db()
        lista_vuelos.insertar_frente(vuelo)
        return {"mensaje": "Vuelo insertado al frente de la lista"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    
@app.post("/vuelos/insertar/final")   # Endpoint para insertar un vuelo al final de la lista
def insertar_final(codigo:str, db:Session = Depends(get_db)):
    try:
        vuelo = db.query(Vuelo).filter(Vuelo.codigo == codigo).first()
        if vuelo is None:
            raise HTTPException(status_code=404, detail="Vuelo no encontrado")
        
        # Verificar si el vuelo ya está en la lista
        vuelo_lista = db.query(ListaVueloDB).filter(ListaVueloDB.codigo_vuelo == codigo).first()
        if vuelo_lista:
            raise HTTPException(status_code=400, detail="El vuelo ya está en la lista")
        
        lista_vuelos = ListaVuelos(db)
        lista_vuelos.cargar_db()
        lista_vuelos.insertar_final(vuelo)
        return {"mensaje": "Vuelo insertado al final de la lista"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/vuelos/insertar")   # Insertar en una posicion específica
def insertar_vuelo(codigo:str, posicion:int, db:Session = Depends(get_db)):
    try:
        vuelo = db.query(Vuelo).filter(Vuelo.codigo == codigo).first()
        if vuelo is None:
            raise HTTPException(status_code=404, detail="Vuelo no encontrado")
        
        # Verificar si el vuelo ya está en la lista
        vuelo_lista = db.query(ListaVueloDB).filter(ListaVueloDB.codigo_vuelo == codigo).first()
        if vuelo_lista:
            raise HTTPException(status_code=400, detail="El vuelo ya está en la lista")
        
        lista_vuelos = ListaVuelos(db)
        lista_vuelos.cargar_db()
        nodo_referencia = lista_vuelos.obtener_nodo(posicion)   # El nodo que estaba en esa posicion antes de la inserción
        if nodo_referencia is None:
            raise HTTPException(status_code=404, detail="Posición no válida en la lista")
        lista_vuelos.insertar_entre(vuelo, nodo_referencia._anterior, nodo_referencia, db)

        return {"mensaje": "Vuelo insertado en la posición especificada"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    
@app.get("/vuelos/lista") # Endpoint para obtener la lista de vuelos
def obtener_lista_vuelos(db:Session = Depends(get_db)):
    try:
        lista_vuelos = ListaVuelos(db)
        lista_vuelos.cargar_db()
        return {"lista de vuelos": str(lista_vuelos)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/vuelos/lista/{posicion}") # Endpoint para obtener un vuelo específico de la lista
def obtener_vuelo_lista(posicion:int, db:Session = Depends(get_db)):
    try:
        lista_vuelos = ListaVuelos(db)
        lista_vuelos.cargar_db()
        vuelo = lista_vuelos.obtener_nodo(posicion)
        if vuelo is None:
            raise HTTPException(status_code=404, detail="Vuelo no encontrado en la lista")
        return {"vuelo en la posición": posicion, "vuelo": vuelo._vuelo}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))