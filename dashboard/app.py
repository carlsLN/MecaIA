"""Dashboard de observabilidad de MecaIA (Streamlit).

Muestra las métricas de la evaluación (precisión, consistencia, errores, latencia y recursos)
y permite explorar las trazas de ejecución del agente, turno por turno y nodo por nodo.

Uso (desde la carpeta del proyecto):
    python scripts/evaluar.py          # genera los datos (si aún no existen)
    streamlit run dashboard/app.py     # abre el dashboard en el navegador
"""
import json
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

RAIZ = Path(__file__).resolve().parent.parent
EVALUACION = RAIZ / "evidencias" / "observabilidad"
LOGS_USO = RAIZ / "logs" / "trazas.jsonl"

AZUL = "#2a78d6"      # serie única
NARANJO = "#eb6834"   # segunda serie (p95)
BIEN = "#0ca30c"      # estado: cumple
CRITICO = "#d03b3b"   # estado: no cumple

# Metas (umbrales) contra las que se compara cada métrica
METAS = {"precision": 90.0, "consistencia_repeticion": 95.0, "consistencia_parafraseo": 90.0,
         "tasa_excepciones": 1.0, "latencia_p95_ms": 50.0}

st.set_page_config(page_title="MecaIA · Observabilidad", page_icon="🔧", layout="wide")


@st.cache_data
def cargar_jsonl(ruta: str, modificado: float) -> pd.DataFrame:
    filas = [json.loads(linea) for linea in Path(ruta).read_text(encoding="utf-8").splitlines() if linea.strip()]
    return pd.DataFrame(filas)


@st.cache_data
def cargar_csv(ruta: str, modificado: float) -> pd.DataFrame:
    return pd.read_csv(ruta)


def leer(ruta: Path, lector):
    return lector(str(ruta), ruta.stat().st_mtime) if ruta.exists() else None


def estado_meta(valor, meta, menor_es_mejor=False) -> str:
    if valor is None:
        return "sin datos"
    cumple = valor <= meta if menor_es_mejor else valor >= meta
    return f"✅ cumple la meta ({'≤' if menor_es_mejor else '≥'} {meta:g})" if cumple else \
        f"⚠️ bajo la meta ({'≤' if menor_es_mejor else '≥'} {meta:g})"


def barras(df: pd.DataFrame, x: str, y: str, titulo_x: str, titulo_y: str, color: str = AZUL,
           tooltip: list | None = None, orden: str | None = "-x", alto: int = 300, entero: bool = False):
    """Barras horizontales con el valor escrito al final de cada barra."""
    eje = alt.Axis(tickMinStep=1, format="d") if entero else alt.Axis()
    base = alt.Chart(df).encode(x=alt.X(x, title=titulo_x, axis=eje), y=alt.Y(y, title=titulo_y, sort=orden),
                                tooltip=tooltip or [y, x])
    return (base.mark_bar(color=color, cornerRadiusEnd=4, size=18)
            + base.mark_text(align="left", dx=4, color="gray").encode(text=x)).properties(height=alto)


# ----------------------------------------------------------------------------- datos
metricas_ruta = EVALUACION / "metricas.json"
if not metricas_ruta.exists():
    st.error("No hay resultados de evaluación. Ejecuta primero:  python scripts/evaluar.py")
    st.stop()
M = json.loads(metricas_ruta.read_text(encoding="utf-8"))
resultados = leer(EVALUACION / "resultados_casos.csv", cargar_csv)
trazas_eval = leer(EVALUACION / "trazas_evaluacion.jsonl", cargar_jsonl)
trazas_uso = leer(LOGS_USO, cargar_jsonl)

st.title("🔧 MecaIA · Observabilidad del agente")
st.caption(f"Evaluación generada el {M['generado']} · modo {M['modo']} · {M['casos']} casos × "
           f"{M['repeticiones']} repeticiones · {M['turnos_ejecutados']} turnos ejecutados")

