import json
import os
import re

from api_sensores import sensores_bp
from datetime import datetime
from pathlib import Path

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    jsonify
)

from recordatorios import obtener_riegos_pendientes


app = Flask(__name__)
app.register_blueprint(sensores_bp)

app.secret_key = os.environ.get(
    "FLASK_SECRET_KEY",
    "clave-solo-para-desarrollo-local"
)


# ==============================
# CONFIGURACIÓN
# ==============================

DIAS_SEMANA = [
    "lunes",
    "martes",
    "miercoles",
    "jueves",
    "viernes",
    "sabado",
    "domingo"
]

CALENDARIO_FILE = (
    Path(__file__).resolve().parent
    / "data"
    / "calendario.json"
)


# ==============================
# LEER CALENDARIO
# ==============================

def leer_calendario():

    if not CALENDARIO_FILE.exists():
        return []

    with open(
        CALENDARIO_FILE,
        "r",
        encoding="utf-8"
    ) as archivo:
        return json.load(archivo)


# ==============================
# GUARDAR CALENDARIO
# ==============================

def guardar_calendario(calendario):

    CALENDARIO_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    archivo_temporal = CALENDARIO_FILE.with_suffix(
        ".tmp"
    )

    with open(
        archivo_temporal,
        "w",
        encoding="utf-8"
    ) as archivo:

        json.dump(
            calendario,
            archivo,
            indent=4,
            ensure_ascii=False
        )

    archivo_temporal.replace(
        CALENDARIO_FILE
    )


# ==============================
# PÁGINA PRINCIPAL
# ==============================

@app.route("/")
def inicio():

    calendario = leer_calendario()

    return render_template(
        "index.html",
        calendario=calendario,
        dias=DIAS_SEMANA
    )


# ==============================
# RF1 - AGREGAR RIEGO
# ==============================

@app.route("/calendario", methods=["POST"])
def agregar_riego():

    dia = request.form.get("dia", "").strip()
    hora = request.form.get("hora", "").strip()

    if dia not in DIAS_SEMANA:

        flash(
            "Debe seleccionar un día válido.",
            "error"
        )

        return redirect(url_for("inicio"))

    if not re.fullmatch(
        r"(?:[01]\d|2[0-3]):[0-5]\d",
        hora
    ):

        flash(
            "Debe ingresar una hora válida.",
            "error"
        )

        return redirect(url_for("inicio"))

    calendario = leer_calendario()

    for riego in calendario:

        if (
            riego["dia"] == dia
            and riego["hora"] == hora
        ):

            flash(
                "Ese horario ya está registrado.",
                "error"
            )

            return redirect(url_for("inicio"))

    calendario.append({
        "dia": dia,
        "hora": hora
    })

    calendario.sort(
        key=lambda riego: (
            DIAS_SEMANA.index(riego["dia"]),
            riego["hora"]
        )
    )

    guardar_calendario(calendario)

    flash(
        "Horario de riego guardado correctamente.",
        "exito"
    )

    return redirect(url_for("inicio"))


# ==============================
# RF1 - ELIMINAR RIEGO
# ==============================

@app.route(
    "/calendario/eliminar",
    methods=["POST"]
)
def eliminar_riego():

    dia = request.form.get("dia")
    hora = request.form.get("hora")

    calendario = leer_calendario()

    calendario_actualizado = [
        riego
        for riego in calendario
        if not (
            riego["dia"] == dia
            and riego["hora"] == hora
        )
    ]

    if len(calendario_actualizado) == len(calendario):

        flash(
            "No se encontró el horario de riego.",
            "error"
        )

    else:

        guardar_calendario(calendario_actualizado)

        flash(
            "Horario eliminado correctamente.",
            "exito"
        )

    return redirect(url_for("inicio"))


# ==============================
# RF2 - CONSULTAR RECORDATORIOS
# ==============================

@app.route("/api/riegos/pendientes")
def consultar_riegos_pendientes():

    calendario = leer_calendario()

    ahora = datetime.now()

    pendientes = obtener_riegos_pendientes(
        calendario,
        ahora
    )

    return jsonify({
        "fecha": ahora.strftime("%Y-%m-%d"),
        "pendientes": pendientes
    })


# ==============================
# EJECUTAR APLICACIÓN
# ==============================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)