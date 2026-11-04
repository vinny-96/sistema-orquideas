
import json
from datetime import datetime

import mysql.connector

from flask import (
    Blueprint,
    jsonify,
    request,
    current_app,
    render_template
)

from configuracion_historial import (
    obtener_configuracion,
    guardar_configuracion,
    INTERVALOS_PERMITIDOS
)

from lecturas_dao import LecturasDAO


# =====================================
# V7 - CONFIGURACION DEL HISTORIAL
# =====================================

historial_bp = Blueprint("historial", __name__)


# =====================================
# V7 - CONSULTAR CONFIGURACION
# =====================================

@historial_bp.route(
    "/api/historial/configuracion",
    methods=["GET"]
)
def consultar_configuracion():
    """
    Devuelve la frecuencia configurada
    para registrar nuevas mediciones.
    """

    try:
        configuracion = obtener_configuracion()

        return jsonify({
            "intervalo_segundos": configuracion["intervalo_segundos"],
            "intervalos_permitidos": INTERVALOS_PERMITIDOS
        }), 200

    except (
        OSError,
        json.JSONDecodeError,
        KeyError,
        ValueError,
        TypeError
    ):
        current_app.logger.exception(
            "Error al consultar la configuracion del historial"
        )

        return jsonify({
            "error": "No se pudo consultar la configuracion."
        }), 503


# =====================================
# V7 - GUARDAR CONFIGURACION
# =====================================

@historial_bp.route(
    "/api/historial/configuracion",
    methods=["POST"]
)
def actualizar_configuracion():
    """
    Recibe una nueva frecuencia y
    la guarda en el archivo JSON.
    """

    datos = request.get_json(silent=True)

    if not isinstance(datos, dict):
        return jsonify({
            "error": "Debes enviar un objeto JSON valido."
        }), 400

    if "intervalo_segundos" not in datos:
        return jsonify({
            "error": "Falta intervalo_segundos."
        }), 400

    try:
        configuracion = guardar_configuracion(
            datos["intervalo_segundos"]
        )

        return jsonify({
            "mensaje": "Frecuencia actualizada correctamente.",
            "intervalo_segundos": configuracion["intervalo_segundos"]
        }), 200

    except ValueError as error:
        return jsonify({
            "error": str(error)
        }), 400

    except OSError:
        current_app.logger.exception(
            "Error al guardar la configuracion del historial"
        )

        return jsonify({
            "error": "No se pudo guardar la configuracion."
        }), 503


# =====================================
# V7 - PAGINA DE CONFIGURACION
# =====================================

@historial_bp.route(
    "/historial/configuracion",
    methods=["GET", "POST"]
)
def pagina_configuracion():
    """
    Permite consultar y modificar la frecuencia
    de las mediciones desde el navegador.
    """

    mensaje = None
    error = None

    if request.method == "POST":

        try:
            intervalo = request.form.get(
                "intervalo_segundos"
            )

            guardar_configuracion(intervalo)

            mensaje = (
                "Frecuencia actualizada correctamente."
            )

        except ValueError as excepcion:
            error = str(excepcion)

        except OSError:
            current_app.logger.exception(
                "Error al guardar la frecuencia"
            )

            error = "No se pudo guardar la configuracion."

    try:
        configuracion = obtener_configuracion()

    except (
        OSError,
        json.JSONDecodeError,
        KeyError,
        ValueError,
        TypeError
    ):
        current_app.logger.exception(
            "Error al leer la configuracion"
        )

        return (
            "No se pudo consultar la configuracion.",
            503
        )

    return render_template(
        "configuracion_historial.html",
        configuracion=configuracion,
        intervalos=INTERVALOS_PERMITIDOS,
        mensaje=mensaje,
        error=error
    )


# =====================================
# V7 - API DEL HISTORIAL DE MEDICIONES
# =====================================

@historial_bp.route(
    "/api/historial/lecturas",
    methods=["GET"]
)
def consultar_historial_lecturas():
    """
    Consulta las ultimas mediciones
    almacenadas en MySQL.

    Permite recuperar entre 1 y 100 registros.

    Ejemplo:
    /api/historial/lecturas?limite=20
    """

    # =====================================
    # VALIDAR CANTIDAD DE REGISTROS
    # =====================================

    limite_texto = request.args.get(
        "limite",
        "20"
    )

    try:
        limite = int(limite_texto)

        if not 1 <= limite <= 100:
            raise ValueError(
                "El limite debe estar entre 1 y 100."
            )

    except (ValueError, TypeError):

        return jsonify({
            "error": (
                "El limite debe ser un numero "
                "entero entre 1 y 100."
            )
        }), 400

    # =====================================
    # CONSULTAR MYSQL
    # =====================================

    try:
        dao = LecturasDAO()

        lecturas = dao.obtener_ultimas_lecturas(
            limite
        )

        historial = []

        # =====================================
        # PROCESAR MEDICIONES
        # =====================================

        for lectura in lecturas:

            id_lectura = lectura["id_lectura"]

            sensor_id = str(
                lectura["sensor_id"]
            )

            humedad = float(
                lectura["humedad"]
            )

            temperatura = float(
                lectura["temperatura"]
            )

            fecha = lectura.get(
                "fecha_hora"
            )

            # Formatear fecha de MySQL.
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

            # Identificar datos simulados.
            simulada = "_SIM_" in sensor_id

            origen = (
                "Simulado"
                if simulada
                else "Origen no verificado"
            )

            # Agregar medicion al historial.
            historial.append({
                "id_lectura": id_lectura,
                "sensor_id": sensor_id,
                "humedad": humedad,
                "temperatura": temperatura,
                "fecha_hora": fecha_hora,
                "simulada": simulada,
                "origen": origen
            })

        # =====================================
        # RESPUESTA JSON DEL HISTORIAL
        # =====================================

        return jsonify({
            "hay_datos": len(historial) > 0,
            "total": len(historial),
            "limite": limite,
            "lecturas": historial
        }), 200

    # =====================================
    # MANEJO DE ERRORES
    # =====================================

    except (
        mysql.connector.Error,
        ValueError,
        TypeError,
        KeyError
    ):

        current_app.logger.exception(
            "Error al consultar el historial de mediciones"
        )

        return jsonify({
            "error": (
                "No se pudo consultar "
                "el historial de mediciones."
            )
        }), 503


# =====================================
# V7 - PAGINA DEL HISTORIAL
# =====================================

@historial_bp.route(
    "/historial",
    methods=["GET"]
)
def pagina_historial():
    """
    Muestra el historial de mediciones
    ambientales almacenadas en MySQL.

    Los datos se consultan mediante
    JavaScript y la API de V7.
    """

    return render_template("historial.html")
