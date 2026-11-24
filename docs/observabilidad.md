# Observabilidad de MecaIA (Evaluación Parcial 3)

> **Borrador de apoyo para el informe y la presentación.** Este documento reúne los datos medidos y
> una primera lectura de ellos. La pauta exige que el análisis, las justificaciones técnicas y las
> conclusiones sean del equipo: revisen cada hallazgo contra el dashboard, decidan cuáles defienden
> y redáctenlos con sus propias palabras. Las secciones **Conclusiones** y **Reflexiones
> individuales** quedan en blanco a propósito.

Los números de este documento salen de una corrida de `python scripts/evaluar.py` en modo demo
(54 casos × 5 repeticiones = 295 turnos). Los tiempos cambian un poco en cada corrida y según el
computador; el valor vigente siempre está en `evidencias/observabilidad/metricas.json` y en el
dashboard.

## 1. Qué se implementó

| Pieza | Archivo | Qué hace |
| --- | --- | --- |
| Trazas por nodo | `mecaia/observabilidad.py` | Envuelve cada nodo del grafo de LangGraph y registra en JSONL: hora, duración, CPU, memoria pico, decisión tomada, tokens (modo Claude) y errores. También registra cada llamada a herramienta y un resumen por turno (ruta del grafo, vehículo, nivel de seguridad, latencia total, respaldo al modo demo). |
| Manejo de errores | `mecaia/grafo.py` (`MecaIA.responder`) | Si el modelo de lenguaje falla (por ejemplo, API key sin créditos) el turno se responde con el modo demo y queda marcado `respaldo_demo`. Si falla otra cosa, el usuario recibe un mensaje seguro y el error queda en la traza. |
| Set de pruebas | `evaluacion/casos.json` | 54 casos en 9 categorías: normales, variaciones de escritura, datos faltantes, vehículo desconocido, riesgo, conversación, registro, fuera de dominio y robustez. |
| Cálculo de métricas | `scripts/evaluar.py` | Ejecuta los casos, compara con lo esperado y calcula precisión, consistencia, errores, latencia y recursos. |
| Dashboard | `dashboard/app.py` (Streamlit) | 5 pestañas: resumen con metas, precisión y consistencia, latencia y recursos, explorador de trazas con línea de tiempo por turno, y privacidad. |
| Privacidad | `mecaia/observabilidad.py`, `main.py` | Usuario anonimizado con hash, texto opcional (`MECAIA_TRAZAS_TEXTO=0`), borrado de datos con `--borrar-mis-datos`. |

### Métricas y cómo se calculan

| Métrica | Definición | Resultado | Meta |
| --- | --- | --- | --- |
| Precisión | % de turnos en que el agente hace lo esperado: camino del grafo, vehículo, nivel de seguridad y contenido de la respuesta | **79,6 %** (43/54) | ≥ 90 % |
| Consistencia al repetir | % de preguntas que, repetidas 5 veces, dan exactamente la misma respuesta y ruta | **100 %** | ≥ 95 % |
| Consistencia ante paráfrasis | % de preguntas equivalentes (mismo grupo) que llevan a la misma decisión | **83,3 %** | ≥ 90 % |
| Tasa de excepciones | % de turnos que terminan con un error interno | **0 %** (0/295) | ≤ 1 % |
| Tasa de fallo funcional | % de turnos que no cumplen lo esperado, aunque no haya excepción | **20,4 %** | — |
| Latencia por turno | p50 / p95 / p99 / máximo | **3,8 / 5,0 / 8,0 / 10,8 ms** | p95 ≤ 50 ms |
| CPU por turno | Tiempo de CPU promedio | **4,0 ms** | — |
| Memoria pico por turno | Memoria extra reservada durante el turno (tracemalloc), p50 / p95 | **2,3 / 6,6 KB** | — |
| Tokens por turno | Suma de tokens de entrada y salida del modelo | 0 (modo demo) | — |

La precisión usa 6 chequeos por turno (`accion`, `vehiculo`, `seguridad`, `contenido`,
`no_inventa`, `sin_error`); un turno es correcto solo si pasa todos los que aplican.

## 2. Hallazgos en los registros (material para IE3 e IE6)

Capturas: `evidencias/observabilidad/capturas/`.

### H1. Vehículos que no están en la base: 0 % de precisión
Los 4 casos (Toyota Corolla, Chevrolet Sail, Nissan Versa, Kawasaki Ninja 650) terminan en
`seguridad > interpretar > aclarar` y el agente responde *"¿Para qué vehículo es?"*, aunque el usuario
ya lo dijo. En una conversación real eso genera un bucle. El grupo tiene 100 % de consistencia:
falla siempre igual, lo que muestra que **consistente no es lo mismo que correcto**.
Origen en el código: `buscar_vehiculo` devuelve 0 candidatos y `ruta_interpretar` trata "no
encontrado" igual que "no mencionado".

