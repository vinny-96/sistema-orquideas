
from datetime import datetime

import mysql.connector

from flask import Blueprint, jsonify, current_app, render_template
from lecturas_dao import LecturasDAO


# ==============================
# V6 - BLUEPRINT TIEMPO REAL
# ==============================

tiempo_real_bp = Blueprint("tiempo_real", __name__)


# ==============================
# V6 - API DE MEDICIONES
# ==============================

@tiempo_real_bp.route("/api/tiempo-real", methods=["GET"])
def consultar_tiempo_real():
    """
    Devuelve la última medición ambiental
    almacenada en MySQL.
    """

    try:
        dao = LecturasDAO()
        lecturas = dao.obtener_ultimas_lecturas(1)

        if not lecturas:
            return jsonify({
                "hay_datos": False,
                "mensaje": "Todavía no hay mediciones registradas."
            }), 200

        lectura = lecturas[0]

        humedad = float(lectura["humedad"])
        temperatura = float(lectura["temperatura"])
        sensor_id = str(lectura["sensor_id"])

        fecha = lectura.get("fecha_hora")

        if isinstance(fecha, datetime):
            fecha_hora = fecha.strftime("%Y-%m-%d %H:%M:%S")
        else:
            fecha_hora = str(fecha) if fecha is not None else ""

        simulada = "_SIM_" in sensor_id

        return jsonify({
            "hay_datos": True,
            "humedad": humedad,
            "temperatura": temperatura,
            "sensor_id": sensor_id,
            "fecha_hora": fecha_hora,
            "simulada": simulada,
            "origen": (
                "Simulado"
                if simulada
                else "Origen no verificado"
            )
        }), 200

    except (mysql.connector.Error, ValueError, TypeError, KeyError):
        current_app.logger.exception(
            "Error al consultar mediciones en tiempo real"
        )

        return jsonify({
            "error": "No se pudieron consultar las mediciones."
        }), 503


# ==============================
# V6 - PANEL DE MONITOREO
# ==============================

@tiempo_real_bp.route("/tiempo-real", methods=["GET"])
def pagina_tiempo_real():
    """
    Muestra la página de monitoreo
    de humedad y temperatura.

    Los datos se actualizarán automáticamente
    mediante JavaScript.
    """

    return render_template("tiempo_real.html")
