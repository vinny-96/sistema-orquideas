
import os
from datetime import datetime

import mysql.connector

from flask import Blueprint, jsonify, current_app, render_template

from lecturas_dao import LecturasDAO
from monitoreo_humedad import evaluar_humedad


# =====================================
# V5 Y V6 - MONITOREO AMBIENTAL UNIFICADO
# =====================================

tiempo_real_bp = Blueprint("tiempo_real", __name__)


# =====================================
# CONSULTAR LIMITES DE HUMEDAD
# =====================================

def obtener_limites_humedad():
    """
    Obtiene los limites de humedad configurados
    en las variables de entorno.
    """

    minimo = float(os.getenv("HUMEDAD_MIN", "75"))
    maximo = float(os.getenv("HUMEDAD_MAX", "85"))

    if not (0 <= minimo <= maximo <= 100):
        raise ValueError(
            "La configuracion de humedad es invalida."
        )

    return minimo, maximo


# =====================================
# V5 Y V6 - API DE MONITOREO UNIFICADA
# =====================================

@tiempo_real_bp.route("/api/tiempo-real", methods=["GET"])
def consultar_tiempo_real():
    """
    Devuelve la ultima medicion ambiental
    almacenada en MySQL.

    Incluye:
    - Humedad
    - Temperatura
    - Evaluacion de humedad
    - Limites configurados
    - Dispositivo
    - Fecha de registro
    - Origen de los datos
    """

    try:

        # Obtener los limites configurados.
        minimo, maximo = obtener_limites_humedad()

        # Obtener la ultima medicion desde MySQL.
        dao = LecturasDAO()
        lecturas = dao.obtener_ultimas_lecturas(1)

        # Si aun no hay mediciones registradas.
        if not lecturas:

            return jsonify({
                "hay_datos": False,
                "mensaje": (
                    "Todavia no hay mediciones registradas."
                ),
                "limite_minimo": minimo,
                "limite_maximo": maximo
            }), 200

        lectura = lecturas[0]

        humedad = float(lectura["humedad"])
        temperatura = float(lectura["temperatura"])

        sensor_id = str(lectura["sensor_id"])

        # =====================================
        # V5 - EVALUAR HUMEDAD
        # =====================================

        evaluacion = evaluar_humedad(
            humedad,
            minimo,
            maximo
        )

        # =====================================
        # FECHA DE LA MEDICION
        # =====================================

        fecha = lectura.get("fecha_hora")

        if isinstance(fecha, datetime):

            fecha_hora = fecha.strftime(
                "%Y-%m-%d %H:%M:%S"
            )

        else:

            fecha_hora = (
                str(fecha)
                if fecha is not None
                else ""
            )

        # =====================================
        # IDENTIFICAR MEDICION SIMULADA
        # =====================================

        simulada = "_SIM_" in sensor_id

        origen = (
            "Simulado"
            if simulada
            else "Origen no verificado"
        )

        # =====================================
        # RESPUESTA UNIFICADA
        # =====================================

        return jsonify({

            "hay_datos": True,

            # V6: valores ambientales
            "humedad": humedad,
            "temperatura": temperatura,

            # V5: evaluacion de humedad
            "codigo": evaluacion["codigo"],
            "estado": evaluacion["estado"],
            "mensaje": evaluacion["mensaje"],

            # V5: limites de humedad
            "limite_minimo": minimo,
            "limite_maximo": maximo,

            # Informacion de la medicion
            "sensor_id": sensor_id,
            "fecha_hora": fecha_hora,
            "simulada": simulada,
            "origen": origen

        }), 200

    except (
        mysql.connector.Error,
        ValueError,
        TypeError,
        KeyError
    ):

        current_app.logger.exception(
            "Error al consultar el monitoreo ambiental"
        )

        return jsonify({
            "error": (
                "No se pudieron consultar "
                "las mediciones ambientales."
            )
        }), 503


# =====================================
# V5 Y V6 - PAGINA UNIFICADA
# =====================================

@tiempo_real_bp.route("/tiempo-real", methods=["GET"])
def pagina_tiempo_real():
    """
    Muestra la pagina unificada de monitoreo.

    JavaScript actualiza automaticamente:
    - Humedad
    - Temperatura
    - Estado de humedad
    - Informacion del dispositivo
    """

    return render_template("tiempo_real.html")
