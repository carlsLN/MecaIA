"""Agente MecaIA como grafo de LangGraph.

Flujo de cada mensaje:

    seguridad ──riesgo──> derivar
        │
    interpretar ──varios modelos o falta el vehículo──> aclarar
        │        ──el usuario cuenta una mantención──> registrar
        │
    responder (modo demo)   o   agente <──> herramientas (modo Claude)

Memoria de corto plazo: el checkpointer de LangGraph guarda el estado de cada conversación
(mensajes, vehículo confirmado, pregunta pendiente). Memoria de largo plazo: la base SQLite de
memoria.py guarda los vehículos y mantenciones de cada usuario entre conversaciones.
"""
import os
import re
from typing import Annotated, TypedDict

from langchain_core.messages import AIMessage, AnyMessage, HumanMessage, SystemMessage
from langchain_core.tools import tool
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import InjectedState, ToolNode, tools_condition

from . import base_conocimiento as bc
from . import respuestas, seguridad
from .herramientas import Herramientas
from .memoria import Memoria
from .texto import normalizar

MODELO = os.environ.get("MECAIA_MODELO", "claude-opus-5-5")

PROMPT_SISTEMA = """Eres MecaIA, un asistente de mantención para personas dueñas de un auto o una moto \
(no para talleres). Respondes en español, claro y cercano, como un amigo que sabe de mecánica.

Reglas, en este orden de prioridad:
1. Seguridad primero. Si hay un riesgo, no des pasos para reparar: explica por qué es peligroso y usa \
derivar_a_mecanico.
2. Usa el vehículo confirmado que aparece en el contexto. Si no hay uno, identifícalo con buscar_vehiculo \
o mis_vehiculos; si hay más de un candidato, pregunta cuál es y no adivines.
3. Nunca inventes datos técnicos. Viscosidad, capacidades, códigos de repuesto, torques y medidas salen \
solo de obtener_datos_vehiculo. Si un dato es null o no está, dilo y sugiere el manual. Si viene con \
"verificado": false, menciónalo brevemente ("dato por confirmar con tu manual").
4. Para tareas de mantención usa buscar_procedimiento y responde con estas secciones: Lo que necesitas, \
Herramientas, Si no tienes las herramientas, Paso a paso, No olvides (p. ej. cambiar el filtro con el \
aceite), Cuándo ir al mecánico.
5. Si el usuario cuenta que hizo una mantención, regístrala con registrar_mantencion.
6. Si la pregunta no es de mecánica de autos o motos, dilo amablemente."""


class Estado(TypedDict, total=False):
    messages: Annotated[list[AnyMessage], add_messages]
    usuario: str
    seguridad: dict
    intencion: str  # "consulta" o "registro"
    procedimiento_id: str | None
    candidatos: list[str]
    vehiculo_id: str | None
    km: int | None
    pendiente: bool  # True si se le hizo una pregunta al usuario y se espera su respuesta
    plan: list[str]  # decisiones tomadas en este turno, para mostrar el razonamiento


def _ultimo_texto(estado: Estado) -> str:
    return next(m.content for m in reversed(estado["messages"]) if isinstance(m, HumanMessage))


def _es_registro(texto: str) -> bool:
    return bool(re.search(r"\b(ya )?(cambie|hice|realice|le hice|le cambie)\b", texto))


def _km(texto: str) -> int | None:
    m = re.search(r"(\d{1,3}(?:[.\s]\d{3})+|\d+)\s*(?:km|kms|kilometros)\b", texto)
    return int(re.sub(r"\D", "", m.group(1))) if m else None


