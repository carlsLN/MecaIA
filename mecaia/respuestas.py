"""Textos de respuesta armados desde la base de conocimiento (sin modelo de lenguaje)."""
from .texto import normalizar


def elegir(texto: str, candidatos: list[dict]) -> list[dict]:
    t = normalizar(texto)
    for i, v in enumerate(candidatos, 1):
        if t.strip(" .") == str(i):
            return [v]
    elegidos = [v for v in candidatos if normalizar(v["modelo"]).split()[0] in t]
    return elegidos


def derivacion(motivos: list[str]) -> str:
    return (f"Esto es un tema de seguridad ({', '.join(motivos).lower()}). "
            "No te voy a dar pasos para repararlo tú: no uses el vehículo y llévalo a un mecánico "
            "(si no es seguro moverlo, pide una grúa o asistencia en ruta). "
            "Cuéntale cuándo empezó, en qué condiciones pasa y cualquier ruido u olor.")


def _lista(items: list[str]) -> str:
    return "\n".join(f"- {i}" for i in items)


def formatear(p: dict, v: dict, ultimo_cambio: dict | None = None) -> str:
    nombre = f"{v['marca']} {v['modelo']}"
    partes = [f"**{p['nombre']} para tu {nombre}**"]
    intervalo = v.get("aceite_motor", {}).get("intervalo_km")
    if p["id"] == "cambio_aceite" and ultimo_cambio and ultimo_cambio.get("km") and intervalo:
        partes.append(f"Según tu historial, el último cambio fue el {ultimo_cambio['fecha']} a los "
                      f"{_km(ultimo_cambio['km'])}; el próximo toca cerca de los "
                      f"{_km(ultimo_cambio['km'] + intervalo)}.")

    if p["id"] == "cambio_aceite":
        a = v.get("aceite_motor", {})
        if not a.get("viscosidad"):
            partes.append(f"No tengo datos de aceite cargados para la {nombre}. Revisa el manual de servicio "
                          "o consulta a un mecánico; no te voy a dar un dato inventado.")
            return "\n\n".join(partes)
        lineas = [f"- Aceite: {a['viscosidad']}, {a['norma']}"]
        con, sin = a.get("capacidad_con_filtro_l"), a.get("capacidad_sin_filtro_l")
        if con and sin:
            lineas.append(f"- Cantidad: {con} L cambiando el filtro ({sin} L sin cambiarlo)")
        elif con or sin:
            lineas.append(f"- Cantidad: {con or sin} L {'cambiando el filtro' if con else 'sin cambiar el filtro'}")
        else:
            lineas.append("- Cantidad: no la tengo cargada; revisa el manual y llena de a poco mirando la varilla")
        f = v.get("filtro_aceite")
        if f and f.get("codigo_original"):
            equiv = f" (equivalentes: {', '.join(f['equivalentes'])})" if f.get("equivalentes") else ""
            lineas.append(f"- Filtro: {f['codigo_original']}{equiv}")
        t = v.get("torques_nm", {})
        if t.get("tapon_carter"):
            lineas.append(f"- Torque del tapón del cárter: {t['tapon_carter']} N·m")
        m = v.get("medidas_herramientas", {})
        if m.get("tapon_carter_mm"):
            lineas.append(f"- Llave para el tapón: {m['tapon_carter_mm']} mm")
        if v.get("notas"):
            lineas.append(f"- Nota: {v['notas']}")
        no_verificado = any(not d.get("verificado", True) for d in (a, f or {}, t, m) if d)
        if no_verificado:
            lineas.append(f"_Datos por confirmar con el manual. Fuente: {a['fuente']}._")
        partes.append("**Lo que necesitas**\n" + "\n".join(lineas))

    partes.append("**Herramientas**\n" + _lista(p["herramientas"]))
    partes.append("**Si no tienes las herramientas**\n" + _lista(p["alternativas_sin_herramientas"]))
    partes.append("**Paso a paso**\n" + "\n".join(f"{i}. {s}" for i, s in enumerate(p["pasos"], 1)))
    recordatorios = p["recordatorios"]
    if v["tipo"] == "auto":
        recordatorios = [r for r in recordatorios if "embrague húmedo" not in r]
    partes.append("**No olvides**\n" + _lista(recordatorios))
    partes.append("**Seguridad**\n" + _lista(p["advertencias_seguridad"]))
    partes.append("**Ve al mecánico si**\n" + _lista(p["derivar_si"]))
    return "\n\n".join(partes)


def _km(km: int) -> str:
    return f"{km:,} km".replace(",", ".")


def registro_confirmado(v: dict, tipo: str, nombre: str, km: int | None) -> str:
    texto = f"Listo, anoté: {nombre.lower()} de tu {v['marca']} {v['modelo']}"
    intervalo = v.get("aceite_motor", {}).get("intervalo_km")
    if km:
        texto += f" a los {_km(km)}"
        if tipo == "cambio_aceite" and intervalo:
            texto += f". Te toca el próximo cerca de los {_km(km + intervalo)}"
    return texto + "."


def pedir_vehiculo(candidatos: list[dict]) -> str:
    if not candidatos:
        return "¿Para qué vehículo es? Dime marca, modelo y, si puedes, el año."
    opciones = "\n".join(
        f"{i}. {v['marca']} {v['modelo']} ({v['anios'][0]}-{v['anios'][1]})"
        for i, v in enumerate(candidatos, 1)
    )
    return f"Hay más de un modelo que calza. ¿Cuál es el tuyo?\n{opciones}"


SIN_PROCEDIMIENTO = ("En modo demo puedo ayudarte con: cambio de aceite, revisión de pastillas de freno "
                     "y presión de neumáticos. ¿Cuál necesitas y para qué vehículo?")
