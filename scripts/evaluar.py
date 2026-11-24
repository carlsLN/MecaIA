"""Evaluación de observabilidad de MecaIA.

Ejecuta los casos de evaluacion/casos.json, guarda las trazas de cada nodo y calcula las métricas:

- precisión: porcentaje de turnos que hacen lo que debería hacer un agente correcto,
- consistencia: (a) misma respuesta al repetir la misma pregunta y (b) misma decisión ante
  preguntas que dicen lo mismo con otras palabras,
- frecuencia de errores: excepciones, respaldos al modo demo y fallos por tipo de chequeo,
- latencia: p50, p95, p99 y máximo, por turno y por nodo del grafo,
- uso de recursos: tiempo de CPU, memoria pico y tokens del modelo de lenguaje.

Uso (desde la carpeta del proyecto):
    python scripts/evaluar.py                  # modo demo, 5 repeticiones por caso
    python scripts/evaluar.py --repeticiones 10
    python scripts/evaluar.py --modo claude    # usa Claude (requiere ANTHROPIC_API_KEY con créditos)

Resultados en evidencias/observabilidad/:
    trazas_evaluacion.jsonl   una línea por nodo, herramienta y turno (latencia y CPU)
    trazas_memoria.jsonl      una vuelta extra midiendo la memoria de cada nodo
    resultados_casos.csv      un turno evaluado por fila
    metricas.json             resumen de métricas (lo lee el dashboard)
"""
import argparse
import csv
import json
import os
import statistics
import sys
import time
import tracemalloc
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from mecaia.grafo import MecaIA, crear_llm  # noqa: E402
from mecaia.memoria import Memoria  # noqa: E402
from mecaia.observabilidad import Trazador, leer_trazas  # noqa: E402
from mecaia.texto import normalizar  # noqa: E402

CASOS = RAIZ / "evaluacion" / "casos.json"
SALIDA = RAIZ / "evidencias" / "observabilidad"

# Qué nodo final corresponde a cada acción esperada
ACCIONES = {"responder": "responder", "agente": "responder", "aclarar": "aclarar",
            "recomendar_mecanico": "mecanico", "conversar": "conversar", "registrar": "registrar"}

MENSAJE_LARGO = ("Hola, te cuento que tengo una yamaha r3 hace unos años y la uso todos los días para ir al "
                 "trabajo. " * 50 + "¿Qué aceite le pongo?")


def percentil(valores: list[float], p: float) -> float | None:
    """Percentil con interpolación lineal (igual que numpy por defecto)."""
    if not valores:
        return None
    v = sorted(valores)
    k = (len(v) - 1) * p / 100
    i = int(k)
    j = min(i + 1, len(v) - 1)
    return round(v[i] + (v[j] - v[i]) * (k - i), 3)


def resumen_numerico(valores: list[float]) -> dict:
    valores = [x for x in valores if x is not None]
    if not valores:
        return {}
    return {"n": len(valores), "promedio": round(statistics.mean(valores), 3),
            "p50": percentil(valores, 50), "p95": percentil(valores, 95),
            "p99": percentil(valores, 99), "max": round(max(valores), 3), "min": round(min(valores), 3)}


def evaluar_turno(esperado: dict, turno: dict, respuesta: str) -> dict:
    """Compara lo que hizo el agente con lo esperado. Devuelve un chequeo por criterio."""
    texto = normalizar(respuesta)
    accion = ACCIONES.get(turno.get("nodo_final"), turno.get("nodo_final"))
    chequeos = {}
    if "accion" in esperado:
        chequeos["accion"] = accion == esperado["accion"]
    if "vehiculo_id" in esperado:
        chequeos["vehiculo"] = turno.get("vehiculo_id") == esperado["vehiculo_id"]
    if "seguridad" in esperado:
        chequeos["seguridad"] = turno.get("seguridad") == esperado["seguridad"]
    if "contiene" in esperado:
        chequeos["contenido"] = all(normalizar(c) in texto for c in esperado["contiene"])
    if "contiene_alguno" in esperado:
        chequeos["contenido"] = chequeos.get("contenido", True) and any(
            normalizar(c) in texto for c in esperado["contiene_alguno"])
    if "no_contiene" in esperado:
        chequeos["no_inventa"] = not any(normalizar(c) in texto for c in esperado["no_contiene"])
    chequeos["sin_error"] = turno.get("estado") == "ok"
    return chequeos