def crear_herramientas(memoria: Memoria) -> list:
    """Herramientas de consulta y escritura para el modelo. El usuario se toma del estado."""

    def h(estado: dict) -> Herramientas:
        return Herramientas(memoria, estado.get("usuario", "invitado"))

    @tool
    def revisar_seguridad(descripcion: str, estado: Annotated[dict, InjectedState]) -> str:
        """Evalúa si lo que describe el usuario es un riesgo. Devuelve nivel ok, precaucion o detener."""
        return h(estado).ejecutar("revisar_seguridad", {"descripcion": descripcion})

    @tool
    def buscar_vehiculo(descripcion: str, estado: Annotated[dict, InjectedState], anio: int | None = None) -> str:
        """Busca vehículos en la base verificada (ej. 'kawasaki 400', 'yaris'). Si hay varios, pregunta cuál."""
        return h(estado).ejecutar("buscar_vehiculo", {"descripcion": descripcion, "anio": anio})

    @tool
    def obtener_datos_vehiculo(vehiculo_id: str, estado: Annotated[dict, InjectedState]) -> str:
        """Especificaciones verificadas de un vehículo: aceite, capacidades, filtro, torques y medidas."""
        return h(estado).ejecutar("obtener_datos_vehiculo", {"vehiculo_id": vehiculo_id})

    @tool
    def buscar_procedimiento(consulta: str, estado: Annotated[dict, InjectedState]) -> str:
        """Procedimiento de mantención: pasos, herramientas, alternativas, recordatorios y cuándo derivar."""
        return h(estado).ejecutar("buscar_procedimiento", {"consulta": consulta})

    @tool
    def mis_vehiculos(estado: Annotated[dict, InjectedState]) -> str:
        """Vehículos guardados del usuario y su historial de mantenciones (memoria de largo plazo)."""
        return h(estado).ejecutar("mis_vehiculos", {})

    @tool
    def guardar_vehiculo(vehiculo_id: str, estado: Annotated[dict, InjectedState], anio: int | None = None,
                         km: int | None = None, apodo: str | None = None) -> str:
        """Guarda o actualiza un vehículo confirmado en la memoria del usuario."""
        return h(estado).ejecutar("guardar_vehiculo",
                                  {"vehiculo_id": vehiculo_id, "anio": anio, "km": km, "apodo": apodo})

    @tool
    def registrar_mantencion(vehiculo_id: str, tipo: str, estado: Annotated[dict, InjectedState],
                             km: int | None = None, notas: str | None = None) -> str:
        """Registra una mantención hecha por el usuario (ej. tipo 'cambio_aceite')."""
        return h(estado).ejecutar("registrar_mantencion",
                                  {"vehiculo_id": vehiculo_id, "tipo": tipo, "km": km, "notas": notas})

    @tool
    def derivar_a_mecanico(motivo: str, urgencia: str, estado: Annotated[dict, InjectedState]) -> str:
        """Deriva a un mecánico cuando el caso excede lo seguro. urgencia: inmediata, pronto o cuando_pueda."""
        return h(estado).ejecutar("derivar_a_mecanico", {"motivo": motivo, "urgencia": urgencia})

    return [revisar_seguridad, buscar_vehiculo, obtener_datos_vehiculo, buscar_procedimiento,
            mis_vehiculos, guardar_vehiculo, registrar_mantencion, derivar_a_mecanico]


