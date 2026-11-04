
import os
import unittest

from datetime import datetime
from unittest.mock import patch

import mysql.connector

from app import app


# =====================================
# V5 + V6 - PRUEBAS DE MONITOREO UNIFICADO
# =====================================

class TestTiempoReal(unittest.TestCase):

    def setUp(self):
        """
        Configura Flask y los limites de humedad
        para ejecutar las pruebas.
        """

        app.config["TESTING"] = True

        self.config = patch.dict(
            os.environ,
            {
                "HUMEDAD_MIN": "75",
                "HUMEDAD_MAX": "85"
            }
        )

        self.config.start()
        self.addCleanup(self.config.stop)

        self.cliente = app.test_client()


    # =====================================
    # PRUEBA 1: MEDICION CORRECTA
    # =====================================

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

        # V6 - Mediciones ambientales
        self.assertTrue(datos["hay_datos"])
        self.assertEqual(datos["humedad"], 83.6)
        self.assertEqual(datos["temperatura"], 21.7)

        # V5 - Evaluacion de humedad
        self.assertEqual(datos["codigo"], "adecuada")
        self.assertEqual(datos["estado"], "Humedad adecuada")
        self.assertIn("mensaje", datos)

        # V5 - Limites configurados
        self.assertEqual(datos["limite_minimo"], 75.0)
        self.assertEqual(datos["limite_maximo"], 85.0)

        # Informacion del dispositivo
        self.assertEqual(
            datos["sensor_id"],
            "ESP8266_SIM_01"
        )

        self.assertTrue(datos["simulada"])
        self.assertEqual(datos["origen"], "Simulado")

        self.assertEqual(
            datos["fecha_hora"],
            "2026-11-04 12:30:00"
        )


    # =====================================
    # PRUEBA 2: SIN MEDICIONES
    # =====================================

    @patch("tiempo_real.LecturasDAO")
    def test_api_sin_mediciones(self, mock_dao):

        mock_dao.return_value.obtener_ultimas_lecturas.return_value = []

        respuesta = self.cliente.get("/api/tiempo-real")

        self.assertEqual(respuesta.status_code, 200)

        datos = respuesta.get_json()

        self.assertFalse(datos["hay_datos"])
        self.assertIn("mensaje", datos)

        # Los limites siguen disponibles
        # aunque no existan mediciones.
        self.assertEqual(datos["limite_minimo"], 75.0)
        self.assertEqual(datos["limite_maximo"], 85.0)


    # =====================================
    # PRUEBA 3: ERROR DE MYSQL
    # =====================================

    @patch("tiempo_real.LecturasDAO")
    def test_api_error_base_datos(self, mock_dao):

        mock_dao.return_value.obtener_ultimas_lecturas.side_effect = (
            mysql.connector.Error("Conexion fallida")
        )

        respuesta = self.cliente.get("/api/tiempo-real")

        self.assertEqual(respuesta.status_code, 503)

        datos = respuesta.get_json()

        self.assertIn("error", datos)


    # =====================================
    # PRUEBA 4: PAGINA WEB UNIFICADA
    # =====================================

    def test_pagina_tiempo_real(self):
        """
        Comprueba que la pagina de monitoreo
        contiene las funcionalidades de V5 y V6.
        """

        respuesta = self.cliente.get("/tiempo-real")

        self.assertEqual(respuesta.status_code, 200)

        contenido = respuesta.get_data(as_text=True)

        # Titulo de la pagina unificada
        self.assertIn(
            "Monitoreo ambiental",
            contenido
        )

        # V6 - Humedad y temperatura
        self.assertIn(
            "valor-humedad",
            contenido
        )

        self.assertIn(
            "valor-temperatura",
            contenido
        )

        # V5 - Evaluacion de humedad
        self.assertIn(
            "estado-humedad",
            contenido
        )

        self.assertIn(
            "mensaje-humedad",
            contenido
        )

        # V5 - Limites de humedad
        self.assertIn(
            "humedad-minima",
            contenido
        )

        self.assertIn(
            "humedad-maxima",
            contenido
        )

        # V6 - Actualizacion automatica
        self.assertIn(
            "tiempo_real.js",
            contenido
        )

        # V7 - Acceso a configuracion
        self.assertIn(
            "/historial/configuracion",
            contenido
        )


if __name__ == "__main__":
    unittest.main()
