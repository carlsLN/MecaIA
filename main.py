"""Chat de MecaIA en la terminal.

Uso:
    python main.py                 # usa Claude si hay ANTHROPIC_API_KEY; si no, modo demo
    python main.py --demo          # fuerza el modo demo (sin costo)
    python main.py --ver-plan      # muestra las decisiones del agente en cada turno
    python main.py --grafo         # imprime el diagrama del grafo (Mermaid)
"""
import argparse
import os
import sqlite3

from langgraph.checkpoint.sqlite import SqliteSaver

from mecaia.grafo import MecaIA, crear_llm
from mecaia.memoria import Memoria


def main() -> None:
    parser = argparse.ArgumentParser(description="MecaIA: asistente de mantención de autos y motos")
    parser.add_argument("--demo", action="store_true", help="modo sin API key")
    parser.add_argument("--usuario", default="invitado")
    parser.add_argument("--conversacion", default="principal", help="id de la conversación (memoria corta)")
    parser.add_argument("--ver-plan", action="store_true")
    parser.add_argument("--grafo", action="store_true")
    args = parser.parse_args()

    usar_llm = not args.demo and bool(os.environ.get("ANTHROPIC_API_KEY"))
    if not usar_llm and not args.demo:
        print("(No hay ANTHROPIC_API_KEY: uso el modo demo)\n")

    # Largo plazo: vehículos y mantenciones. Corto plazo: estado de cada conversación.
    memoria = Memoria("mecaia.db")
    checkpointer = SqliteSaver(sqlite3.connect("mecaia_conversaciones.db", check_same_thread=False))
    agente = MecaIA(args.usuario, memoria, crear_llm() if usar_llm else None, checkpointer)

    if args.grafo:
        print(agente.grafo.get_graph().draw_mermaid())
        return

    print("MecaIA: Hola, ¿en qué te ayudo con tu auto o moto? (escribe 'salir' para terminar)")
    while True:
        try:
            texto = input("\nTú: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if texto.lower() in {"salir", "exit", "quit"}:
            break
        if not texto:
            continue
        respuesta = agente.responder(texto, args.conversacion)
        if args.ver_plan:
            print("\n[plan] " + " -> ".join(agente.ultimo_plan))
        print(f"\nMecaIA: {respuesta}")


if __name__ == "__main__":
    main()