### H2. Riesgos que no se detectan (el hallazgo más grave)
Fallan 4 de 16 casos de riesgo: R11 *"los frenos de mi moto están fallando"*, R12 *"la temperatura del
motor está muy alta"*, R13 *"…los frenos que no responden"* y R16. Las reglas de `seguridad.json`
reconocen frases exactas (`fren\w* no (responde|…)`), así que basta una palabra entre medio
("frenos **que** no responden") para que el riesgo pase como `ok`.
R16 muestra el peor caso: el usuario dice que los frenos fallan, el agente pregunta el vehículo, el
usuario responde *"una yamaha r15"* y el agente le entrega el **paso a paso para revisar las
pastillas**. El chequeo de seguridad solo mira el último mensaje, por lo que el riesgo del turno
anterior se pierde.

### H3. Variaciones de escritura
El grupo "aceite R3" tiene 80 % de consistencia: `r-3` (V03) no se reconoce porque los alias no
incluyen guiones, y `aseite` (V04) no activa el procedimiento porque las palabras clave se comparan de
forma exacta.

### H4. El año no se usa para resolver la ambigüedad
F07 (*"kawasaki 400 del año 1978"*) solo calza con la KZ400 (1974-1984), pero el agente pregunta entre
tres modelos: `nodo_interpretar` no extrae el año, aunque `buscar_vehiculo` acepta el parámetro `anio`.

### H5. El tiempo se va fuera de la lógica del agente
En promedio, el **86 %** de cada turno ocurre fuera de los nodos: es el trabajo de LangGraph para
guardar el estado en el checkpointer, enrutar y copiar datos. El nodo más lento es `interpretar`
(p95 0,62 ms): en mensajes sin procedimiento llama dos veces a `bc.buscar_vehiculo(texto)`, y siempre recorre todas las expresiones
regulares de la base en cada mensaje.

### H6. Construir el agente cuesta más que responder
Crear un objeto `MecaIA` (compilar el grafo) toma **≈19 ms**, unas 5 veces lo que tarda un turno
(≈3,5 ms). Hoy se crea uno por usuario; en un servidor con muchos usuarios ese costo dominaría.

### H7. Arranque en frío
El primer turno de la corrida tardó 9,4 ms contra 3,8 ms de mediana, y el pico de memoria más alto
(81 KB) aparece en ese primer turno: es la carga de los JSON de la base y las reglas (`lru_cache`).

### H8. La observabilidad también tiene costo
Escribir trazas agrega entre 4 % y 10 % a la latencia (varía por corrida), pero medir memoria con
`tracemalloc` la multiplica por ~3 (+195 %). Por eso la evaluación mide latencia y memoria en
pasadas separadas.

### H9. Robustez y errores
0 excepciones en 295 turnos, incluidos emojis, signos sueltos, un texto con `DROP TABLE` (las
consultas SQL usan parámetros) y un mensaje de 5.000 caracteres. La prueba
`test_si_el_modelo_falla_responde_en_modo_demo` simula una API key sin créditos: el agente responde
con la base y la traza registra el error del modelo y el respaldo.

### H10. Lo que falta medir
El modo Claude no se pudo medir porque la API key no tiene créditos. Con créditos basta
`python scripts/evaluar.py --modo claude`; ahí aparecerán tokens por turno y la consistencia al
repetir dejará de ser 100 % trivial, porque un modelo de lenguaje no siempre responde igual.

## 3. Recomendaciones basadas en los datos (material para IE5 e IE7)

| # | Recomendación | Dato que la respalda | Métrica que debería mejorar |
| --- | --- | --- | --- |
| R1 | Ampliar las reglas de seguridad para tolerar palabras intermedias (`fren\w*.{0,20}(no responde\|fall)`) y agregar un segundo filtro semántico (el modelo de lenguaje o un clasificador) que solo pueda **subir** el nivel de riesgo, nunca bajarlo | H2: 4/16 riesgos sin detectar | Precisión en `riesgo` → 100 % |
| R2 | Guardar el nivel de riesgo en el estado de la conversación y no bajarlo hasta que el usuario cambie de tema | H2, caso R16 | R16 correcto |
| R3 | Separar "no mencionó vehículo" de "mencionó uno que no está": responder *"todavía no tengo el Corolla en mi base; revisa el manual"* y contar en las trazas qué modelos se piden para decidir cuáles agregar | H1: 0/4 | Precisión `vehiculo_desconocido` |
| R4 | Normalizar guiones en alias y usar coincidencia aproximada (por ejemplo `difflib`) para palabras clave | H3 | Consistencia ante paráfrasis ≥ 90 % |
| R5 | Extraer el año del mensaje y pasarlo a `buscar_vehiculo` | H4 | F07 correcto |
| R6 | Compilar el grafo una sola vez y compartirlo entre usuarios (el usuario ya viaja en el estado) | H6: 19 ms por construcción | Latencia por usuario nuevo |
| R7 | Calcular `buscar_vehiculo` una sola vez en `interpretar` y precompilar las expresiones regulares; precargar la base al iniciar | H5, H7 | p95 de `interpretar`, primer turno |
| R8 | En producción, dejar las trazas siempre activas pero medir memoria solo por muestreo | H8 | Sobrecarga < 10 % |
| R9 | Correr `scripts/evaluar.py` en cada cambio (o en GitHub Actions) y comparar con la línea base | Todos | Evitar regresiones |

