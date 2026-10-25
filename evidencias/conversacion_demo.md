# Conversación de prueba en modo demo

Generado con `python scripts/generar_evidencias.py`. Usuario: ana. La conversación "otra" no comparte mensajes con la "principal": lo que recuerda viene de la memoria de largo plazo.

## Conversación "principal"

**Usuario:** hola

> Plan del agente: Seguridad: ok → Vehículo: 0 candidatos → Intención: conversación (saludo) → Decisión: responder con cordialidad y ofrecer más ayuda

**MecaIA:**

¡Hola! Soy MecaIA, tu asistente para la mantención de autos y motos. Puedo ayudarte con:
- Cambio de aceite, revisión de pastillas de freno y presión de neumáticos, paso a paso
- Cada cuánto se hace cada mantención y cuánto demora (bujías, balatas, filtro de aire, correa de distribución, cadena y más)
- Cuánto rinde el estanque de tu auto o moto
- Anotar las mantenciones que hagas para recordarte la próxima

¿En qué te ayudo hoy?

---

**Usuario:** ¿Qué aceite necesito para mi Kawasaki 400?

> Plan del agente: Seguridad: ok → Vehículo: 3 candidatos → Intención: consulta; procedimiento: cambio_aceite → Decisión: preguntar antes de dar datos

**MecaIA:**

Hay más de un modelo que calza. ¿Cuál es el tuyo?
1. Kawasaki KZ400 (clásica) (1974-1984)
2. Kawasaki Ninja 400 (2018-2024)
3. Kawasaki Z400 (2019-2024)

---

**Usuario:** la ninja

> Plan del agente: Seguridad: ok → Vehículo: kawasaki_ninja_400_2018, respuesta a la pregunta anterior → Intención: consulta; procedimiento: cambio_aceite → Decisión: responder desde la base

**MecaIA:**

**Cambio de aceite de motor para tu Kawasaki Ninja 400**

**Lo que necesitas**
- Aceite: SAE 10W-40, API SG o superior, JASO MA o MA2 (aceite para motos con embrague húmedo)
- Cantidad: 2.0 L cambiando el filtro (1.6 L sin cambiarlo)
- Filtro: Kawasaki 16097-0008 (equivalentes: HiFlo HF303)
- Torque del tapón del cárter: 30 N·m
- Llave para el tapón: 17 mm
_Datos por confirmar con el manual. Fuente: Manual del propietario Kawasaki Ninja 400._

**Herramientas**
- Llave de copa o punta corona para el tapón del cárter (medida según el vehículo)
- Llave para filtro de aceite (de cinta, cadena o copa)
- Bandeja o recipiente para recibir el aceite usado (mínimo la capacidad del motor)
- Embudo
- Guantes y paños
- Torquímetro (recomendado)

**Si no tienes las herramientas**
- Si no tienes llave de filtro: hay modelos económicos de cinta; muchas tiendas de repuestos las prestan o las venden por poco.
- Si no tienes torquímetro: aprieta firme sin forzar y revisa que no gotee; nunca apretar en exceso porque se daña la rosca del cárter.
- Si no tienes donde dejar el aceite usado o prefieres no hacerlo: compra el aceite y el filtro correctos y llévalos a un lubricentro; pide solo la mano de obra.
- En moto, si no tienes atril central: pide ayuda para mantenerla vertical; con la moto inclinada en el atril lateral queda aceite sin drenar y la lectura del nivel es incorrecta.

**Paso a paso**
1. Calienta el motor 2 a 3 minutos (el aceite tibio drena mejor) y apágalo. No lo dejes muy caliente: puede quemar.
2. Pon el vehículo en superficie plana y firme; en moto, vertical o en atril central.
3. Coloca la bandeja bajo el tapón del cárter y retira el tapón de llenado de arriba para que drene más rápido.
4. Afloja y saca el tapón del cárter; deja drenar por completo (5 a 10 minutos).
5. Retira el filtro de aceite y deja drenar su alojamiento.
6. Unta con aceite nuevo la goma del filtro nuevo y atorníllalo a mano hasta que toque; luego aprieta según el torque indicado.
7. Instala el tapón del cárter con arandela nueva y apriétalo al torque indicado.
8. Llena con la cantidad indicada de aceite, de a poco, usando el embudo.
9. Enciende el motor 1 minuto, apágalo, espera 2 a 3 minutos y revisa el nivel en la mirilla o varilla. Completa si falta.
10. Revisa que no haya goteo en tapón ni filtro.

