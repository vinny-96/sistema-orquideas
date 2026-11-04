
import os
import unittest

from datetime import datetime
from decimal import Decimal
from unittest.mock import patch

import mysql.connector

from app import app
from monitoreo_humedad import evaluar_humedad


class TestMonitoreoHumedad(unittest.TestCase):

    def setUp(self):

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

    def lectura_ejemplo(self):

        return {
            "id_lectura": 3,
            "sensor_id": "ESP8266_SIM_01",
            "humedad": Decimal("82.00"),
            "temperatura": Decimal("21.30"),
            "fecha_hora": datetime(2026, 10, 31, 18, 30)
        }

    # =====================================
    # V5 - EVALUACION DE HUMEDAD
    # =====================================

    def test_humedad_baja(self):

        resultado = evaluar_humedad(65)

        self.assertEqual(
            resultado["codigo"],
            "baja"
        )

    def test_humedad_adecuada(self):

        for humedad in (75, 80, 85):

            with self.subTest(humedad=humedad):

                resultado = evaluar_humedad(humedad)

                self.assertEqual(
                    resultado["codigo"],
                    "adecuada"
                )

    def test_humedad_alta(self):

        resultado = evaluar_humedad(92)

        self.assertEqual(
            resultado["codigo"],
            "alta"
        )

    def test_rechazar_humedad_invalida(self):

        with self.assertRaises(ValueError):
            evaluar_humedad(110)

    # =====================================
    # V5 - API DE MONITOREO
    # =====================================

    @patch("monitoreo_humedad.LecturasDAO")
    def test_api_humedad(self, mock_dao):

        mock_dao.return_value.obtener_ultimas_lecturas.return_value = [
            self.lectura_ejemplo()
        ]

        respuesta = self.cliente.get(
            "/api/humedad/estado"
        )

        self.assertEqual(
            respuesta.status_code,
            200
        )

        datos = respuesta.get_json()

        self.assertTrue(datos["hay_datos"])
        self.assertEqual(datos["humedad"], 82.0)
        self.assertEqual(datos["codigo"], "adecuada")
        self.assertTrue(datos["simulada"])

    @patch("monitoreo_humedad.LecturasDAO")
    def test_sin_mediciones(self, mock_dao):

        mock_dao.return_value.obtener_ultimas_lecturas.return_value = []

        respuesta = self.cliente.get(
            "/api/humedad/estado"
        )

        self.assertEqual(
            respuesta.status_code,
            200
        )

        self.assertFalse(
            respuesta.get_json()["hay_datos"]
        )

    # =====================================
    # V5 + V6 - REDIRECCION AL PANEL UNIFICADO
    # =====================================

    def test_pagina_humedad(self):
        """
        Comprueba que la antigua pagina
        /humedad redirige al monitoreo
        ambiental unificado /tiempo-real.
        """

        respuesta = self.cliente.get(
            "/humedad",
            follow_redirects=False
        )

        # La antigua ruta debe redirigir.
        self.assertEqual(
            respuesta.status_code,
            302
        )

        # Debe llevar al nuevo panel.
        self.assertEqual(
            respuesta.headers["Location"],
            "/tiempo-real"
        )

        # Comprobar que la pagina de destino funciona.
        destino = self.cliente.get(
            "/humedad",
            follow_redirects=True
        )

        self.assertEqual(
            destino.status_code,
            200
        )

        contenido = destino.get_data(
            as_text=True
        )

        self.assertIn(
            "Monitoreo ambiental",
            contenido
        )

        self.assertIn(
            "Humedad ambiental",
            contenido
        )

        self.assertIn(
            "Temperatura ambiental",
            contenido
        )

    # =====================================
    # V5 - ERROR DE BASE DE DATOS
    # =====================================

    @patch("monitoreo_humedad.LecturasDAO")
    def test_error_base_datos(self, mock_dao):

        mock_dao.return_value.obtener_ultimas_lecturas.side_effect = (
            mysql.connector.Error("Conexion fallida")
        )

        respuesta = self.cliente.get(
            "/api/humedad/estado"
        )

        self.assertEqual(
            respuesta.status_code,
            503
        )


if __name__ == "__main__":
    unittest.main()