with st.sidebar:
    st.header("Filtros")
    categorias = sorted(resultados["categoria"].unique()) if resultados is not None else []
    elegidas = st.multiselect("Categoría de prueba", categorias, default=categorias)
    st.divider()
    st.markdown("**Datos**")
    st.markdown(f"- Evaluación: `evidencias/observabilidad/`\n- Uso real: `logs/trazas.jsonl` "
                f"({'sin datos aún' if trazas_uso is None else f'{len(trazas_uso)} eventos'})")
    st.caption("Para actualizar los datos vuelve a ejecutar `python scripts/evaluar.py` y recarga la página.")

res = resultados[resultados["categoria"].isin(elegidas)] if resultados is not None else None
res1 = res[res["repeticion"] == 1] if res is not None else None

tab_resumen, tab_precision, tab_latencia, tab_trazas, tab_privacidad = st.tabs(
    ["Resumen", "Precisión y consistencia", "Latencia y recursos", "Explorador de trazas", "Privacidad"])

# ----------------------------------------------------------------------------- resumen
with tab_resumen:
    p, c, e, lat, rec = M["precision"], M["consistencia"], M["errores"], M["latencia_ms"], M["recursos"]
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Precisión", f"{p['porcentaje']}%", help="Turnos en que el agente hizo lo correcto")
    k1.caption(f"{p['correctos']} de {p['total']} turnos · {estado_meta(p['porcentaje'], METAS['precision'])}")
    k2.metric("Consistencia al repetir", f"{c['repeticion_porcentaje']}%",
              help="Misma pregunta repetida → misma respuesta y misma ruta")
    k2.caption(estado_meta(c["repeticion_porcentaje"], METAS["consistencia_repeticion"]))
    k3.metric("Consistencia ante paráfrasis", f"{c['parafraseo_porcentaje']}%",
              help="Preguntas que dicen lo mismo con otras palabras → misma decisión")
    k3.caption(estado_meta(c["parafraseo_porcentaje"], METAS["consistencia_parafraseo"]))
    k4.metric("Tasa de excepciones", f"{e['tasa_excepciones_porcentaje']}%",
              help="Turnos que terminaron con un error interno")
    k4.caption(f"{e['excepciones']} excepciones · {e['respaldos_modo_demo']} respaldos al modo demo · "
               f"{estado_meta(e['tasa_excepciones_porcentaje'], METAS['tasa_excepciones'], True)}")

    k5, k6, k7, k8 = st.columns(4)
    k5.metric("Latencia p50", f"{lat['turno']['p50']:.1f} ms")
    k6.metric("Latencia p95", f"{lat['turno']['p95']:.1f} ms")
    k6.caption(estado_meta(lat["turno"]["p95"], METAS["latencia_p95_ms"], True))
    k7.metric("CPU por turno (promedio)", f"{rec['cpu_ms_turno']['promedio']:.1f} ms")
    k8.metric("Memoria pico por turno (p95)", f"{rec['memoria_pico_kb_turno']['p95']:.1f} KB")
    k8.caption(f"Tokens usados: {rec['tokens_total']} (modo {M['modo']})")

    st.subheader("Fallos funcionales por tipo de chequeo")
    fallos = pd.DataFrame([{"chequeo": k, "turnos": v} for k, v in p["fallos_por_chequeo"].items()])
    if fallos.empty:
        st.success("No hay fallos.")
    else:
        st.altair_chart(barras(fallos, "turnos:Q", "chequeo:N", "Turnos con el chequeo fallido", "Chequeo",
                               color=CRITICO, alto=200, entero=True), use_container_width=True)
    st.caption("accion = el agente tomó otro camino · vehiculo = no identificó el vehículo correcto · "
               "seguridad = no detectó (o exageró) un riesgo · contenido = la respuesta no tiene el dato esperado · "
               "no_inventa = la respuesta tiene datos que no debería.")

