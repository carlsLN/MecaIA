import pytest
from langchain_core.messages import AIMessage

from mecaia import base_conocimiento as bc
from mecaia import seguridad
from mecaia.grafo import MecaIA
from mecaia.memoria import Memoria


@pytest.fixture
def memoria():
    return Memoria(":memory:")


def ids(vehiculos):
    return sorted(v["id"] for v in vehiculos)


def test_kawasaki_400_es_ambiguo():
    assert ids(bc.buscar_vehiculo("qué aceite necesito para mi Kawasaki 400?")) == [
        "kawasaki_kz400_1974", "kawasaki_ninja_400_2018", "kawasaki_z400_2019"]


def test_modelo_especifico_y_anio():
    assert ids(bc.buscar_vehiculo("mi Ninja 400")) == ["kawasaki_ninja_400_2018"]
    assert ids(bc.buscar_vehiculo("kawasaki 400 del 1980", anio=1980)) == ["kawasaki_kz400_1974"]


@pytest.mark.parametrize("texto, esperado", [
    ("Hyundai Accent", "hyundai_accent_14_2011"), ("mi elantra", "hyundai_elantra_16_2016"),
    ("Suzuki Swift", "suzuki_swift_12_2017"), ("Suzuki Alto", "suzuki_alto_08_2013"),
    ("Toyota Yaris", "toyota_yaris_15_2014"), ("Suzuki Gixxer 150", "suzuki_gixxer_150_2015"),
    ("KTM RC200", "ktm_rc_200_2014"), ("MT-03", "yamaha_mt03_2016"), ("Yamaha R3", "yamaha_r3_2015"),
    ("Yamaha R15", "yamaha_r15_v3_2017"), ("Honda CBR-250", "honda_cbr250r_2011"),
    ("Honda CBR-300", "honda_cbr300r_2014"), ("Honda CB-190R", "honda_cb190r_2015"),
])
def test_vehiculos_pedidos(texto, esperado):
    assert ids(bc.buscar_vehiculo(f"qué aceite uso en mi {texto}")) == [esperado]


@pytest.mark.parametrize("vehiculo_id", sorted(bc.vehiculos()))
def test_cada_vehiculo_responde_sin_errores(memoria, vehiculo_id):
    v = bc.obtener_vehiculo(vehiculo_id)
    respuesta = MecaIA("ana", memoria).responder(f"cambio de aceite para mi {v['alias'][0]}")
    assert v["modelo"] in respuesta and "None" not in respuesta


def test_procedimiento_por_palabras():
    assert bc.buscar_procedimiento("quiero cambiar el aceite")["id"] == "cambio_aceite"
    assert bc.buscar_procedimiento("cómo reviso la presión de los neumáticos")["id"] == "presion_neumaticos"


@pytest.mark.parametrize("texto", [
    "los frenos no responden", "siento olor a bencina", "sale humo del motor",
    "se encendió la luz de aceite", "el motor se sobrecalentó",
])
def test_seguridad_detener(texto):
    assert seguridad.evaluar(texto).nivel == "detener"


def test_seguridad_ok_y_precaucion():
    assert seguridad.evaluar("qué aceite uso").nivel == "ok"
    assert seguridad.evaluar("me chirrían los frenos").nivel == "precaucion"


def test_memoria(memoria):
    memoria.guardar_vehiculo("ana", "kawasaki_ninja_400_2018", anio=2020)
    memoria.registrar_mantencion("ana", "kawasaki_ninja_400_2018", "cambio_aceite", km=12000)
    [v] = memoria.vehiculos("ana")
    assert v["anio"] == 2020 and v["km"] == 12000
    assert v["mantenciones"][0]["tipo"] == "cambio_aceite"
    assert memoria.vehiculos("otro") == []


def test_flujo_kawasaki_con_aclaracion(memoria):
    agente = MecaIA("ana", memoria)
    pregunta = agente.responder("¿Qué aceite necesito para mi Kawasaki 400?")
    assert "¿Cuál es el tuyo?" in pregunta and "Ninja 400" in pregunta
    assert agente.ultimo_plan[-1] == "Decisión: preguntar antes de dar datos"
    # Memoria de corto plazo: recuerda la pregunta pendiente y el procedimiento.
    respuesta = agente.responder("la ninja")
    assert "10W-40" in respuesta and "2.0 L" in respuesta
    assert "filtro de aceite" in respuesta.lower() and "Si no tienes las herramientas" in respuesta


def test_memoria_largo_plazo_entre_conversaciones(memoria):
    MecaIA("ana", memoria).responder("aceite para mi ninja 400")
    nueva = MecaIA("ana", memoria)  # otra sesión, sin historial de mensajes
    respuesta = nueva.responder("cómo reviso la presión de los neumáticos", conversacion="otra")
    assert "Ninja 400" in respuesta
    assert "memoria de largo plazo" in nueva.ultimo_plan[1]


def test_registrar_mantencion_y_recordatorio(memoria):
    agente = MecaIA("ana", memoria)
    agente.responder("tengo una ninja 400")
    confirmacion = agente.responder("ya cambié el aceite a los 12.000 km")
    assert "18.000 km" in confirmacion
    assert memoria.vehiculos("ana")[0]["mantenciones"][0]["km"] == 12000
    assert "el próximo toca cerca de los 18.000 km" in agente.responder("cambio de aceite")


def test_no_inventa_datos(memoria):
    respuesta = MecaIA("ana", memoria).responder("aceite para mi kz400")
    assert "no te voy a dar un dato inventado" in respuesta


def test_deriva_en_riesgo(memoria):
    agente = MecaIA("ana", memoria)
    assert "mecánico" in agente.responder("mi moto no frena, ¿qué hago?")
    assert agente.ultimo_plan[-1].startswith("Decisión: derivar")


class LLMFalso:
    """Imita a ChatAnthropic: primero pide una herramienta y luego responde con texto."""

    def __init__(self):
        self.llamadas = []

    def bind_tools(self, herramientas):
        self.herramientas = [h.name for h in herramientas]
        return self

    def invoke(self, mensajes):
        self.llamadas.append(mensajes)
        if len(self.llamadas) == 1:
            return AIMessage("", tool_calls=[{"id": "t1", "name": "obtener_datos_vehiculo",
                                              "args": {"vehiculo_id": "kawasaki_ninja_400_2018"}}])
        return AIMessage("Usa 10W-40 y cambia el filtro.")


def test_modo_claude_usa_herramientas(memoria):
    llm = LLMFalso()
    agente = MecaIA("ana", memoria, llm)
    assert agente.responder("qué aceite uso en mi ninja 400") == "Usa 10W-40 y cambia el filtro."
    resultado_herramienta = llm.llamadas[1][-1]
    assert resultado_herramienta.type == "tool" and "10W-40" in resultado_herramienta.content
    assert "vehiculo_confirmado=kawasaki_ninja_400_2018" in llm.llamadas[0][0].content
    assert "registrar_mantencion" in llm.herramientas


def test_modo_claude_respeta_seguridad_en_codigo(memoria):
    llm = LLMFalso()
    assert "mecánico" in MecaIA("ana", memoria, llm).responder("siento olor a bencina")
    assert llm.llamadas == []  # el riesgo se resuelve antes de llamar al modelo
