"""Memoria persistente del usuario: sus vehículos y sus mantenciones (SQLite)."""
import sqlite3
from datetime import date
from pathlib import Path

ESQUEMA = """
CREATE TABLE IF NOT EXISTS vehiculos (
    id INTEGER PRIMARY KEY,
    usuario TEXT NOT NULL,
    vehiculo_id TEXT NOT NULL,
    apodo TEXT,
    anio INTEGER,
    km INTEGER
);
CREATE TABLE IF NOT EXISTS mantenciones (
    id INTEGER PRIMARY KEY,
    vehiculo INTEGER NOT NULL REFERENCES vehiculos(id),
    fecha TEXT NOT NULL,
    tipo TEXT NOT NULL,
    km INTEGER,
    notas TEXT
);
"""


class Memoria:
    def __init__(self, ruta: str | Path = "mecaia.db"):
        self.db = sqlite3.connect(ruta)
        self.db.row_factory = sqlite3.Row
        self.db.executescript(ESQUEMA)

    def guardar_vehiculo(self, usuario: str, vehiculo_id: str, anio: int | None = None,
                         km: int | None = None, apodo: str | None = None) -> int:
        existente = self.db.execute(
            "SELECT id FROM vehiculos WHERE usuario = ? AND vehiculo_id = ?", (usuario, vehiculo_id)
        ).fetchone()
        if existente:
            self.db.execute(
                "UPDATE vehiculos SET anio = COALESCE(?, anio), km = COALESCE(?, km), "
                "apodo = COALESCE(?, apodo) WHERE id = ?",
                (anio, km, apodo, existente["id"]),
            )
            self.db.commit()
            return existente["id"]
        cur = self.db.execute(
            "INSERT INTO vehiculos (usuario, vehiculo_id, apodo, anio, km) VALUES (?, ?, ?, ?, ?)",
            (usuario, vehiculo_id, apodo, anio, km),
        )
        self.db.commit()
        return cur.lastrowid

    def vehiculos(self, usuario: str) -> list[dict]:
        filas = self.db.execute("SELECT * FROM vehiculos WHERE usuario = ? ORDER BY id", (usuario,))
        resultado = []
        for f in filas:
            v = dict(f)
            v["mantenciones"] = [dict(m) for m in self.db.execute(
                "SELECT fecha, tipo, km, notas FROM mantenciones WHERE vehiculo = ? ORDER BY fecha DESC",
                (f["id"],),
            )]
            resultado.append(v)
        return resultado

    def registrar_mantencion(self, usuario: str, vehiculo_id: str, tipo: str,
                             km: int | None = None, notas: str | None = None,
                             fecha: str | None = None) -> None:
        rowid = self.guardar_vehiculo(usuario, vehiculo_id, km=km)
        self.db.execute(
            "INSERT INTO mantenciones (vehiculo, fecha, tipo, km, notas) VALUES (?, ?, ?, ?, ?)",
            (rowid, fecha or date.today().isoformat(), tipo, km, notas),
        )
        self.db.commit()
