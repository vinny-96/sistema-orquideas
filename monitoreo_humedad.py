
import math
import os
from datetime import datetime

import mysql.connector
from flask import Blueprint, current_app, jsonify, render_template

from lecturas_dao import LecturasDAO


monitoreo_bp = Blueprint("monitoreo", __name__)


def evaluar_humedad(humedad, minimo=75.0, maximo=85.0):
    """
    Evalua la humedad ambiental segun limites configurables.
    """

    valor = float(humedad)

    if not math.isfinite(valor) or not 0 <= valor <= 100:
        raise ValueError("La humedad debe estar entre 0 y 100.")

    if not (0 <= minimo <= maximo <= 100):
        raise ValueError("Los limites de humedad son invalidos.")

    if valor < minimo:
        return {
            "codigo": "baja",
            "estado": "Humedad baja",
            "mensaje": (
                "La humedad ambiental esta por debajo "
                "del rango configurado."
            )
        }

    if valor > maximo:
        return {
            "codigo": "alta",
            "estado": "Humedad alta",
            "mensaje": (
                "La humedad ambiental supera "
                "el rango configurado."
            )
        }

    return {
        "codigo": "adecuada",
        "estado": "Humedad adecuada",
        "mensaje": (
            "La humedad ambiental esta dentro "
            "del rango configurado."
        )
    }


def obtener_estado_actual():
    """
    Consulta la ultima lectura registrada en MySQL.
    """

    minimo = float(os.getenv("HUMEDAD_MIN", "75"))
    maximo = float(os.getenv("HUMEDAD_MAX", "85"))

    if not (0 <= minimo <= maximo <= 100):
        raise ValueError("Configuracion de humedad invalida.")

    dao = LecturasDAO()
    lecturas = dao.obtener_ultimas_lecturas(1)

    if not lecturas:
        return {
            "hay_datos": False,
            "mensaje": "Todavia no existen mediciones registradas.",
            "limite_minimo": minimo,
            "limite_maximo": maximo
        }

    lectura = lecturas[0]

    humedad = float(lectura["humedad"])
    evaluacion = evaluar_humedad(humedad, minimo, maximo)

    sensor_id = str(lectura["sensor_id"])

    # Identificamos las lecturas de nuestros simuladores.
    # Un identificador desconocido no se considera
    # automaticamente un sensor fisico verificado.
    es_simulada = "_SIM_" in sensor_id

    fecha = lectura.get("fecha_hora")

    if isinstance(fecha, datetime):
        fecha_texto = fecha.strftime("%d-%m-%Y %H:%M:%S")
    else:
        fecha_texto = str(fecha) if fecha else "No disponible"

    return {
        "hay_datos": True,
        "humedad": humedad,
        "codigo": evaluacion["codigo"],
        "estado": evaluacion["estado"],
        "mensaje": evaluacion["mensaje"],
        "sensor_id": sensor_id,
        "simulada": es_simulada,
        "origen": (
            "Simulado" if es_simulada
            else "Origen no verificado"
        ),
        "fecha_hora": fecha_texto,
        "limite_minimo": minimo,
        "limite_maximo": maximo
    }


@monitoreo_bp.route("/api/humedad/estado", methods=["GET"])
def api_estado_humedad():

    try:
        resultado = obtener_estado_actual()
        return jsonify(resultado), 200

    except (
        mysql.connector.Error,
        ValueError,
        TypeError,
        KeyError
    ):
        current_app.logger.exception(
            "Error al consultar el estado de humedad"
        )

        return jsonify({
            "error": "No se pudo consultar el monitoreo de humedad."
        }), 503


@monitoreo_bp.route("/humedad", methods=["GET"])
def pagina_humedad():

    try:
        resultado = obtener_estado_actual()
        error = None

    except (
        mysql.connector.Error,
        ValueError,
        TypeError,
        KeyError
    ):
        current_app.logger.exception(
            "Error al mostrar el monitoreo de humedad"
        )

        resultado = None
        error = "No se pudo obtener la medicion desde MySQL."

    return render_template(
        "humedad.html",
        resultado=resultado,
        error=error
    )