def ejecutar(casos: list[dict], repeticiones: int, llm, trazador: Trazador) -> list[dict]:
    filas = []
    for rep in range(1, repeticiones + 1):
        for caso in casos:
            # Memoria nueva por caso: cada caso parte de cero y no depende de los anteriores
            memoria = Memoria(":memory:")
            agente = MecaIA(f"eval_{caso['id']}_{rep}", memoria, llm, trazador=trazador)
            for n, paso in enumerate(caso["turnos"], 1):
                mensaje = MENSAJE_LARGO if paso["mensaje"] == "__LARGO__" else paso["mensaje"]
                trazador.etiquetas = {"caso": caso["id"], "categoria": caso["categoria"],
                                      "repeticion": rep, "paso": n}
                respuesta = agente.responder(mensaje, paso.get("conversacion", "principal"))
                turno = trazador.ultimo_turno
                if "esperado" not in paso:
                    continue
                chequeos = evaluar_turno(paso["esperado"], turno, respuesta)
                filas.append({
                    "caso": caso["id"], "categoria": caso["categoria"], "grupo": caso.get("grupo", ""),
                    "descripcion": caso["descripcion"], "repeticion": rep, "paso": n,
                    "mensaje": mensaje[:120], "accion": ACCIONES.get(turno["nodo_final"], turno["nodo_final"]),
                    "accion_esperada": paso["esperado"].get("accion", ""),
                    "vehiculo_id": turno["vehiculo_id"] or "",
                    "vehiculo_esperado": paso["esperado"].get("vehiculo_id", "") or "",
                    "seguridad": turno["seguridad"] or "", "intencion": turno["intencion"] or "",
                    "ruta": " > ".join(turno["ruta"]), "correcto": all(chequeos.values()),
                    "chequeos_fallidos": ", ".join(k for k, ok in chequeos.items() if not ok),
                    "estado": turno["estado"], "error": turno["error"] or "",
                    "respaldo_demo": turno["respaldo_demo"], "duracion_ms": turno["duracion_ms"],
                    "cpu_ms": turno["cpu_ms"],
                    "tokens": turno["tokens_entrada"] + turno["tokens_salida"],
                    "turno_id": turno["turno_id"], "respuesta": respuesta,
                })
            memoria.db.close()
    return filas


