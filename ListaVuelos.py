from sqlalchemy.orm import Session
from models import Vuelo, ListaVuelo

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
    
    def _insertar_entre(self, info: Vuelo, anterior, siguiente, db:Session):
        nuevo_nodo = self._Nodo(info, anterior, siguiente)
        anterior._siguiente = nuevo_nodo
        siguiente._anterior = nuevo_nodo
        self._size += 1

        # Registrar el orden del vuelo en la base de datos

        # Si se añade al primero:
        if anterior == self._header:
            try:
                # Aumentar el orden de todos los vuelos en la lista
                db.query(ListaVuelo).filter(ListaVuelo.orden >= 1).update({ListaVuelo.orden: ListaVuelo.orden + 1})
                # Agregar el nuevo vuelo al inicio de la lista
                nuevo_vuelo = ListaVuelo(codigo_vuelo=info.codigo, orden=1)
                db.add(nuevo_vuelo)
                db.commit()
                db.refresh(nuevo_vuelo)  # Refrescar el objeto para obtener el ID generado
            except Exception as e:
                db.rollback()
                raise e
        
        return nuevo_nodo
    
    def _eliminar(self, nodo):
        # Se puede eliminar cualquier nodo menos el header y el trailer, esos son delimitadores
        if nodo == self._header or nodo == self._trailer:
            raise ValueError("No se puede eliminar el nodo header o trailer")
            # Esto no debería ocurrir, pero se deja por si acaso
            # En la api no deberían aparecer estos nodos
        anterior = nodo._anterior
        siguiente = nodo._siguiente
        anterior._siguiente = siguiente
        siguiente._anterior = anterior
        self._size -= 1

        info = nodo._vuelo  # Guardamos la info del vuelo antes de eliminar el nodo
        # Eliminar 