### Escalabilidad y sostenibilidad

- **Datos:** con 16 vehículos los JSON en memoria bastan; con cientos conviene una base de datos
  (SQLite/PostgreSQL) con índice por marca y modelo.
- **Memoria y checkpointer:** `SqliteSaver` sirve para un computador; con varios usuarios a la vez se
  cambia por un checkpointer de PostgreSQL. H5 indica que este componente es el que más pesa.
- **Trazas:** el JSONL crece sin límite. Para producción: rotación diaria, retención acotada (por
  ejemplo 30 días) y envío a una plataforma estándar (OpenTelemetry con Grafana, o LangSmith).
- **Costo en modo Claude:** monitorear tokens por turno y respuestas que usan el respaldo; las
  preguntas frecuentes (aceite, estanque) se pueden responder sin llamar al modelo, como ya hace el
  modo demo.
- **Alertas:** usar las metas del dashboard como objetivos de servicio (p95 ≤ 50 ms en demo,
  excepciones ≤ 1 %, 100 % de riesgos detectados) y avisar cuando se incumplan.

## 4. Ética y privacidad (material para IE8)

- **Marco legal en Chile:** la Ley 19.628 sobre protección de la vida privada regula el tratamiento
  de datos personales. La Ley 21.719 (2024) la reforma y crea la Agencia de Protección de Datos
  Personales; su entrada en vigencia está prevista para diciembre de 2026 (confirmar la fecha en la
  BCN antes de la presentación).
- **Qué datos trata MecaIA:** nombre de usuario, vehículos, kilometraje y mantenciones. No pide RUT,
  dirección ni patente.
- **Minimización:** las trazas no guardan el nombre del usuario, sino un hash irreversible
  (`u_75cee5b221`). El texto de los mensajes se puede desactivar (`MECAIA_TRAZAS_TEXTO=0`) y las
  respuestas se recortan a 400 caracteres.
- **Derecho de cancelación:** `python main.py --usuario ana --borrar-mis-datos` borra los vehículos,
  mantenciones y trazas de ese usuario.
- **Seguridad de la información:** la API key solo vive en una variable de entorno; las consultas a
  SQLite usan parámetros (probado con `DROP TABLE` en X03); `.gitignore` excluye bases de datos y logs.
- **Seguridad física del usuario:** el chequeo de seguridad corre en código antes del modelo y deriva
  al mecánico de confianza. H2 muestra que las reglas fijas no bastan, por eso R1 y R2 son prioridad.
- **Transparencia:** los datos técnicos están marcados `verificado: false` y el agente lo avisa; no
  reemplaza a un profesional.
- **Uso de IA en el proyecto:** declarar en el informe qué herramientas de IA usaron y para qué.

## 5. Conclusiones

_(Sección para el equipo. La pauta no permite redactarla con IA.)_

## 6. Reflexiones individuales

_(Cada integrante escribe la suya, sin apoyo de IA.)_

## Referencias sugeridas (APA 7)

Revisen cada referencia antes de usarla.

- Beyer, B., Jones, C., Petoff, J., & Murphy, N. R. (Eds.). (2016). *Site reliability engineering: How
  Google runs production systems*. O'Reilly Media. https://sre.google/sre-book/table-of-contents/
- Biblioteca del Congreso Nacional de Chile. (1999). *Ley 19.628 sobre protección de la vida privada*.
  https://www.bcn.cl/leychile/navegar?idNorma=141599
- Biblioteca del Congreso Nacional de Chile. (2024). *Ley 21.719 que regula la protección y el
  tratamiento de los datos personales y crea la Agencia de Protección de Datos Personales*.
  https://www.bcn.cl/leychile/
- LangChain. (2025). *LangGraph documentation*. https://langchain-ai.github.io/langgraph/
- National Institute of Standards and Technology. (2023). *Artificial intelligence risk management
  framework (AI RMF 1.0)* (NIST AI 100-1). https://doi.org/10.6028/NIST.AI.100-1
- OpenTelemetry. (s.f.). *Observability primer*. https://opentelemetry.io/docs/concepts/observability-primer/
- Snowflake. (s.f.). *Streamlit documentation*. https://docs.streamlit.io/
- UNESCO. (2021). *Recomendación sobre la ética de la inteligencia artificial*.
  https://unesdoc.unesco.org/ark:/48223/pf0000381137_spa