def calcular_metricas(filas: list[dict], trazas: list[dict], trazas_memoria: list[dict], modo: str, repeticiones: int,
                      segundos: float) -> dict:
    total = len(filas)
    turnos = [t for t in trazas if t["tipo"] == "turno"]
    nodos = [t for t in trazas if t["tipo"] == "nodo"]
    unicos = [f for f in filas if f["repeticion"] == 1]

    # Precisión
    por_categoria = defaultdict(list)
    for f in unicos:
        por_categoria[f["categoria"]].append(f["correcto"])
    fallos_por_chequeo = Counter(c for f in unicos for c in f["chequeos_fallidos"].split(", ") if c)

    # Consistencia (a): la misma pregunta repetida da la misma respuesta y la misma ruta
    respuestas = defaultdict(set)
    for f in filas:
        respuestas[(f["caso"], f["paso"])].add((f["respuesta"], f["ruta"]))
    estables = sum(1 for r in respuestas.values() if len(r) == 1)

    # Consistencia (b): preguntas equivalentes (mismo grupo) llevan a la misma decisión
    grupos = defaultdict(list)
    for f in unicos:
        if f["grupo"]:
            grupos[f["grupo"]].append((f["accion"], f["vehiculo_id"], f["seguridad"]))
    consistencia_grupos = {}
    for g, decisiones in grupos.items():
        mas_comun, veces = Counter(decisiones).most_common(1)[0]
        consistencia_grupos[g] = {"casos": len(decisiones), "coinciden": veces,
                                  "porcentaje": round(100 * veces / len(decisiones), 1),
                                  "decision_mas_comun": " / ".join(x or "-" for x in mas_comun)}
    total_grupo = sum(v["casos"] for v in consistencia_grupos.values())

    # Errores
    excepciones = sum(1 for t in turnos if t["estado"] == "error")
    errores_nodo = Counter(n["nodo"] for n in nodos if n["estado"] == "error")
    respaldos = sum(1 for t in turnos if t.get("respaldo_demo"))

    # Latencia y recursos
    latencia_nodo = {}
    for nombre in sorted({n["nodo"] for n in nodos}):
        latencia_nodo[nombre] = resumen_numerico([n["duracion_ms"] for n in nodos if n["nodo"] == nombre])
    latencia_categoria = {}
    for cat in sorted({f["categoria"] for f in filas}):
        latencia_categoria[cat] = resumen_numerico([f["duracion_ms"] for f in filas if f["categoria"] == cat])
    duraciones = [t["duracion_ms"] for t in turnos]
    # Tiempo dentro de los nodos vs. tiempo del framework (checkpointer, estado, enrutamiento)
    suma_nodos = defaultdict(float)
    for n in nodos:
        suma_nodos[n["turno_id"]] += n["duracion_ms"]
    fuera_de_nodos = [t["duracion_ms"] - suma_nodos[t["turno_id"]] for t in turnos]
    pct_fuera = [100 * f / t["duracion_ms"] for f, t in zip(fuera_de_nodos, turnos) if t["duracion_ms"]]

    return {
        "generado": datetime.now().isoformat(timespec="seconds"),
        "modo": modo,
        "repeticiones": repeticiones,
        "casos": len({f["caso"] for f in filas}),
        "turnos_evaluados": total,
        "turnos_ejecutados": len(turnos),
        "duracion_total_s": round(segundos, 2),
        "turnos_por_segundo": round(len(turnos) / segundos, 1) if segundos else None,
        "precision": {
            "porcentaje": round(100 * sum(f["correcto"] for f in unicos) / len(unicos), 1),
            "correctos": sum(f["correcto"] for f in unicos), "total": len(unicos),
            "por_categoria": {c: {"correctos": sum(v), "total": len(v), "porcentaje": round(100 * sum(v) / len(v), 1)}
                              for c, v in sorted(por_categoria.items())},
            "fallos_por_chequeo": dict(fallos_por_chequeo.most_common()),
            "casos_fallidos": sorted({f["caso"] for f in unicos if not f["correcto"]}),
        },
        "consistencia": {
            "repeticion_porcentaje": round(100 * estables / len(respuestas), 1),
            "repeticion_estables": estables, "repeticion_total": len(respuestas),
            "parafraseo_porcentaje": round(100 * sum(v["coinciden"] for v in consistencia_grupos.values())
                                           / total_grupo, 1) if total_grupo else None,
            "parafraseo_por_grupo": consistencia_grupos,
        },
        "errores": {
            "excepciones": excepciones,
            "tasa_excepciones_porcentaje": round(100 * excepciones / len(turnos), 2) if turnos else 0,
            "errores_por_nodo": dict(errores_nodo),
            "respaldos_modo_demo": respaldos,
            "tasa_fallo_funcional_porcentaje": round(100 * sum(not f["correcto"] for f in filas) / total, 1),
        },
        "latencia_ms": {
            "turno": resumen_numerico(duraciones),
            "turno_sin_primero": resumen_numerico(duraciones[1:]),
            "primer_turno": duraciones[0] if duraciones else None,
            "por_nodo": latencia_nodo,
            "fuera_de_nodos": resumen_numerico(fuera_de_nodos),
            "fuera_de_nodos_porcentaje_promedio": round(statistics.mean(pct_fuera), 1) if pct_fuera else None,
            "por_categoria": latencia_categoria,
        },
        "recursos": {
            "cpu_ms_turno": resumen_numerico([t["cpu_ms"] for t in turnos]),
            "memoria_pico_kb_turno": resumen_numerico([t["memoria_pico_kb"] for t in trazas_memoria
                                                       if t["tipo"] == "turno"]),
            "memoria_pico_kb_por_nodo": {n: resumen_numerico([x["memoria_pico_kb"] for x in trazas_memoria
                                                              if x["tipo"] == "nodo" and x["nodo"] == n])
                                         for n in sorted({x["nodo"] for x in nodos})},
            "tokens_total": sum(t["tokens_entrada"] + t["tokens_salida"] for t in turnos),
            "tokens_promedio_turno": round(statistics.mean(
                [t["tokens_entrada"] + t["tokens_salida"] for t in turnos]), 1) if turnos else 0,
            "llamadas_herramientas": sum(len(t["herramientas"]) for t in turnos),
        },
        "uso": {
            "rutas": dict(Counter(f["ruta"] for f in unicos).most_common()),
            "derivaciones_mecanico_porcentaje": round(100 * sum(f["accion"] == "mecanico" for f in unicos) / len(unicos), 1),
            "aclaraciones_porcentaje": round(100 * sum(f["accion"] == "aclarar" for f in unicos) / len(unicos), 1),
        },
    }


