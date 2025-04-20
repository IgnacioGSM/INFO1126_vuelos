from sqlalchemy.orm import Session
from models import Vuelo, ListaVueloDB

class ListaVuelos:
    
    class _Nodo:
        # slots optimiza memoria y hace que el objeto sea inmutable, no se pueden crear nuevos atributos
        __slots__ = "_vuelo", "_anterior", "_siguiente"

        def __init__(self, vuelo:Vuelo, anterior, siguiente):
            self._vuelo = vuelo # Info del vuelo, usa el modelo de la base de datos
            self._anterior = anterior
            self._siguiente = siguiente
    
    def __init__(self, db:Session):
        # Estos nodos son los extremos de la lista, no contienen información de vuelos
        # pero son necesarios para la implementación de la lista doblemente enlazada
        self._header = self._Nodo(None, None, None)  # Nodo cabecera
        self._trailer = self._Nodo(None, None, None)  # Nodo final
        self._header._siguiente = self._trailer
        self._trailer._anterior = self._header
        self._size = 0
        self._db = db  # Sesion de SQLAlchemy para interactuar con la base de datos
    
    def __len__(self):  # Longitud
        return self._size
    
    def esta_vacio(self):
        return self._size == 0
    
    def cargar_db(self):
        # Cargar la lista de vuelos desde la base de datos
        vuelos_lista = self._db.query(ListaVueloDB).order_by(ListaVueloDB.orden).all()
        for vuelo in vuelos_lista:
            # Obtener el vuelo completo desde la base de datos
            vuelo_completo = self._db.query(Vuelo).filter(Vuelo.codigo == vuelo.codigo_vuelo).first()
            if vuelo_completo:
                nuevo_nodo = self._Nodo(vuelo_completo, self._trailer._anterior, self._trailer)
                self._trailer._anterior._siguiente = nuevo_nodo
                self._trailer._anterior = nuevo_nodo
                self._size += 1

    def obtener_primero(self):
        # Obtener el primer vuelo de la lista
        if self.esta_vacio():
            return None
        return self._header._siguiente._vuelo

    def obtener_ultimo(self):
        # Obtener el último vuelo de la lista
        if self.esta_vacio():
            return None
        return self._trailer._anterior._vuelo
    
    def obtener_nodo(self, posicion:int):
        # Obtener un nodo en una posición específica
        if posicion < 0 or posicion >= self._size:
            raise IndexError("Posición fuera de rango")
        nodo_actual = self._header._siguiente
        for i in range(posicion):   ## Iterar hasta la posición deseada
            nodo_actual = nodo_actual._siguiente
        return nodo_actual
    
    def insertar_entre(self, info: Vuelo, anterior, siguiente, db:Session):
        nuevo_nodo = self._Nodo(info, anterior, siguiente)
        anterior._siguiente = nuevo_nodo
        siguiente._anterior = nuevo_nodo
        self._size += 1

        # Registrar el orden del vuelo en la base de datos

        # Si se añade al primero:
        if anterior == self._header:
            try:
                # Aumentar el orden de todos los vuelos en la lista
                vuelos_a_reaordenar = db.query(ListaVueloDB).filter(ListaVueloDB.orden >= 1).order_by(ListaVueloDB.orden.desc()).all()
                for vuelo in vuelos_a_reaordenar:
                    vuelo.orden += 1
                    db.commit()
                # Agregar el nuevo vuelo al inicio de la lista
                nuevo_vuelo = ListaVueloDB(codigo_vuelo=info.codigo, orden=1)
                db.add(nuevo_vuelo)
                db.commit()
                db.refresh(nuevo_vuelo)  # Refrescar el objeto para obtener el ID generado
            except Exception as e:
                db.rollback()
                raise e
        
        # Si está en medio:
        elif siguiente != self._trailer:
            try:
                # Encontrar el siguiente vuelo en la base de datos
                siguiente_vuelo_db = db.query(ListaVueloDB).filter(ListaVueloDB.codigo_vuelo == siguiente._vuelo.codigo).first()
                posicion_db = siguiente_vuelo_db.orden
                if siguiente_vuelo_db:
                    # Aumentar el orden de todos los vuelos en la lista
                    vuelos_a_reaordenar = db.query(ListaVueloDB).filter(ListaVueloDB.orden >= posicion_db).order_by(ListaVueloDB.orden.desc()).all()
                    for vuelo in vuelos_a_reaordenar:
                        vuelo.orden += 1
                        db.commit()
                    # Agregar el nuevo vuelo a la lista
                    nuevo_vuelo = ListaVueloDB(codigo_vuelo=info.codigo, orden=posicion_db)
                    db.add(nuevo_vuelo)
                    db.commit()
                    db.refresh(nuevo_vuelo)
                else:
                    raise ValueError("Vuelo siguiente no encontrado en la base de datos")
            except Exception as e:
                db.rollback()
                raise e
        
        # Si se añade al último:
        elif siguiente == self._trailer:
            try:
                # Obtener el último vuelo en la base de datos
                ultimo_vuelo_db = db.query(ListaVueloDB).order_by(ListaVueloDB.orden.desc()).first()
                if ultimo_vuelo_db:
                    nuevo_orden = ultimo_vuelo_db.orden + 1
                    nuevo_vuelo = ListaVueloDB(codigo_vuelo=info.codigo, orden=nuevo_orden)
                    db.add(nuevo_vuelo)
                    db.commit()
                    db.refresh(nuevo_vuelo)
                else:   # Lista vacia
                    nuevo_vuelo = ListaVueloDB(codigo_vuelo=info.codigo, orden=1)
                    db.add(nuevo_vuelo)
                    db.commit()
                    db.refresh(nuevo_vuelo)
            except Exception as e:
                db.rollback()
                raise e
        
        return nuevo_nodo
    
    def extraer(self, nodo):
        # Se puede extraer cualquier nodo menos el header y el trailer, esos son delimitadores
        if nodo == self._header or nodo == self._trailer:
            raise ValueError("No seextraer el nodo header o trailer")
            # Esto no debería ocurrir, pero se deja por si acaso
            # En la api no deberían aparecer estos nodos
        anterior = nodo._anterior
        siguiente = nodo._siguiente
        anterior._siguiente = siguiente
        siguiente._anterior = anterior
        self._size -= 1

        info = nodo._vuelo  # Guardamos la info del vuelo anextraer el nodo

        # Eliminar de la lista en la base de datos
        try:
            # Encontrar el vuelo en la base de datos
            vuelo_db = self._db.query(ListaVueloDB).filter(ListaVueloDB.codigo_vuelo == info.codigo).first()
            if vuelo_db:
                # Eliminar el vuelo de la base de datos
                self._db.delete(vuelo_db)
                self._db.commit()
                # Actualizar el orden de los vuelos restantes
                vuelos_a_reaordenar = self._db.query(ListaVueloDB).filter(ListaVueloDB.orden > vuelo_db.orden).order_by(ListaVueloDB.orden.asc()).all()
                for vuelo in vuelos_a_reaordenar:
                    vuelo.orden -= 1
                    self._db.commit()
                return {"vuelo eliminado de la cola": info}
            else:
                raise ValueError("Vuelo no encontrado en la base de datos")
        except Exception as e:
            self._db.rollback()
            raise e
    
    def insertar_frente(self, vuelo:Vuelo):
        # Insertar un vuelo al frente de la lista
        self.insertar_entre(vuelo, self._header, self._header._siguiente, self._db)
    
    def insertar_final(self, vuelo:Vuelo):
        # Insertar un vuelo al final de la lista
        self.insertar_entre(vuelo, self._trailer._anterior, self._trailer, self._db)

    def __str__(self):
        # Representación de la lista como una cadena
        nodos = []
        nodo_actual = self._header._siguiente
        while nodo_actual != self._trailer:
            nodos.append(nodo_actual._vuelo.codigo)
            nodo_actual = nodo_actual._siguiente
        return "inicio " + " <-> ".join(nodos) + " <-> fin"