def construir_grafo(memoria: Memoria, llm=None, checkpointer=None):
    """Arma el grafo. Sin llm funciona en modo demo (respuestas desde la base, sin costo)."""
    herramientas = crear_herramientas(memoria)

    def nodo_seguridad(estado: Estado) -> dict:
        r = seguridad.evaluar(_ultimo_texto(estado))
        detalle = f" ({', '.join(r.motivos)})" if r.motivos else ""
        return {"seguridad": r.como_dict(), "plan": [f"Seguridad: {r.nivel}{detalle}"]}

    def nodo_interpretar(estado: Estado) -> dict:
        texto = normalizar(_ultimo_texto(estado))
        plan = list(estado["plan"])
        pendiente = estado.get("pendiente", False)

        procedimiento = bc.buscar_procedimiento(texto)
        intencion = "registro" if _es_registro(texto) else "consulta"
        if pendiente:
            procedimiento = procedimiento or bc.obtener_procedimiento(estado.get("procedimiento_id") or "")
            if estado.get("intencion") == "registro":
                intencion = "registro"
        km = _km(texto) or (estado.get("km") if pendiente else None)

        candidatos = bc.buscar_vehiculo(texto)
        origen = "mencionado en el mensaje"
        if not candidatos and pendiente and estado.get("candidatos"):
            candidatos = respuestas.elegir(texto, [bc.obtener_vehiculo(i) for i in estado["candidatos"]])
            origen = "respuesta a la pregunta anterior"
        if not candidatos and estado.get("vehiculo_id"):
            candidatos = [bc.obtener_vehiculo(estado["vehiculo_id"])]
            origen = "memoria de corto plazo (esta conversación)"
        if not candidatos:
            guardados = memoria.vehiculos(estado["usuario"])
            if len(guardados) == 1:
                candidatos = [bc.obtener_vehiculo(guardados[0]["vehiculo_id"])]
                origen = "memoria de largo plazo (vehículo guardado)"

        vehiculo_id = candidatos[0]["id"] if len(candidatos) == 1 else None
        if vehiculo_id:
            memoria.guardar_vehiculo(estado["usuario"], vehiculo_id)
            plan.append(f"Vehículo: {vehiculo_id}, {origen}")
        else:
            plan.append(f"Vehículo: {len(candidatos)} candidatos")
        plan.append(f"Intención: {intencion}; procedimiento: {procedimiento['id'] if procedimiento else 'ninguno'}")
        return {
            "intencion": intencion,
            "procedimiento_id": procedimiento["id"] if procedimiento else None,
            "candidatos": [v["id"] for v in candidatos],
            "vehiculo_id": vehiculo_id,
            "km": km,
            "pendiente": False,
            "plan": plan,
        }

    def ruta_interpretar(estado: Estado) -> str:
        if len(estado["candidatos"]) > 1:
            return "aclarar"
        if estado["intencion"] == "registro":
            return "registrar" if estado["vehiculo_id"] else "aclarar"
        if llm is not None:
            return "agente"
        if estado["procedimiento_id"] and not estado["vehiculo_id"]:
            return "aclarar"
        return "responder"

    def nodo_aclarar(estado: Estado) -> dict:
        candidatos = [bc.obtener_vehiculo(i) for i in estado["candidatos"]]
        return {"messages": [AIMessage(respuestas.pedir_vehiculo(candidatos))], "pendiente": True,
                "plan": estado["plan"] + ["Decisión: preguntar antes de dar datos"]}

    def nodo_derivar(estado: Estado) -> dict:
        return {"messages": [AIMessage(respuestas.derivacion(estado["seguridad"]["motivos"]))],
                "plan": estado["plan"] + ["Decisión: derivar a mecánico, sin pasos de reparación"]}

    def nodo_registrar(estado: Estado) -> dict:
        tipo = estado["procedimiento_id"] or "mantencion"
        memoria.registrar_mantencion(estado["usuario"], estado["vehiculo_id"], tipo, estado.get("km"))
        v = bc.obtener_vehiculo(estado["vehiculo_id"])
        procedimiento = bc.obtener_procedimiento(tipo)
        nombre = procedimiento["nombre"] if procedimiento else "Mantención"
        return {"messages": [AIMessage(respuestas.registro_confirmado(v, tipo, nombre, estado.get("km")))],
                "plan": estado["plan"] + ["Decisión: guardar la mantención en memoria de largo plazo"]}

    def nodo_responder(estado: Estado) -> dict:
        procedimiento = bc.obtener_procedimiento(estado["procedimiento_id"] or "")
        if procedimiento is None:
            texto = respuestas.SIN_PROCEDIMIENTO
        else:
            v = bc.obtener_vehiculo(estado["vehiculo_id"])
            texto = respuestas.formatear(procedimiento, v, _ultimo_cambio(estado))
            if estado["seguridad"]["nivel"] == "precaucion":
                texto = f"Ojo: {', '.join(estado['seguridad']['motivos']).lower()}. Ve con cuidado.\n\n{texto}"
        return {"messages": [AIMessage(texto)], "plan": estado["plan"] + ["Decisión: responder desde la base"]}

    def _ultimo_cambio(estado: Estado) -> dict | None:
        for v in memoria.vehiculos(estado["usuario"]):
            if v["vehiculo_id"] == estado["vehiculo_id"]:
                return next((m for m in v["mantenciones"] if m["tipo"] == "cambio_aceite"), None)
        return None

    def nodo_agente(estado: Estado) -> dict:
        contexto = (f"\n\nContexto de este turno (calculado por el sistema): usuario={estado['usuario']}, "
                    f"seguridad={estado['seguridad']}, vehiculo_confirmado={estado.get('vehiculo_id')}, "
                    f"candidatos={estado.get('candidatos')}, procedimiento={estado.get('procedimiento_id')}")
        respuesta = llm.bind_tools(herramientas).invoke(
            [SystemMessage(PROMPT_SISTEMA + contexto)] + estado["messages"])
        nombres = [c["name"] for c in respuesta.tool_calls]
        paso = f"Agente: usa {', '.join(nombres)}" if nombres else "Agente: responde"
        return {"messages": [respuesta], "plan": estado["plan"] + [paso]}

    g = StateGraph(Estado)
    g.add_node("seguridad", nodo_seguridad)
    g.add_node("interpretar", nodo_interpretar)
    g.add_node("aclarar", nodo_aclarar)
    g.add_node("derivar", nodo_derivar)
    g.add_node("registrar", nodo_registrar)
    g.add_node("responder", nodo_responder)
    g.add_edge(START, "seguridad")
    g.add_conditional_edges("seguridad", lambda e: "derivar" if e["seguridad"]["nivel"] == "detener"
                            else "interpretar", ["derivar", "interpretar"])
    destinos = ["aclarar", "registrar", "responder"]
    if llm is not None:
        g.add_node("agente", nodo_agente)
        g.add_node("herramientas", ToolNode(herramientas))
        g.add_conditional_edges("agente", tools_condition, {"tools": "herramientas", END: END})
        g.add_edge("herramientas", "agente")
        destinos.append("agente")
    g.add_conditional_edges("interpretar", ruta_interpretar, destinos)
    for nodo in ("aclarar", "derivar", "registrar", "responder"):
        g.add_edge(nodo, END)
    return g.compile(checkpointer=checkpointer or InMemorySaver())


class MecaIA:
    """Interfaz simple sobre el grafo: un objeto por usuario, una conversación por thread_id."""

    def __init__(self, usuario: str = "invitado", memoria: Memoria | None = None,
                 llm=None, checkpointer=None):
        self.usuario = usuario
        self.grafo = construir_grafo(memoria or Memoria(), llm, checkpointer)
        self.ultimo_plan: list[str] = []

    def responder(self, texto: str, conversacion: str = "principal") -> str:
        config = {"configurable": {"thread_id": f"{self.usuario}:{conversacion}"}}
        estado = self.grafo.invoke(
            {"messages": [HumanMessage(texto)], "usuario": self.usuario, "plan": []}, config)
        self.ultimo_plan = estado["plan"]
        ultimo = estado["messages"][-1]
        return str(ultimo.text)


def crear_llm():
    from langchain_anthropic import ChatAnthropic
    return ChatAnthropic(model=MODELO, max_tokens=16000)