# ----------------------------------------------------------------------------- precisión
with tab_precision:
    if res1 is None or res1.empty:
        st.info("Sin resultados para los filtros elegidos.")
    else:
        por_cat = (res1.groupby("categoria")["correcto"].agg(["sum", "count"]).reset_index()
                   .rename(columns={"sum": "correctos", "count": "total"}))
        por_cat["precision"] = (100 * por_cat["correctos"] / por_cat["total"]).round(1)
        izq, der = st.columns(2)
        with izq:
            st.subheader("Precisión por categoría (%)")
            base = barras(por_cat, "precision:Q", "categoria:N", "Precisión (%)", "Categoría",
                          tooltip=["categoria", "precision", "correctos", "total"])
            meta = alt.Chart(pd.DataFrame({"meta": [METAS["precision"]]})).mark_rule(
                strokeDash=[4, 4], color="gray").encode(x="meta:Q")
            st.altair_chart(base + meta, use_container_width=True)
            st.caption(f"Línea punteada: meta de {METAS['precision']:g}%.")
        with der:
            st.subheader("Consistencia ante paráfrasis")
            grupos = pd.DataFrame([{"grupo": g, **v} for g, v in M["consistencia"]["parafraseo_por_grupo"].items()])
            st.altair_chart(barras(grupos, "porcentaje:Q", "grupo:N", "Casos con la misma decisión (%)", "Grupo",
                                   tooltip=["grupo", "porcentaje", "coinciden", "casos", "decision_mas_comun"]),
                            use_container_width=True)
            st.caption("Ojo: consistente no significa correcto. Un grupo puede fallar siempre igual. "
                       "Cada grupo junta preguntas equivalentes (ej. 'aceite r3', 'q aceite le pongo a la r3', "
                       "'que aseite lleva mi r3'). Deberían terminar en la misma decisión.")

        st.subheader("Casos que fallan")
        fallidos = res1[~res1["correcto"]][["caso", "categoria", "descripcion", "mensaje", "accion",
                                            "accion_esperada", "vehiculo_id", "vehiculo_esperado",
                                            "seguridad", "chequeos_fallidos", "respuesta"]]
        st.dataframe(fallidos, hide_index=True, use_container_width=True)

        with st.expander("Ver todos los casos (primera repetición)"):
            st.dataframe(res1.drop(columns=["turno_id"]), hide_index=True, use_container_width=True)

        st.subheader("Rutas del grafo más frecuentes")
        rutas = res1["ruta"].value_counts().reset_index()
        rutas.columns = ["ruta", "turnos"]
        st.altair_chart(barras(rutas, "turnos:Q", "ruta:N", "Turnos", "Ruta", entero=True), use_container_width=True)

