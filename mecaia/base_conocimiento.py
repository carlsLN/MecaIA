"""Acceso a la base de conocimiento verificada (archivos JSON en conocimiento/)."""
import json
import re
from functools import lru_cache
from pathlib import Path

from .texto import normalizar

CARPETA = Path(__file__).parent / "conocimiento"


@lru_cache
def vehiculos() -> dict[str, dict]:
    return _cargar(CARPETA / "vehiculos")


@lru_cache
def procedimientos() -> dict[str, dict]:
    return _cargar(CARPETA / "procedimientos")


def _cargar(carpeta: Path) -> dict[str, dict]:
    datos = {}
    for archivo in sorted(carpeta.glob("*.json")):
        item = json.loads(archivo.read_text(encoding="utf-8"))
        datos[item["id"]] = item
    return datos


def buscar_vehiculo(consulta: str, anio: int | None = None) -> list[dict]:
    """Devuelve los vehículos cuyo alias aparece en la consulta.

    Si hay varios candidatos (p. ej. "kawasaki 400"), el agente debe preguntar cuál es.
    """
    texto = normalizar(consulta)
    candidatos = []
    for v in vehiculos().values():
        alias = [normalizar(a) for a in v["alias"]]
        if any(re.search(rf"\b{re.escape(a)}\b", texto) for a in alias):
            if anio is None or v["anios"][0] <= anio <= v["anios"][1]:
                candidatos.append(v)
    return candidatos


def obtener_vehiculo(vehiculo_id: str) -> dict | None:
    return vehiculos().get(vehiculo_id)


def buscar_procedimiento(consulta: str) -> dict | None:
    texto = normalizar(consulta)
    mejor, puntaje_mejor = None, 0
    for p in procedimientos().values():
        puntaje = sum(1 for k in p["palabras_clave"] if normalizar(k) in texto)
        if puntaje > puntaje_mejor:
            mejor, puntaje_mejor = p, puntaje
    return mejor


def obtener_procedimiento(procedimiento_id: str) -> dict | None:
    return procedimientos().get(procedimiento_id)