**No olvides**
- Cambia también el filtro de aceite: aceite nuevo con filtro viejo se contamina rápido.
- Usa una arandela (golilla) nueva en el tapón del cárter para evitar filtraciones.
- En motos con embrague húmedo usa aceite JASO MA o MA2; un aceite de auto con aditivos de fricción puede hacer patinar el embrague.
- Anota el kilometraje del cambio para saber cuándo toca el próximo.
- Lleva el aceite usado a un punto de reciclaje; nunca lo botes al desagüe o a la tierra.

**Seguridad**
- El aceite y el escape pueden estar muy calientes: usa guantes.
- Nunca te pongas bajo un auto sostenido solo por la gata: usa caballetes (torres) o rampas.

**Acude a tu mecánico de confianza si**
- La rosca del tapón está dañada o el tapón no aprieta.
- El aceite drenado sale lechoso (posible mezcla con refrigerante), con partículas metálicas o con olor fuerte a combustible.
- La luz de presión de aceite queda encendida después del cambio.

¿Tienes alguna otra duda? Aquí estoy para ayudarte.

---

**Usuario:** ya cambié el aceite a los 12.000 km

> Plan del agente: Seguridad: ok → Vehículo: kawasaki_ninja_400_2018, memoria de corto plazo (esta conversación) → Intención: registro; procedimiento: cambio_aceite → Decisión: guardar la mantención en memoria de largo plazo

**MecaIA:**

Listo, anoté: cambio de aceite de motor de tu Kawasaki Ninja 400 a los 12.000 km. Te toca el próximo cerca de los 18.000 km. ¿Tienes alguna otra duda? Aquí estoy para ayudarte.

---

**Usuario:** cómo reviso la presión de los neumáticos

> Plan del agente: Seguridad: ok → Vehículo: kawasaki_ninja_400_2018, memoria de corto plazo (esta conversación) → Intención: consulta; procedimiento: presion_neumaticos → Decisión: responder desde la base

**MecaIA:**

**Revisión de presión de neumáticos para tu Kawasaki Ninja 400**

**Herramientas**
- Manómetro de presión
- Compresor o inflador

**Si no tienes las herramientas**
- Casi todas las bencineras tienen inflador con manómetro, muchas veces gratis.

**Paso a paso**
1. Revisa con los neumáticos fríos (antes de andar o tras 3 horas detenido).
2. Busca la presión correcta en la etiqueta del vehículo (marco de la puerta, tapa de combustible o basculante en motos) o en el manual.
3. Mide cada neumático y ajusta a la presión indicada.
4. Revisa también desgaste, cortes o deformaciones.

**No olvides**
- La presión indicada en el costado del neumático es la máxima, no la recomendada.
- Revisa la presión al menos una vez al mes y antes de un viaje largo.

**Seguridad**
- No conduzcas con un neumático con corte, globo o tela a la vista.

**Acude a tu mecánico de confianza si**
- El neumático pierde aire de forma repetida.
- Hay un globo, corte en el costado o desgaste irregular marcado.

¿Tienes alguna otra duda? Aquí estoy para ayudarte.

---

**Usuario:** mi moto no frena, ¿qué hago?

> Plan del agente: Seguridad: detener (Falla de frenos) → Decisión: recomendar acudir al mecánico de confianza, sin pasos de reparación

**MecaIA:**

Esto es un tema de seguridad (falla de frenos), así que no te voy a dar pasos para repararlo tú. Lo mejor es que no uses el vehículo y acudas a tu mecánico de confianza (si no es seguro moverlo, pide una grúa o asistencia en ruta). Cuéntale cuándo empezó, en qué condiciones pasa y si notas algún ruido u olor.

---

## Conversación "otra"

**Usuario:** cambio de aceite

> Plan del agente: Seguridad: ok → Vehículo: kawasaki_ninja_400_2018, memoria de largo plazo (vehículo guardado) → Intención: consulta; procedimiento: cambio_aceite → Decisión: responder desde la base

**MecaIA:**

**Cambio de aceite de motor para tu Kawasaki Ninja 400**

Según tu historial, el último cambio fue el 2026-10-25 a los 12.000 km; el próximo toca cerca de los 18.000 km.

**Lo que necesitas**
- Aceite: SAE 10W-40, API SG o superior, JASO MA o MA2 (aceite para motos con embrague húmedo)
- Cantidad: 2.0 L cambiando el filtro (1.6 L sin cambiarlo)
- Filtro: Kawasaki 16097-0008 (equivalentes: HiFlo HF303)
- Torque del tapón del cárter: 30 N·m
- Llave para el tapón: 17 mm
_Datos por confirmar con el manual. Fuente: Manual del propietario Kawasaki Ninja 400._

**Herramientas**
- Llave de copa o punta corona para el tapón del cárter (medida según el vehículo)
- Llave para filtro de aceite (de cinta, cadena o copa)
- Bandeja o recipiente para recibir el aceite usado (mínimo la capacidad del motor)
- Embudo
- Guantes y paños
- Torquímetro (recomendado)