def medir_costos(llm, vueltas: int = 30) -> dict:
    """Mide cuánto cuesta construir el agente y cuánto agrega la propia observabilidad."""
    mensajes = ["aceite para mi r3", "mi moto no frena", "hola", "cambio de aceite", "estanque de mi swift"]
    resultado = {}
    configuraciones = {
        "sin_trazas": dict(ruta=None, medir_memoria=False),
        "trazas_sin_memoria": dict(ruta=SALIDA / "_costos.jsonl", medir_memoria=False),
        "trazas_con_memoria": dict(ruta=SALIDA / "_costos.jsonl", medir_memoria=True),
    }
    for nombre, cfg in configuraciones.items():
        if tracemalloc.is_tracing():
            tracemalloc.stop()
        trazador = Trazador(cfg["ruta"], medir_memoria=cfg["medir_memoria"])
        inicio = time.perf_counter()
        agentes = [MecaIA(f"costo_{i}", Memoria(":memory:"), llm, trazador=trazador) for i in range(vueltas)]
        construir = (time.perf_counter() - inicio) * 1000 / vueltas
        tiempos = []
        for i, agente in enumerate(agentes):
            for m in mensajes:
                t0 = time.perf_counter()
                agente.responder(m, f"c{i}")
                tiempos.append((time.perf_counter() - t0) * 1000)
        resultado[nombre] = {"construir_agente_ms": round(construir, 3), "turno": resumen_numerico(tiempos)}
    if tracemalloc.is_tracing():
        tracemalloc.stop()
    (SALIDA / "_costos.jsonl").unlink(missing_ok=True)
    base = resultado["sin_trazas"]["turno"]["promedio"]
    for nombre in resultado:
        resultado[nombre]["sobrecarga_porcentaje"] = round(100 * (resultado[nombre]["turno"]["promedio"] - base) / base, 1)
    return resultado


def main() -> None:
    parser = argparse.ArgumentParser(description="Evalúa a MecaIA y calcula métricas de observabilidad")
    parser.add_argument("--repeticiones", type=int, default=5)
    parser.add_argument("--modo", choices=["demo", "claude"], default="demo")
    parser.add_argument("--salida", default=str(SALIDA))
    args = parser.parse_args()

    llm = None
    if args.modo == "claude":
        if not os.environ.get("ANTHROPIC_API_KEY"):
            sys.exit("Falta ANTHROPIC_API_KEY. Usa --modo demo o define la variable.")
        llm = crear_llm()

    salida = Path(args.salida)
    salida.mkdir(parents=True, exist_ok=True)
    ruta_trazas = salida / "trazas_evaluacion.jsonl"
    ruta_trazas.unlink(missing_ok=True)
    # Pasada 1 (latencia): sin medir memoria, porque tracemalloc hace más lento a Python
    trazador = Trazador(ruta_trazas, sesion=f"evaluacion-{args.modo}", medir_memoria=False)

    casos = json.loads(CASOS.read_text(encoding="utf-8"))["casos"]
    print(f"Ejecutando {len(casos)} casos x {args.repeticiones} repeticiones en modo {args.modo}...")
    inicio = time.perf_counter()
    filas = ejecutar(casos, args.repeticiones, llm, trazador)
    segundos = time.perf_counter() - inicio
    # Pasada 2 (memoria): una vuelta de los casos midiendo la memoria de cada nodo
    ruta_memoria = salida / "trazas_memoria.jsonl"
    ruta_memoria.unlink(missing_ok=True)
    ejecutar(casos, 1, llm, Trazador(ruta_memoria, sesion=f"memoria-{args.modo}", medir_memoria=True))
    tracemalloc.stop()

    with (salida / "resultados_casos.csv").open("w", encoding="utf-8", newline="") as f:
        escritor = csv.DictWriter(f, fieldnames=list(filas[0].keys()))
        escritor.writeheader()
        escritor.writerows(filas)

    metricas = calcular_metricas(filas, leer_trazas(ruta_trazas), leer_trazas(ruta_memoria),
                                 args.modo, args.repeticiones, segundos)
    if args.modo == "demo":
        print("Midiendo el costo de construir el agente y de la observabilidad...")
        metricas["costos"] = medir_costos(llm)
    (salida / "metricas.json").write_text(json.dumps(metricas, ensure_ascii=False, indent=2), encoding="utf-8")

    p, c, e, lat = metricas["precision"], metricas["consistencia"], metricas["errores"], metricas["latencia_ms"]
    print(f"\nPrecisión:              {p['porcentaje']}% ({p['correctos']}/{p['total']} turnos)")
    print(f"Consistencia repetición: {c['repeticion_porcentaje']}%")
    print(f"Consistencia parafraseo: {c['parafraseo_porcentaje']}%")
    print(f"Excepciones:             {e['excepciones']} ({e['tasa_excepciones_porcentaje']}%)")
    print(f"Latencia turno p50/p95:  {lat['turno']['p50']} / {lat['turno']['p95']} ms")
    if "costos" in metricas:
        k = metricas["costos"]
        print(f"Construir el agente:     {k['sin_trazas']['construir_agente_ms']} ms (un turno: "
              f"{k['sin_trazas']['turno']['promedio']} ms)")
        print(f"Costo de las trazas:     {k['trazas_sin_memoria']['sobrecarga_porcentaje']:+}% sin medir memoria, "
              f"{k['trazas_con_memoria']['sobrecarga_porcentaje']:+}% midiendo memoria")
    print(f"Casos que fallan:        {', '.join(p['casos_fallidos']) or 'ninguno'}")
    print(f"\nResultados en {salida}")


if __name__ == "__main__":
    main()
