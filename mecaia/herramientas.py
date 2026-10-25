"""Herramientas del agente: consultan la base verificada o leen y escriben la memoria."""
import json

from . import base_conocimiento as bc
from . import seguridad
from .memoria import Memoria


class Herramientas:
    def __init__(self, memoria: Memoria, usuario: str):
        self.memoria = memoria
        self.usuario = usuario

    def ejecutar(self, nombre: str, entrada: dict) -> str:
        metodo = getattr(self, nombre, None)
        if metodo is None or nombre.startswith("_") or nombre == "ejecutar":
            raise ValueError(f"Herramienta desconocida: {nombre}")
        return json.dumps(metodo(**entrada), ensure_ascii=False)

    def revisar_seguridad(self, descripcion: str) -> dict:
        return seguridad.evaluar(descripcion).como_dict()

    def buscar_vehiculo(self, descripcion: str, anio: int | None = None) -> dict:
        candidatos = bc.buscar_vehiculo(descripcion, anio)
        return {
            "candidatos": [
                {"vehiculo_id": v["id"], "marca": v["marca"], "modelo": v["modelo"],
                 "anios": v["anios"], "tipo": v["tipo"]}
                for v in candidatos
            ],
            "nota": "Sin coincidencias en la base: no inventes datos." if not candidatos else
                    "Varios candidatos: pregunta al usuario cuál es." if len(candidatos) > 1 else "",
        }

    def obtener_datos_vehiculo(self, vehiculo_id: str) -> dict:
        return bc.obtener_vehiculo(vehiculo_id) or {"error": f"No existe {vehiculo_id} en la base"}

    def buscar_procedimiento(self, consulta: str) -> dict:
        return bc.buscar_procedimiento(consulta) or {"error": "No hay un procedimiento cargado para eso"}

    def mis_vehiculos(self) -> dict:
        return {"vehiculos": self.memoria.vehiculos(self.usuario)}

    def guardar_vehiculo(self, vehiculo_id: str, anio: int | None = None,
                         km: int | None = None, apodo: str | None = None) -> dict:
        if not bc.obtener_vehiculo(vehiculo_id):
            return {"error": f"No existe {vehiculo_id} en la base"}
        self.memoria.guardar_vehiculo(self.usuario, vehiculo_id, anio, km, apodo)
        return {"ok": True}

    def registrar_mantencion(self, vehiculo_id: str, tipo: str,
                             km: int | None = None, notas: str | None = None) -> dict:
        self.memoria.registrar_mantencion(self.usuario, vehiculo_id, tipo, km, notas)
        return {"ok": True}

    def derivar_a_mecanico(self, motivo: str, urgencia: str) -> dict:
        consejo = {
            "inmediata": "No uses el vehículo. Si es seguro, llama a una grúa o asistencia en ruta.",
            "pronto": "Úsalo lo mínimo y con precaución hasta que lo revisen, idealmente esta semana.",
            "cuando_pueda": "Agenda una revisión en tu próxima mantención.",
        }[urgencia]
        return {
            "motivo": motivo,
            "que_hacer": consejo,
            "que_decirle_al_mecanico": "Describe cuándo empezó, en qué condiciones ocurre "
                                       "(frío/caliente, al frenar, a cierta velocidad) y cualquier ruido u olor.",
        }
