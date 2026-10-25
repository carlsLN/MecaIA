"""Chequeo de seguridad: corre en código antes de cualquier respuesta."""
import json
import re
from dataclasses import dataclass, field
from functools import lru_cache

from .base_conocimiento import CARPETA
from .texto import normalizar


@dataclass
class ResultadoSeguridad:
    nivel: str  # "ok", "precaucion" o "detener"
    motivos: list[str] = field(default_factory=list)

    def como_dict(self) -> dict:
        return {"nivel": self.nivel, "motivos": self.motivos}


@lru_cache
def _reglas() -> dict:
    return json.loads((CARPETA / "seguridad.json").read_text(encoding="utf-8"))


def evaluar(mensaje: str) -> ResultadoSeguridad:
    texto = normalizar(mensaje)
    for nivel in ("detener", "precaucion"):
        motivos = [r["motivo"] for r in _reglas()[nivel] if re.search(r["patron"], texto)]
        if motivos:
            return ResultadoSeguridad(nivel, sorted(set(motivos)))
    return ResultadoSeguridad("ok")