# ----------------------------------------------------------------------------- latencia
with tab_latencia:
    nodos = trazas_eval[trazas_eval["tipo"] == "nodo"] if trazas_eval is not None else pd.DataFrame()
    turnos = trazas_eval[trazas_eval["tipo"] == "turno"] if trazas_eval is not None else pd.DataFrame()
    if "categoria" in turnos:
        turnos = turnos[turnos["categoria"].isin(elegidas)]
        nodos = nodos[nodos["categoria"].isin(elegidas)]

    izq, der = st.columns(2)
    with izq:
        st.subheader("Distribución de la latencia por turno")
        if not turnos.empty:
            hist = (alt.Chart(turnos).mark_bar(color=AZUL, cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
                    .encode(x=alt.X("duracion_ms:Q", bin=alt.Bin(maxbins=30), title="Latencia del turno (ms)"),
                            y=alt.Y("count():Q", title="Turnos"),
                            tooltip=[alt.Tooltip("count():Q", title="Turnos")])
                    .properties(height=300))
            st.altair_chart(hist, use_container_width=True)
    with der:
        st.subheader("Latencia por nodo del grafo (ms)")
        filas = [{"nodo": n, "percentil": k, "ms": v[k]} for n, v in M["latencia_ms"]["por_nodo"].items()
                 for k in ("p50", "p95")]
        df_nodo = pd.DataFrame(filas)
        graf = (alt.Chart(df_nodo).mark_bar(cornerRadiusEnd=4, size=10)
                .encode(x=alt.X("ms:Q", title="Milisegundos"), y=alt.Y("nodo:N", title="Nodo", sort="-x"),
                        yOffset="percentil:N",
                        color=alt.Color("percentil:N", scale=alt.Scale(range=[AZUL, NARANJO]),
                                        legend=alt.Legend(title="Percentil", orient="bottom")),
                        tooltip=["nodo", "percentil", "ms"])
                .properties(height=300))
        st.altair_chart(graf, use_container_width=True)

    st.subheader("¿Dónde se va el tiempo de un turno?")
    fuera = M["latencia_ms"].get("fuera_de_nodos", {})
    c1, c2, c3 = st.columns(3)
    c1.metric("Turno completo (promedio)", f"{M['latencia_ms']['turno']['promedio']:.2f} ms")
    c2.metric("Fuera de los nodos (promedio)", f"{fuera.get('promedio', 0):.2f} ms")
    c3.metric("Porcentaje del turno fuera de los nodos", f"{M['latencia_ms'].get('fuera_de_nodos_porcentaje_promedio')}%")
    st.caption("'Fuera de los nodos' es el tiempo que usa LangGraph para guardar el estado (checkpointer), "
               "enrutar y copiar datos entre nodos. Si es alto, el cuello de botella no está en la lógica del agente.")

    if "costos" in M:
        st.subheader("Costo de construir el agente y de la propia observabilidad")
        k = M["costos"]
        costos = pd.DataFrame([{"configuración": n.replace("_", " "), "construir agente (ms)": v["construir_agente_ms"],
                                "turno promedio (ms)": v["turno"]["promedio"], "turno p95 (ms)": v["turno"]["p95"],
                                "sobrecarga vs. sin trazas (%)": v["sobrecarga_porcentaje"]} for n, v in k.items()])
        st.dataframe(costos, hide_index=True, use_container_width=True)

    izq, der = st.columns(2)
    with izq:
        st.subheader("Memoria pico por nodo (KB, p95)")
        mem = pd.DataFrame([{"nodo": n, "kb_p95": v.get("p95"), "kb_max": v.get("max")}
                            for n, v in M["recursos"]["memoria_pico_kb_por_nodo"].items() if v])
        st.altair_chart(barras(mem, "kb_p95:Q", "nodo:N", "KB (p95)", "Nodo", tooltip=["nodo", "kb_p95", "kb_max"]),
                        use_container_width=True)
    with der:
        st.subheader("Latencia por categoría (p50 y p95, ms)")
        filas = [{"categoria": n, "percentil": k, "ms": v[k]} for n, v in M["latencia_ms"]["por_categoria"].items()
                 for k in ("p50", "p95") if n in elegidas]
        graf = (alt.Chart(pd.DataFrame(filas)).mark_bar(cornerRadiusEnd=4, size=8)
                .encode(x=alt.X("ms:Q", title="Milisegundos"), y=alt.Y("categoria:N", title="Categoría"),
                        yOffset="percentil:N",
                        color=alt.Color("percentil:N", scale=alt.Scale(range=[AZUL, NARANJO]),
                                        legend=alt.Legend(title="Percentil", orient="bottom")),
                        tooltip=["categoria", "percentil", "ms"])
                .properties(height=300))
        st.altair_chart(graf, use_container_width=True)

# ----------------------------------------------------------------------------- trazas
with tab_trazas:
    fuentes = {"Evaluación (scripts/evaluar.py)": trazas_eval}
    if trazas_uso is not None:
        fuentes["Uso real (logs/trazas.jsonl)"] = trazas_uso
    fuente = st.radio("Origen de las trazas", list(fuentes), horizontal=True)
    df = fuentes[fuente]
    if df is None or df.empty:
        st.info("No hay trazas en este origen.")
    else:
        f1, f2, f3, f4 = st.columns(4)
        tipos = f1.multiselect("Tipo de evento", sorted(df["tipo"].unique()), default=["turno"])
        estados = f2.multiselect("Estado", sorted(df["estado"].dropna().unique()),
                                 default=sorted(df["estado"].dropna().unique()))
        nodos_disp = sorted(df["nodo"].dropna().unique()) if "nodo" in df else []
        nodos_sel = f3.multiselect("Nodo", nodos_disp, default=nodos_disp)
        lento = f4.number_input("Solo eventos más lentos que (ms)", min_value=0.0, value=0.0, step=1.0)
        vista = df[df["tipo"].isin(tipos) & df["estado"].isin(estados) & (df["duracion_ms"] >= lento)]
        if "nodo" in vista:
            vista = vista[vista["nodo"].isna() | vista["nodo"].isin(nodos_sel)]
        if "categoria" in vista:
            vista = vista[vista["categoria"].isna() | vista["categoria"].isin(elegidas)]
        columnas = [c for c in ["ts", "tipo", "caso", "categoria", "repeticion", "turno_id", "nodo", "herramienta",
                                "mensaje", "ruta", "decision", "seguridad", "intencion", "vehiculo_id", "duracion_ms",
                                "cpu_ms", "memoria_pico_kb", "estado", "error", "respaldo_demo"] if c in vista]
        st.caption(f"{len(vista)} eventos")
        st.dataframe(vista[columnas].sort_values("ts", ascending=False), hide_index=True,
                     use_container_width=True, height=320)

        st.subheader("Línea de tiempo de un turno")
        turnos_df = df[df["tipo"] == "turno"]
        if not turnos_df.empty:
            etiquetas = {r.turno_id: f"{r.turno_id} · {str(r.mensaje)[:60]} · {r.duracion_ms:.1f} ms"
                         for r in turnos_df.sort_values("duracion_ms", ascending=False).itertuples()}
            elegido = st.selectbox("Turno (ordenados del más lento al más rápido)", list(etiquetas),
                                   format_func=etiquetas.get)
            t = turnos_df[turnos_df["turno_id"] == elegido].iloc[0]
            pasos = df[(df["turno_id"] == elegido) & (df["tipo"].isin(["nodo", "herramienta"]))].copy()
            pasos["nombre"] = pasos.get("nodo").fillna(pasos.get("herramienta", pd.Series(dtype=str))) \
                if "herramienta" in pasos else pasos["nodo"]
            pasos["inicio"] = pd.to_datetime(pasos["ts"])
            pasos["fin"] = pasos["inicio"] + pd.to_timedelta(pasos["duracion_ms"], unit="ms")
            linea = (alt.Chart(pasos).mark_bar(color=AZUL, cornerRadius=3, size=16)
                     .encode(x=alt.X("inicio:T", title="Tiempo"), x2="fin:T",
                             y=alt.Y("nombre:N", sort=None, title="Paso"),
                             tooltip=["nombre", "duracion_ms", "estado", "decision"])
                     .properties(height=60 + 30 * len(pasos)))
            st.altair_chart(linea, use_container_width=True)
            st.markdown(f"**Mensaje:** {t.get('mensaje')}  \n**Ruta:** {' → '.join(t['ruta'])}  \n"
                        f"**Plan:** {' → '.join(t['plan'])}  \n**Estado:** {t['estado']}"
                        + (f" · **Error:** {t['error']}" if t.get("error") else ""))
            with st.expander("Respuesta del agente"):
                st.write(t.get("respuesta"))

# ----------------------------------------------------------------------------- privacidad
with tab_privacidad:
    st.subheader("Qué se guarda en las trazas")
    st.markdown("""
| Dato | ¿Se guarda? | Cómo |
| --- | --- | --- |
| Nombre del usuario | No | Se reemplaza por un código irreversible (hash SHA-256 recortado), ej. `u_75cee5b221` |
| Texto del mensaje y de la respuesta | Opcional | Se puede apagar con `MECAIA_TRAZAS_TEXTO=0`; las respuestas se recortan a 400 caracteres |
| Vehículo, ruta del grafo, tiempos, errores | Sí | Son datos técnicos, necesarios para medir y mejorar el agente |
| API key | Nunca | Se lee de una variable de entorno y no se escribe en ningún archivo |
""")
    if trazas_eval is not None and "usuario" in trazas_eval:
        st.caption(f"Usuarios distintos en las trazas de evaluación: {trazas_eval['usuario'].nunique()} "
                   f"(todos anonimizados).")
    st.markdown("Ver el análisis completo en `docs/observabilidad.md` (sección *Ética y privacidad*).")
