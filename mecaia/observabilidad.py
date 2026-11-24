"""Observabilidad de MecaIA: trazas de ejecución en formato JSONL.

Cada turno del agente (un mensaje del usuario y su respuesta) deja en el archivo de trazas:

- un evento "nodo" por cada nodo del grafo que se ejecutó (seguridad, interpretar, responder...),
- un evento "herramienta" por cada herramienta que se llamó (en modo Claude),
- un evento "turno" con el resumen: ruta seguida, latencia total, CPU, memoria, tokens y errores.

La memoria se mide con tracemalloc: es la memoria extra que Python reservó durante el nodo
(pico), en KB.

JSONL significa una línea = un evento en JSON. Es fácil de leer con pandas, Streamlit o Excel.

Privacidad (Ley 19.628): el nombre del usuario nunca se guarda; se guarda un código irreversible
(hash). El texto de los mensajes se puede omitir con la variable MECAIA_TRAZAS_TEXTO=0.
"""
import hashlib
import json
import os
import time
import tracemalloc
import uuid
from datetime import datetime, timezone
from pathlib import Path

LARGO_MAXIMO_TEXTO = 400  # se recortan respuestas largas para que el log no crezca sin control


def anonimizar(usuario: str) -> str:
    """Código corto e irreversible para identificar al usuario sin guardar su nombre."""
    return "u_" + hashlib.sha256(usuario.encode("utf-8")).hexdigest()[:10]


def _ahora() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def _recortar(texto: str | None) -> str | None:
    if texto is None or len(texto) <= LARGO_MAXIMO_TEXTO:
        return texto
    return texto[:LARGO_MAXIMO_TEXTO] + "…"


