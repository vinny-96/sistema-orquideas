
import os
from datetime import datetime

import mysql.connector

from flask import (
    Blueprint,
    jsonify,
    current_app,
    render_template
)

from lecturas_dao import LecturasDAO
from monitoreo_humedad import evaluar_humedad


# =====================================
# V8 - MONITOREO AMBIENTAL UNIFICADO
# DHT22 + HC-SR04 + ESP8266
# =====================================

tiempo_real_bp = Blueprint("tiempo_real", __name__)


# =====================================
# CONSULTAR LIMITES DE HUMEDAD
# =====================================

def obtener_limites_humedad():
    """
    Obtiene los limites de humedad ambiental
    configurados en las variables de entorno.
    """

    minimo = float(os.getenv("HUMEDAD_MIN", "75"))
    maximo = float(os.getenv("HUMEDAD_MAX", "85"))

    if not (0 <= minimo <= maximo <= 100):
        raise ValueError(
            "La configuracion de humedad es invalida."
        )

    return minimo, maximo


# =====================================
# API DE MONITOREO AMBIENTAL
# =====================================

@tiempo_real_bp.route(
    "/api/tiempo-real",
    methods=["GET"]
)
def consultar_tiempo_real():
    """
    Devuelve la ultima medicion almacenada en MySQL.

    Incluye:
    - Humedad ambiental
    - Temperatura ambiental
    - Estado de humedad
    - Distancia al agua del estanque
    - Estado del nivel de agua
    - Identificador del dispositivo
    - Fecha de registro
    - Origen de los datos
    """

    try:

        # =====================================
        # LIMITES DE HUMEDAD
        # =====================================

        minimo, maximo = obtener_limites_humedad()

        # =====================================
        # ULTIMA MEDICION DE MYSQL
        # =====================================

        dao = LecturasDAO()
        lecturas = dao.obtener_ultimas_lecturas(1)

        if not lecturas:

            return jsonify({
                "hay_datos": False,
                "mensaje": (
                    "Todavia no hay mediciones registradas."
                ),
                "limite_minimo": minimo,
                "limite_maximo": maximo,
                "distancia_agua_cm": None,
                "agua_baja": None
            }), 200

        lectura = lecturas[0]

        # =====================================
        # DATOS DEL DHT22
        # =====================================

        humedad = float(lectura["humedad"])
        temperatura = float(lectura["temperatura"])

        sensor_id = str(lectura["sensor_id"])

        # =====================================
        # EVALUACION DE HUMEDAD
        # =====================================

        evaluacion = evaluar_humedad(
            humedad,
            minimo,
            maximo
        )

        # =====================================
        # DATOS DEL SENSOR ULTRASONICO
        # =====================================

        distancia_guardada = lectura.get(
            "distancia_agua_cm"
        )

        estado_agua_guardado = lectura.get(
            "agua_baja"
        )

        if (
            distancia_guardada is not None
            and estado_agua_guardado is not None
        ):

            distancia_agua_cm = float(
                distancia_guardada
            )

            agua_baja = bool(
                estado_agua_guardado
            )

            estado_agua = (
                "Agua baja"
                if agua_baja
                else "Agua suficiente"
            )

        else:

            distancia_agua_cm = None
            agua_baja = None
            estado_agua = "Sin medicion disponible"

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
        # IDENTIFICAR ORIGEN DE LA MEDICION
        # =====================================

        simulada = "_SIM_" in sensor_id

        if simulada:

            origen = "Simulado"

        elif sensor_id == "ESP8266_REAL_01":

            origen = "ESP8266 - Sensores reales"

        else:

            origen = "Origen no verificado"

        # =====================================
        # RESPUESTA JSON UNIFICADA
        # =====================================

        return jsonify({

            "hay_datos": True,

            # DHT22
            "humedad": humedad,
            "temperatura": temperatura,

            # Evaluacion de humedad
            "codigo": evaluacion["codigo"],
            "estado": evaluacion["estado"],
            "mensaje": evaluacion["mensaje"],

            # Limites de humedad
            "limite_minimo": minimo,
            "limite_maximo": maximo,

            # Sensor ultrasonico
            "distancia_agua_cm": distancia_agua_cm,
            "agua_baja": agua_baja,
            "estado_agua": estado_agua,

            # Dispositivo
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
# PAGINA DE MONITOREO AMBIENTAL
# =====================================

@tiempo_real_bp.route(
    "/tiempo-real",
    methods=["GET"]
)
def pagina_tiempo_real():
    """
    Muestra el monitoreo ambiental unificado.

    JavaScript actualiza automaticamente:
    - Humedad ambiental
    - Temperatura ambiental
    - Estado de humedad
    - Distancia al agua
    - Estado del estanque
    - Informacion del dispositivo
    """

    return render_template("tiempo_real.html")
