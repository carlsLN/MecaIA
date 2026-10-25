"""Genera evidencias/conversacion_demo.md con una conversación de prueba en modo demo.

Uso: python scripts/generar_evidencias.py
"""
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from mecaia.grafo import MecaIA  # noqa: E402
from mecaia.memoria import Memoria  # noqa: E402

GUION = [
    ("principal", "hola"),
    ("principal", "¿Qué aceite necesito para mi Kawasaki 400?"),
    ("principal", "la ninja"),
    ("principal", "ya cambié el aceite a los 12.000 km"),
    ("principal", "cómo reviso la presión de los neumáticos"),
    ("principal", "mi moto no frena, ¿qué hago?"),
    ("otra", "cambio de aceite"),
    ("otra", "qué aceite lleva un Suzuki Alto"),
    ("otra", "cuánto rinde el estanque de mi Yamaha R3"),
    ("otra", "cada cuánto se cambian las bujías de un auto"),
    ("otra", "cada cuánto cambio las balatas de mi moto"),
    ("otra", "muchas gracias"),
]


def main() -> None:
    memoria = Memoria(":memory:")
    agente = MecaIA("ana", memoria)
    lineas = ["# Conversación de prueba en modo demo", "",
              "Generado con `python scripts/generar_evidencias.py`. Usuario: ana. "
              "La conversación \"otra\" no comparte mensajes con la \"principal\": lo que recuerda "
              "viene de la memoria de largo plazo.", ""]
    actual = None
    for conversacion, texto in GUION:
        if conversacion != actual:
            lineas += [f"## Conversación \"{conversacion}\"", ""]
            actual = conversacion
        respuesta = agente.responder(texto, conversacion)
        lineas += [f"**Usuario:** {texto}", "",
                   f"> Plan del agente: {' → '.join(agente.ultimo_plan)}", "",
                   "**MecaIA:**", "", respuesta, "", "---", ""]
    salida = RAIZ / "evidencias" / "conversacion_demo.md"
    salida.write_text("\n".join(lineas), encoding="utf-8")
    print(f"Escrito {salida}")


if __name__ == "__main__":
    main()
