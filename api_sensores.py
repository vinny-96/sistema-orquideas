
import hmac
import math
import os
from pathlib import Path

import mysql.connector
from dotenv import load_dotenv
from flask import Blueprint, jsonify, request, current_app

from lecturas_dao import LecturasDAO


load_dotenv(Path(__file__).resolve().parent / ".env")

sensores_bp = Blueprint("sensores", __name__)


@sensores_bp.route("/api/mediciones", methods=["POST"])
def recibir_medicion():

    clave_servidor = os.getenv("SENSOR_API_KEY", "")
    clave_recibida = request.headers.get("X-API-Key", "")

    if not clave_servidor:
        return jsonify({
            "error": "La clave de sensores no está configurada"
        }), 503

    if not hmac.compare_digest(clave_servidor, clave_recibida):
        return jsonify({
            "error": "Acceso no autorizado"
        }), 401

    if not request.is_json:
        return jsonify({
            "error": "El contenido debe ser JSON"
        }), 400

    datos = request.get_json(silent=True)

    if not isinstance(datos, dict):
        return jsonify({
            "error": "JSON inválido"
        }), 400

    sensor_id = datos.get("sensor_id")
    humedad = datos.get("humedad")
    temperatura = datos.get("temperatura")

    if (
        not isinstance(sensor_id, str)
        or not sensor_id.strip()
        or len(sensor_id.strip()) > 50
    ):
        return jsonify({
            "error": "Identificador de sensor inválido"
        }), 400

    for valor in (humedad, temperatura):
        if (
            isinstance(valor, bool)
            or not isinstance(valor, (int, float))
            or not math.isfinite(valor)
        ):
            return jsonify({
                "error": "Las mediciones deben ser números válidos"
            }), 400

    if not 0 <= humedad <= 100:
        return jsonify({
            "error": "La humedad debe estar entre 0 y 100"
        }), 400

    if not -40 <= temperatura <= 85:
        return jsonify({
            "error": "Temperatura fuera del rango admitido"
        }), 400

    try:
        dao = LecturasDAO()

        id_lectura = dao.registrar_lectura(
            sensor_id=sensor_id.strip(),
            humedad=humedad,
            temperatura=temperatura
        )

        return jsonify({
            "mensaje": "Medición registrada correctamente",
            "id_lectura": id_lectura,
            "sensor_id": sensor_id.strip(),
            "humedad": humedad,
            "temperatura": temperatura
        }), 201

    except mysql.connector.Error:
        current_app.logger.exception("Error al guardar medición")
        return jsonify({
            "error": "No se pudo guardar la medición"
        }), 503
