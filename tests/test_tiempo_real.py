
import unittest
from datetime import datetime
from unittest.mock import patch

import mysql.connector

from app import app


# ==============================
# V6 - PRUEBAS DE TIEMPO REAL
# ==============================

class TestTiempoReal(unittest.TestCase):

    def setUp(self):
        """
        Configura Flask para ejecutar las pruebas.
        """
        app.config["TESTING"] = True
        self.cliente = app.test_client()

    # ==============================
    # PRUEBA 1: MEDICION CORRECTA
    # ==============================

    @patch("tiempo_real.LecturasDAO")
    def test_api_medicion_correcta(self, mock_dao):

        mock_dao.return_value.obtener_ultimas_lecturas.return_value = [
            {
                "sensor_id": "ESP8266_SIM_01",
                "humedad": 83.6,
                "temperatura": 21.7,
                "fecha_hora": datetime(2026, 11, 4, 12, 30, 0)
            }
        ]

        respuesta = self.cliente.get("/api/tiempo-real")

        self.assertEqual(respuesta.status_code, 200)

        datos = respuesta.get_json()

        self.assertTrue(datos["hay_datos"])
        self.assertEqual(datos["humedad"], 83.6)
        self.assertEqual(datos["temperatura"], 21.7)
        self.assertEqual(datos["sensor_id"], "ESP8266_SIM_01")
        self.assertTrue(datos["simulada"])
        self.assertEqual(datos["origen"], "Simulado")
        self.assertEqual(
            datos["fecha_hora"],
            "2026-11-04 12:30:00"
        )

    # ==============================
    # PRUEBA 2: SIN MEDICIONES
    # ==============================

    @patch("tiempo_real.LecturasDAO")
    def test_api_sin_mediciones(self, mock_dao):

        mock_dao.return_value.obtener_ultimas_lecturas.return_value = []

        respuesta = self.cliente.get("/api/tiempo-real")

        self.assertEqual(respuesta.status_code, 200)

        datos = respuesta.get_json()

        self.assertFalse(datos["hay_datos"])
        self.assertIn("mensaje", datos)

    # ==============================
    # PRUEBA 3: ERROR DE MYSQL
    # ==============================

    @patch("tiempo_real.LecturasDAO")
    def test_api_error_base_datos(self, mock_dao):

        mock_dao.return_value.obtener_ultimas_lecturas.side_effect = (
            mysql.connector.Error("Conexión fallida")
        )

        respuesta = self.cliente.get("/api/tiempo-real")

        self.assertEqual(respuesta.status_code, 503)

        datos = respuesta.get_json()

        self.assertIn("error", datos)

    # ==============================
    # PRUEBA 4: PAGINA WEB
    # ==============================

    def test_pagina_tiempo_real(self):

        respuesta = self.cliente.get("/tiempo-real")

        self.assertEqual(respuesta.status_code, 200)

        contenido = respuesta.get_data(as_text=True)

        self.assertIn("Monitoreo en tiempo real", contenido)
        self.assertIn("valor-humedad", contenido)
        self.assertIn("valor-temperatura", contenido)
        self.assertIn("tiempo_real.js", contenido)


if __name__ == "__main__":
    unittest.main()