class Trazador:
    """Registra lo que hace el agente. Si `ruta` es None, solo guarda el último turno en memoria."""

    def __init__(self, ruta: str | Path | None = None, sesion: str | None = None,
                 guardar_texto: bool | None = None, etiquetas: dict | None = None,
                 medir_memoria: bool | None = None):
        self.ruta = Path(ruta) if ruta else None
        if self.ruta:
            self.ruta.parent.mkdir(parents=True, exist_ok=True)
        self.sesion = sesion or uuid.uuid4().hex[:8]
        if guardar_texto is None:
            guardar_texto = os.environ.get("MECAIA_TRAZAS_TEXTO", "1") != "0"
        self.guardar_texto = guardar_texto
        self.etiquetas = dict(etiquetas or {})  # datos extra para cada evento (ej. caso de prueba)
        self._turno: dict | None = None
        self.ultimo_turno: dict | None = None
        # tracemalloc hace más lento a Python, así que solo se activa cuando se escriben trazas
        self.medir_memoria = bool(self.ruta) if medir_memoria is None else medir_memoria
        if self.medir_memoria and not tracemalloc.is_tracing():
            tracemalloc.start()

    # ------------------------------------------------------------------ turnos
    def iniciar_turno(self, usuario: str, conversacion: str, texto: str, modo: str) -> str:
        turno_id = uuid.uuid4().hex[:12]
        self._turno = {
            "tipo": "turno", "turno_id": turno_id, "ts": _ahora(), "sesion": self.sesion,
            "usuario": anonimizar(usuario), "conversacion": anonimizar(conversacion), "modo": modo,
            "mensaje": texto if self.guardar_texto else None, "largo_mensaje": len(texto),
            "ruta": [], "herramientas": [], "tokens_entrada": 0, "tokens_salida": 0,
            "memoria_pico_kb": 0.0, "errores_nodo": 0, "respaldo_demo": False,
            "_t0": time.perf_counter(), "_cpu0": time.process_time(),
        }
        return turno_id

    def terminar_turno(self, respuesta: str | None, estado: dict | None = None,
                       error: BaseException | None = None) -> dict:
        t = self._turno or {}
        estado = estado or {}
        t.update({
            "duracion_ms": round((time.perf_counter() - t.pop("_t0", time.perf_counter())) * 1000, 3),
            "cpu_ms": round((time.process_time() - t.pop("_cpu0", time.process_time())) * 1000, 3),
            "nodo_final": t["ruta"][-1] if t.get("ruta") else None,
            "seguridad": (estado.get("seguridad") or {}).get("nivel"),
            "intencion": estado.get("intencion"),
            "vehiculo_id": estado.get("vehiculo_id"),
            "n_candidatos": len(estado.get("candidatos") or []),
            "plan": estado.get("plan", []),
            "respuesta": _recortar(respuesta) if self.guardar_texto else None,
            "largo_respuesta": len(respuesta or ""),
            "estado": "error" if error else "ok",
            "error": f"{type(error).__name__}: {error}" if error else None,
        })
        t.update(self.etiquetas)
        self._escribir(t)
        self.ultimo_turno = t
        self._turno = None
        return t

    def marcar_respaldo(self, error: BaseException) -> None:
        """El modelo de lenguaje falló y el turno se respondió con el modo demo."""
        if self._turno is not None:
            self._turno["respaldo_demo"] = True
            self._turno["error_modelo"] = f"{type(error).__name__}: {error}"

    # ------------------------------------------------------------------ nodos
    def envolver_nodo(self, nombre: str, funcion):
        """Devuelve la función del nodo con medición de tiempo, CPU, memoria y errores."""

        def nodo_con_traza(estado):
            evento = {"tipo": "nodo", "nodo": nombre, "ts": _ahora(), "sesion": self.sesion,
                      "turno_id": (self._turno or {}).get("turno_id")}
            medir = self.medir_memoria and tracemalloc.is_tracing()
            if medir:
                tracemalloc.reset_peak()
                memoria_inicial, _ = tracemalloc.get_traced_memory()
            inicio, cpu = time.perf_counter(), time.process_time()
            error = None
            try:
                salida = funcion(estado)
                return salida
            except Exception as e:  # se registra y se vuelve a lanzar
                error, salida = e, None
                raise
            finally:
                pico_kb = None
                if medir:
                    _, pico = tracemalloc.get_traced_memory()
                    pico_kb = round(max(pico - memoria_inicial, 0) / 1024, 1)
                evento.update({
                    "duracion_ms": round((time.perf_counter() - inicio) * 1000, 3),
                    "cpu_ms": round((time.process_time() - cpu) * 1000, 3),
                    "memoria_pico_kb": pico_kb,
                    "estado": "error" if error else "ok",
                    "error": f"{type(error).__name__}: {error}" if error else None,
                })
                evento.update(_resumen_salida(salida))
                evento.update(self.etiquetas)
                self._acumular(evento)
                self._escribir(evento)

        return nodo_con_traza

    def registrar_herramienta(self, nombre: str, duracion_ms: float, error: BaseException | None) -> None:
        evento = {"tipo": "herramienta", "herramienta": nombre, "ts": _ahora(), "sesion": self.sesion,
                  "turno_id": (self._turno or {}).get("turno_id"),
                  "duracion_ms": round(duracion_ms, 3), "estado": "error" if error else "ok",
                  "error": f"{type(error).__name__}: {error}" if error else None}
        evento.update(self.etiquetas)
        if self._turno is not None:
            self._turno["herramientas"].append(nombre)
        self._escribir(evento)

    # ------------------------------------------------------------------ interno
    def _acumular(self, evento: dict) -> None:
        t = self._turno
        if t is None:
            return
        t["ruta"].append(evento["nodo"])
        t["memoria_pico_kb"] = max(t["memoria_pico_kb"], evento["memoria_pico_kb"] or 0.0)
        t["tokens_entrada"] += evento.get("tokens_entrada", 0)
        t["tokens_salida"] += evento.get("tokens_salida", 0)
        t["errores_nodo"] += evento["estado"] == "error"

    def _escribir(self, evento: dict) -> None:
        if not self.ruta:
            return
        limpio = {k: v for k, v in evento.items() if not k.startswith("_")}
        with self.ruta.open("a", encoding="utf-8") as f:
            f.write(json.dumps(limpio, ensure_ascii=False, default=str) + "\n")


def _resumen_salida(salida) -> dict:
    """Datos útiles de lo que devolvió el nodo: último paso del plan y tokens del modelo."""
    if not isinstance(salida, dict):
        return {}
    resumen = {}
    if salida.get("plan"):
        resumen["decision"] = salida["plan"][-1]
    for m in salida.get("messages", []) or []:
        uso = getattr(m, "usage_metadata", None)
        if uso:
            resumen["tokens_entrada"] = resumen.get("tokens_entrada", 0) + uso.get("input_tokens", 0)
            resumen["tokens_salida"] = resumen.get("tokens_salida", 0) + uso.get("output_tokens", 0)
    return resumen


def leer_trazas(ruta: str | Path) -> list[dict]:
    ruta = Path(ruta)
    if not ruta.exists():
        return []
    with ruta.open(encoding="utf-8") as f:
        return [json.loads(linea) for linea in f if linea.strip()]


def borrar_trazas_usuario(ruta: str | Path, usuario: str) -> int:
    """Quita del archivo de trazas los turnos de un usuario. Devuelve cuántos eventos se borraron."""
    ruta = Path(ruta)
    eventos = leer_trazas(ruta)
    if not eventos:
        return 0
    codigo = anonimizar(usuario)
    turnos = {e["turno_id"] for e in eventos if e.get("tipo") == "turno" and e.get("usuario") == codigo}
    quedan = [e for e in eventos if e.get("turno_id") not in turnos]
    with ruta.open("w", encoding="utf-8") as f:
        for e in quedan:
            f.write(json.dumps(e, ensure_ascii=False, default=str) + "\n")
    return len(eventos) - len(quedan)
