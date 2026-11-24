import importlib.util
from pathlib import Path

import pytest

from mecaia import grafo
from mecaia.grafo import MENSAJE_ERROR, MecaIA
from mecaia.memoria import Memoria
from mecaia.observabilidad import Trazador, anonimizar, leer_trazas

RAIZ = Path(__file__).resolve().parent.parent


def cargar_evaluar():
    spec = importlib.util.spec_from_file_location("evaluar", RAIZ / "scripts" / "evaluar.py")
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


@pytest.fixture
def ruta(tmp_path):
    return tmp_path / "trazas.jsonl"


def test_registra_nodos_y_turno(ruta):
    agente = MecaIA("ana", Memoria(":memory:"), trazador=Trazador(ruta))
    agente.responder("qué aceite lleva mi yamaha r3")
    eventos = leer_trazas(ruta)
    nodos = [e["nodo"] for e in eventos if e["tipo"] == "nodo"]
    turno = next(e for e in eventos if e["tipo"] == "turno")
    assert nodos == ["seguridad", "interpretar", "responder"] == turno["ruta"]
    assert turno["estado"] == "ok" and turno["vehiculo_id"] == "yamaha_r3_2015"
    assert turno["duracion_ms"] > 0 and all(e["turno_id"] == turno["turno_id"] for e in eventos)


def test_riesgo_queda_trazado(ruta):
    agente = MecaIA("ana", Memoria(":memory:"), trazador=Trazador(ruta))
    agente.responder("mi moto no frena")
    turno = leer_trazas(ruta)[-1]
    assert turno["nodo_final"] == "recomendar_mecanico" and turno["seguridad"] == "detener"


def test_no_guarda_el_nombre_del_usuario(ruta):
    MecaIA("ana_perez", Memoria(":memory:"), trazador=Trazador(ruta)).responder("hola")
    contenido = ruta.read_text(encoding="utf-8")
    assert "ana_perez" not in contenido and anonimizar("ana_perez") in contenido


def test_puede_omitir_el_texto(ruta):
    MecaIA("ana", Memoria(":memory:"), trazador=Trazador(ruta, guardar_texto=False)).responder("aceite r3")
    turno = leer_trazas(ruta)[-1]
    assert turno["mensaje"] is None and turno["respuesta"] is None and turno["largo_mensaje"] == 9


def test_mide_memoria_solo_si_se_pide(ruta):
    MecaIA("ana", Memoria(":memory:"), trazador=Trazador(ruta, medir_memoria=False)).responder("hola")
    assert all(e["memoria_pico_kb"] is None for e in leer_trazas(ruta) if e["tipo"] == "nodo")


class LLMSinCreditos:
    """Simula una API key sin créditos: toda llamada al modelo falla."""

    def bind_tools(self, herramientas):
        return self

    def invoke(self, mensajes):
        raise RuntimeError("credit balance is too low")


def test_si_el_modelo_falla_responde_en_modo_demo(ruta):
    agente = MecaIA("ana", Memoria(":memory:"), llm=LLMSinCreditos(), trazador=Trazador(ruta))
    respuesta = agente.responder("qué aceite lleva mi yamaha r3")
    eventos = leer_trazas(ruta)
    turno = eventos[-1]
    assert "10W-40" in respuesta
    assert turno["respaldo_demo"] and "credit balance" in turno["error_modelo"]
    assert any(e["tipo"] == "nodo" and e["nodo"] == "agente" and e["estado"] == "error" for e in eventos)


def test_error_interno_da_mensaje_seguro(ruta, monkeypatch):
    def falla(_):
        raise ValueError("regla rota")
    monkeypatch.setattr(grafo.seguridad, "evaluar", falla)
    agente = MecaIA("ana", Memoria(":memory:"), trazador=Trazador(ruta))
    assert agente.responder("hola") == MENSAJE_ERROR
    turno = leer_trazas(ruta)[-1]
    assert turno["estado"] == "error" and "regla rota" in turno["error"]


def test_percentiles_y_chequeos():
    evaluar = cargar_evaluar()
    assert evaluar.percentil([1, 2, 3, 4, 5], 50) == 3
    assert evaluar.percentil([1, 2, 3, 4, 5], 95) == 4.8
    turno = {"nodo_final": "recomendar_mecanico", "seguridad": "detener", "vehiculo_id": None, "estado": "ok"}
    chequeos = evaluar.evaluar_turno({"accion": "mecanico", "seguridad": "detener",
                                      "no_contiene": ["paso a paso"]}, turno, "Acude a tu mecánico")
    assert all(chequeos.values())
    chequeos = evaluar.evaluar_turno({"accion": "responder"}, turno, "")
    assert chequeos["accion"] is False


def test_casos_de_evaluacion_bien_formados():
    import json
    casos = json.loads((RAIZ / "evaluacion" / "casos.json").read_text(encoding="utf-8"))["casos"]
    assert len(casos) >= 50 and len({c["id"] for c in casos}) == len(casos)
    assert all(any("esperado" in t for t in c["turnos"]) for c in casos)


def test_borrar_datos_del_usuario(ruta):
    from mecaia.observabilidad import borrar_trazas_usuario
    memoria = Memoria(":memory:")
    trazador = Trazador(ruta)
    MecaIA("ana", memoria, trazador=trazador).responder("aceite para mi r3")
    MecaIA("luis", memoria, trazador=trazador).responder("hola")
    memoria.registrar_mantencion("ana", "yamaha_r3_2015", "cambio_aceite", 1000)
    assert memoria.borrar_usuario("ana") == 1 and memoria.vehiculos("ana") == []
    assert borrar_trazas_usuario(ruta, "ana") == 4
    assert {e["turno_id"] for e in leer_trazas(ruta)} == {e["turno_id"] for e in leer_trazas(ruta) if e["tipo"] == "turno"}
    assert anonimizar("ana") not in ruta.read_text(encoding="utf-8")
