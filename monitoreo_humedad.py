
import math
import os
from datetime import datetime

import mysql.connector

from flask import (
    Blueprint,
    current_app,
    jsonify,
    redirect,
    url_for
)

from lecturas_dao import LecturasDAO


# =====================================
# V5 - MONITOREO DE HUMEDAD
# =====================================

monitoreo_bp = Blueprint("monitoreo", __name__)


# =====================================
# V5 - EVALUAR HUMEDAD
# =====================================

def evaluar_humedad(humedad, minimo=75.0, maximo=85.0):
    """
    Evalua la humedad ambiental segun
    los limites configurados.

    Esta funcion tambien es utilizada por V6.
    """

    valor = float(humedad)

    if not math.isfinite(valor) or not 0 <= valor <= 100:
        raise ValueError(
            "La humedad debe estar entre 0 y 100."
        )

    if not (0 <= minimo <= maximo <= 100):
        raise ValueError(
            "Los limites de humedad son invalidos."
        )

    # Humedad por debajo del minimo.
    if valor < minimo:
        return {
            "codigo": "baja",
            "estado": "Humedad baja",
            "mensaje": (
                "La humedad ambiental esta por debajo "
                "del rango configurado."
            )
        }

    # Humedad por encima del maximo.
    if valor > maximo:
        return {
            "codigo": "alta",
            "estado": "Humedad alta",
            "mensaje": (
                "La humedad ambiental supera "
                "el rango configurado."
            )
        }

    # Humedad dentro del rango.
    return {
        "codigo": "adecuada",
        "estado": "Humedad adecuada",
        "mensaje": (
            "La humedad ambiental esta dentro "
            "del rango configurado."
        )
    }


# =====================================
# V5 - OBTENER ESTADO ACTUAL
# =====================================

def obtener_estado_actual():
    """
    Consulta la ultima lectura almacenada
    en MySQL y evalua su humedad.

    Se mantiene para conservar la API de V5
    y la compatibilidad con sus pruebas.
    """

    # Limites configurados en .env
    minimo = float(os.getenv("HUMEDAD_MIN", "75"))
    maximo = float(os.getenv("HUMEDAD_MAX", "85"))

    if not (0 <= minimo <= maximo <= 100):
        raise ValueError(
            "Configuracion de humedad invalida."
        )

    # Consultar ultima medicion.
    dao = LecturasDAO()
    lecturas = dao.obtener_ultimas_lecturas(1)

    # No existen mediciones.
    if not lecturas:
        return {
            "hay_datos": False,
            "mensaje": (
                "Todavia no existen mediciones registradas."
            ),
            "limite_minimo": minimo,
            "limite_maximo": maximo
        }

    lectura = lecturas[0]

    humedad = float(lectura["humedad"])
    sensor_id = str(lectura["sensor_id"])

    # Evaluar la humedad.
    evaluacion = evaluar_humedad(
        humedad,
        minimo,
        maximo
    )

    # Identificar datos simulados.
    # Un dispositivo desconocido no se considera
    # automaticamente un sensor fisico verificado.
    es_simulada = "_SIM_" in sensor_id

    # Formatear fecha de registro.
    fecha = lectura.get("fecha_hora")

    if isinstance(fecha, datetime):

        fecha_texto = fecha.strftime(
            "%d-%m-%Y %H:%M:%S"
        )

    else:

        fecha_texto = (
            str(fecha)
            if fecha
            else "No disponible"
        )

    # Resultado de la evaluacion.
    return {
        "hay_datos": True,

        "humedad": humedad,

        "codigo": evaluacion["codigo"],
        "estado": evaluacion["estado"],
        "mensaje": evaluacion["mensaje"],

        "sensor_id": sensor_id,

        "simulada": es_simulada,

        "origen": (
            "Simulado"
            if es_simulada
            else "Origen no verificado"
        ),

        "fecha_hora": fecha_texto,

        "limite_minimo": minimo,
        "limite_maximo": maximo
    }


# =====================================
# V5 - API DE ESTADO DE HUMEDAD
# =====================================

@monitoreo_bp.route(
    "/api/humedad/estado",
    methods=["GET"]
)
def api_estado_humedad():
    """
    Mantiene disponible la API original
    de monitoreo de humedad de V5.
    """

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
            "error": (
                "No se pudo consultar "
                "el monitoreo de humedad."
            )
        }), 503


# =====================================
# V5 + V6 - REDIRECCION AL PANEL UNIFICADO
# =====================================

@monitoreo_bp.route(
    "/humedad",
    methods=["GET"]
)
def pagina_humedad():
    """
    Redirige la antigua pagina de V5
    al monitoreo ambiental unificado.

    Se mantiene la direccion /humedad
    para conservar compatibilidad
    con enlaces anteriores.
    """

    return redirect(
        url_for("tiempo_real.pagina_tiempo_real")
    )