**Si no tienes las herramientas**
- Si no tienes llave de filtro: hay modelos económicos de cinta; muchas tiendas de repuestos las prestan o las venden por poco.
- Si no tienes torquímetro: aprieta firme sin forzar y revisa que no gotee; nunca apretar en exceso porque se daña la rosca del cárter.
- Si no tienes donde dejar el aceite usado o prefieres no hacerlo: compra el aceite y el filtro correctos y llévalos a un lubricentro; pide solo la mano de obra.
- En moto, si no tienes atril central: pide ayuda para mantenerla vertical; con la moto inclinada en el atril lateral queda aceite sin drenar y la lectura del nivel es incorrecta.

**Paso a paso**
1. Calienta el motor 2 a 3 minutos (el aceite tibio drena mejor) y apágalo. No lo dejes muy caliente: puede quemar.
2. Pon el vehículo en superficie plana y firme; en moto, vertical o en atril central.
3. Coloca la bandeja bajo el tapón del cárter y retira el tapón de llenado de arriba para que drene más rápido.
4. Afloja y saca el tapón del cárter; deja drenar por completo (5 a 10 minutos).
5. Retira el filtro de aceite y deja drenar su alojamiento.
6. Unta con aceite nuevo la goma del filtro nuevo y atorníllalo a mano hasta que toque; luego aprieta según el torque indicado.
7. Instala el tapón del cárter con arandela nueva y apriétalo al torque indicado.
8. Llena con la cantidad indicada de aceite, de a poco, usando el embudo.
9. Enciende el motor 1 minuto, apágalo, espera 2 a 3 minutos y revisa el nivel en la mirilla o varilla. Completa si falta.
10. Revisa que no haya goteo en tapón ni filtro.

**No olvides**
- Cambia también el filtro de aceite: aceite nuevo con filtro viejo se contamina rápido.
- Usa una arandela (golilla) nueva en el tapón del cárter para evitar filtraciones.
- En motos con embrague húmedo usa aceite JASO MA o MA2; un aceite de auto con aditivos de fricción puede hacer patinar el embrague.
- Anota el kilometraje del cambio para saber cuándo toca el próximo.
- Lleva el aceite usado a un punto de reciclaje; nunca lo botes al desagüe o a la tierra.

**Seguridad**
- El aceite y el escape pueden estar muy calientes: usa guantes.
- Nunca te pongas bajo un auto sostenido solo por la gata: usa caballetes (torres) o rampas.

**Acude a tu mecánico de confianza si**
- La rosca del tapón está dañada o el tapón no aprieta.
- El aceite drenado sale lechoso (posible mezcla con refrigerante), con partículas metálicas o con olor fuerte a combustible.
- La luz de presión de aceite queda encendida después del cambio.

¿Tienes alguna otra duda? Aquí estoy para ayudarte.

---

**Usuario:** qué aceite lleva un Suzuki Alto

> Plan del agente: Seguridad: ok → Vehículo: suzuki_alto_08_2013, mencionado en el mensaje → Intención: consulta; procedimiento: cambio_aceite → Decisión: responder desde la base

**MecaIA:**

**Cambio de aceite de motor para tu Suzuki Alto 800**

**Lo que necesitas**
- Aceite: SAE 5W-30, API SN o superior
- Cantidad: no la tengo cargada; revisa el manual y llena de a poco mirando la varilla
_Datos por confirmar con el manual. Fuente: Valor de referencia, por contrastar con el manual del propietario._

**Herramientas**
- Llave de copa o punta corona para el tapón del cárter (medida según el vehículo)
- Llave para filtro de aceite (de cinta, cadena o copa)
- Bandeja o recipiente para recibir el aceite usado (mínimo la capacidad del motor)
- Embudo
- Guantes y paños
- Torquímetro (recomendado)

**Si no tienes las herramientas**
- Si no tienes llave de filtro: hay modelos económicos de cinta; muchas tiendas de repuestos las prestan o las venden por poco.
- Si no tienes torquímetro: aprieta firme sin forzar y revisa que no gotee; nunca apretar en exceso porque se daña la rosca del cárter.
- Si no tienes donde dejar el aceite usado o prefieres no hacerlo: compra el aceite y el filtro correctos y llévalos a un lubricentro; pide solo la mano de obra.
- En moto, si no tienes atril central: pide ayuda para mantenerla vertical; con la moto inclinada en el atril lateral queda aceite sin drenar y la lectura del nivel es incorrecta.

