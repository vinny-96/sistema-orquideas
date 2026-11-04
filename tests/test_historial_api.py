
import unittest

from datetime import datetime
from decimal import Decimal
from unittest.mock import patch

import mysql.connector

from app import app


# =====================================
# V7 - PRUEBAS DEL HISTORIAL
# =====================================

class TestHistorialAPI(unittest.TestCase):

    def setUp(self):
        """
        Prepara el cliente de pruebas de Flask.
        """

        self.cliente = app.test_client()

    def lectura_ejemplo(self):
        """
        Genera una medicion simulada para
        las pruebas sin utilizar MySQL real.
        """

        return {
            "id_lectura": 174,
            "sensor_id": "ESP8266_SIM_01",
            "humedad": Decimal("84.0"),
            "temperatura": Decimal("19.9"),
            "fecha_hora": datetime(
                2026, 11, 4, 13, 22, 10
            )
        }

    # =====================================
    # PRUEBA 1 - CONSULTAR HISTORIAL
    # =====================================

    @patch("historial_api.LecturasDAO")
    def test_api_historial_correcto(self, mock_dao):

        mock_dao.return_value.obtener_ultimas_lecturas.return_value = [
            self.lectura_ejemplo()
        ]

        respuesta = self.cliente.get(
            "/api/historial/lecturas?limite=20"
        )

        self.assertEqual(respuesta.status_code, 200)

        datos = respuesta.get_json()

        self.assertTrue(datos["hay_datos"])
        self.assertEqual(datos["total"], 1)
        self.assertEqual(datos["limite"], 20)

        lectura = datos["lecturas"][0]

        self.assertEqual(lectura["id_lectura"], 174)
        self.assertEqual(lectura["humedad"], 84.0)
        self.assertEqual(lectura["temperatura"], 19.9)
        self.assertEqual(
            lectura["sensor_id"],
            "ESP8266_SIM_01"
        )

        self.assertEqual(
            lectura["fecha_hora"],
            "2026-11-04 13:22:10"
        )

        self.assertTrue(lectura["simulada"])
        self.assertEqual(
            lectura["origen"],
            "Simulado"
        )

        mock_dao.return_value.obtener_ultimas_lecturas.assert_called_once_with(
            20
        )

    # =====================================
    # PRUEBA 2 - HISTORIAL VACIO
    # =====================================

    @patch("historial_api.LecturasDAO")
    def test_api_historial_vacio(self, mock_dao):

        mock_dao.return_value.obtener_ultimas_lecturas.return_value = []

        respuesta = self.cliente.get(
            "/api/historial/lecturas?limite=10"
        )

        self.assertEqual(respuesta.status_code, 200)

        datos = respuesta.get_json()

        self.assertFalse(datos["hay_datos"])
        self.assertEqual(datos["total"], 0)
        self.assertEqual(datos["lecturas"], [])

    # =====================================
    # PRUEBA 3 - LIMITES INVALIDOS
    # =====================================

    def test_api_limite_invalido(self):

        for limite in ("0", "101", "abc", "2.5"):

            with self.subTest(limite=limite):

                respuesta = self.cliente.get(
                    "/api/historial/lecturas",
                    query_string={"limite": limite}
                )

                self.assertEqual(
                    respuesta.status_code,
                    400
                )

                self.assertIn(
                    "error",
                    respuesta.get_json()
                )

    # =====================================
    # PRUEBA 4 - ERROR EN MYSQL
    # =====================================

    @patch("historial_api.LecturasDAO")
    def test_api_historial_error_mysql(self, mock_dao):

        mock_dao.return_value.obtener_ultimas_lecturas.side_effect = (
            mysql.connector.Error("Conexion fallida")
        )

        respuesta = self.cliente.get(
            "/api/historial/lecturas"
        )

        self.assertEqual(respuesta.status_code, 503)

        self.assertIn(
            "error",
            respuesta.get_json()
        )

    # =====================================
    # PRUEBA 5 - PAGINA DEL HISTORIAL
    # =====================================

    def test_pagina_historial(self):

        respuesta = self.cliente.get(
            "/historial"
        )

        self.assertEqual(respuesta.status_code, 200)

        contenido = respuesta.get_data(
            as_text=True
        )

        self.assertIn(
            "Historial de mediciones",
            contenido
        )

        self.assertIn(
            "filas-historial",
            contenido
        )

        self.assertIn(
            "limite-historial",
            contenido
        )

        self.assertIn(
            "historial.js",
            contenido
        )

    # =====================================
    # PRUEBA 6 - CONSULTAR FRECUENCIA
    # =====================================

    @patch("historial_api.obtener_configuracion")
    def test_consultar_configuracion(self, mock_obtener):

        mock_obtener.return_value = {
            "intervalo_segundos": 30
        }

        respuesta = self.cliente.get(
            "/api/historial/configuracion"
        )

        self.assertEqual(respuesta.status_code, 200)

        datos = respuesta.get_json()

        self.assertEqual(
            datos["intervalo_segundos"],
            30
        )

        self.assertIn(
            30,
            datos["intervalos_permitidos"]
        )

    # =====================================
    # PRUEBA 7 - ACTUALIZAR FRECUENCIA
    # =====================================

    @patch("historial_api.guardar_configuracion")
    def test_actualizar_configuracion(self, mock_guardar):

        mock_guardar.return_value = {
            "intervalo_segundos": 60
        }

        respuesta = self.cliente.post(
            "/api/historial/configuracion",
            json={
                "intervalo_segundos": 60
            }
        )

        self.assertEqual(respuesta.status_code, 200)

        datos = respuesta.get_json()

        self.assertEqual(
            datos["intervalo_segundos"],
            60
        )

        mock_guardar.assert_called_once_with(60)

    # =====================================
    # PRUEBA 8 - FALTA FRECUENCIA
    # =====================================

    def test_configuracion_sin_intervalo(self):

        respuesta = self.cliente.post(
            "/api/historial/configuracion",
            json={}
        )

        self.assertEqual(respuesta.status_code, 400)

        self.assertIn(
            "error",
            respuesta.get_json()
        )

    # =====================================
    # PRUEBA 9 - FRECUENCIA INVALIDA
    # =====================================

    @patch("historial_api.guardar_configuracion")
    def test_configuracion_intervalo_invalido(self, mock_guardar):

        mock_guardar.side_effect = ValueError(
            "Intervalo no permitido."
        )

        respuesta = self.cliente.post(
            "/api/historial/configuracion",
            json={
                "intervalo_segundos": 999
            }
        )

        self.assertEqual(respuesta.status_code, 400)

        self.assertIn(
            "error",
            respuesta.get_json()
        )

    # =====================================
    # PRUEBA 10 - PAGINA DE CONFIGURACION
    # =====================================

    @patch("historial_api.obtener_configuracion")
    def test_pagina_configuracion(self, mock_obtener):

        mock_obtener.return_value = {
            "intervalo_segundos": 30
        }

        respuesta = self.cliente.get(
            "/historial/configuracion"
        )

        self.assertEqual(respuesta.status_code, 200)


if __name__ == "__main__":
    unittest.main()
