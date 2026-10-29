import json
import os
import re

from pathlib import Path

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash
)


app = Flask(__name__)

app.secret_key = os.environ.get(
    "FLASK_SECRET_KEY",
    "clave-solo-para-desarrollo-local"
)


# ==============================
# CONFIGURACIÓN DEL CALENDARIO
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

    archivo_temporal = (
        CALENDARIO_FILE.with_suffix(".tmp")
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
# AGREGAR RIEGO
# ==============================

@app.route(
    "/calendario",
    methods=["POST"]
)
def agregar_riego():

    dia = request.form.get(
        "dia",
        ""
    ).strip()

    hora = request.form.get(
        "hora",
        ""
    ).strip()

    # Validar día
    if dia not in DIAS_SEMANA:

        flash(
            "Debe seleccionar un día válido.",
            "error"
        )

        return redirect(
            url_for("inicio")
        )

    # Validar hora
    if not re.fullmatch(
        r"(?:[01]\d|2[0-3]):[0-5]\d",
        hora
    ):

        flash(
            "Debe ingresar una hora válida.",
            "error"
        )

        return redirect(
            url_for("inicio")
        )

    calendario = leer_calendario()

    # Evitar duplicados
    for riego in calendario:

        if (
            riego["dia"] == dia
            and riego["hora"] == hora
        ):

            flash(
                "Ese horario ya está registrado.",
                "error"
            )

            return redirect(
                url_for("inicio")
            )

    # Agregar riego
    calendario.append({
        "dia": dia,
        "hora": hora
    })

    # Ordenar por día y hora
    calendario.sort(
        key=lambda riego: (
            DIAS_SEMANA.index(riego["dia"]),
            riego["hora"]
        )
    )

    guardar_calendario(
        calendario
    )

    flash(
        "Horario de riego guardado correctamente.",
        "exito"
    )

    return redirect(
        url_for("inicio")
    )


# ==============================
# ELIMINAR RIEGO
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

        guardar_calendario(
            calendario_actualizado
        )

        flash(
            "Horario eliminado correctamente.",
            "exito"
        )

    return redirect(
        url_for("inicio")
    )


# ==============================
# EJECUTAR APLICACIÓN
# ==============================

if __name__ == "__main__":

    app.run(debug=True)