**Paso a paso**
1. Calienta el motor 2 a 3 minutos (el aceite tibio drena mejor) y apágalo. No lo dejes muy caliente: puede quemar.
2. Pon el vehículo en superficie plana y firme; en moto, vertical o en atril central.
3. Coloca la bandeja bajo el tapón del cárter y retira el tapón de llenado de arriba para que drene más rápido.
4. Afloja y saca el tapón del cárter; deja drenar por completo (5 a 10 minutos).
5. Retira el filtro de aceite y deja drenar su alojamiento.
6. Unta con aceite nuevo la goma del filtro nuevo y atorníllalo a mano hasta que toque; luego aprieta según el torque indicado.
7. Instala el tapón del cárter con arandela nueva y apriétalo al torque indicado.
8. Llena con la cantidad indicada de aceite, de a poco, usando el embudo.
9. Enciende el motor 1 minuto, apágalo, espera 2 a 3 minutos y revisa el nivel en la mirilla o varilla. Completa si falta.
10. Revisa que no haya goteo en tapón ni filtro.

**No olvides**
- Cambia también el filtro de aceite: aceite nuevo con filtro viejo se contamina rápido.
- Usa una arandela (golilla) nueva en el tapón del cárter para evitar filtraciones.
- Anota el kilometraje del cambio para saber cuándo toca el próximo.
- Lleva el aceite usado a un punto de reciclaje; nunca lo botes al desagüe o a la tierra.

**Seguridad**
- El aceite y el escape pueden estar muy calientes: usa guantes.
- Nunca te pongas bajo un auto sostenido solo por la gata: usa caballetes (torres) o rampas.

**Acude a tu mecánico de confianza si**
- La rosca del tapón está dañada o el tapón no aprieta.
- El aceite drenado sale lechoso (posible mezcla con refrigerante), con partículas metálicas o con olor fuerte a combustible.
- La luz de presión de aceite queda encendida después del cambio.

¿Tienes alguna otra duda? Aquí estoy para ayudarte.

---

**Usuario:** cuánto rinde el estanque de mi Yamaha R3

> Plan del agente: Seguridad: ok → Vehículo: yamaha_r3_2015, mencionado en el mensaje → Intención: estanque; procedimiento: ninguno → Decisión: responder con el estanque y la autonomía estimada

**MecaIA:**

**Estanque de tu Yamaha YZF-R3**

- Capacidad del estanque: 14 L
- Rendimiento aproximado: 25 km por litro
- Autonomía estimada con el estanque lleno: unos 350 km

El rendimiento real cambia según cómo manejes, la carga, el tráfico y la mantención. Para no quedarte en pana, carga cuando se encienda la luz de reserva.

_Datos por confirmar con el manual. Fuente: Valor de referencia (rendimiento mixto aproximado), por contrastar con el manual._

¿Tienes alguna otra duda? Aquí estoy para ayudarte.

---

**Usuario:** cada cuánto se cambian las bujías de un auto

> Plan del agente: Seguridad: ok → Vehículo: yamaha_r3_2015, memoria de corto plazo (esta conversación) → Intención: intervalo; ítems: bujias → Decisión: responder con intervalos de mantención

**MecaIA:**

**Cada cuánto: Bujías para tu Yamaha YZF-R3**

- Cada cuánto: Cada 8.000 a 12.000 km (convencionales)
- Tiempo de trabajo: 30 a 60 minutos; más en motos carenadas

_Rangos generales de referencia; el manual de tu vehículo siempre manda._

¿Tienes alguna otra duda? Aquí estoy para ayudarte.

---

**Usuario:** cada cuánto cambio las balatas de mi moto

> Plan del agente: Seguridad: ok → Vehículo: yamaha_r3_2015, memoria de corto plazo (esta conversación) → Intención: intervalo; ítems: pastillas_freno → Decisión: responder con intervalos de mantención

**MecaIA:**

**Cada cuánto: Pastillas de freno (balatas) para tu Yamaha YZF-R3**

- Cada cuánto: Revisarlas cada 5.000 km; se cambian típicamente entre 10.000 y 20.000 km según el uso
- Tiempo de trabajo: 30 a 60 minutos por rueda
- Nota: Se cambian cuando queda menos de 2 a 3 mm de material. Los frenos son críticos: si no tienes experiencia, que lo haga tu mecánico de confianza.

_Rangos generales de referencia; el manual de tu vehículo siempre manda._

¿Tienes alguna otra duda? Aquí estoy para ayudarte.

---

**Usuario:** muchas gracias

> Plan del agente: Seguridad: ok → Vehículo: yamaha_r3_2015, memoria de corto plazo (esta conversación) → Intención: conversación (gracias) → Decisión: responder con cordialidad y ofrecer más ayuda

**MecaIA:**

¡No hay de qué! Estoy aquí para ayudarte. Si tienes alguna otra duda con tu Yamaha YZF-R3 o con otro vehículo, escríbeme cuando quieras.

---
