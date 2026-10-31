import unittest

from datetime import datetime
from unittest.mock import patch

from app import app
from recordatorios import obtener_riegos_pendientes


class TestRecordatorios(unittest.TestCase):

    def test_notificar_en_horario_programado(self):

        calendario = [
            {
                "dia": "jueves",
                "hora": "09:00"
            }
        ]

        ahora = datetime(
            2026, 10, 29, 9, 0
        )

        resultado = obtener_riegos_pendientes(
            calendario,
            ahora
        )

        self.assertEqual(
            len(resultado),
            1
        )


    def test_no_notificar_antes_de_la_hora(self):

        calendario = [
            {
                "dia": "jueves",
                "hora": "10:00"
            }
        ]

        ahora = datetime(
            2026, 10, 29, 9, 0
        )

        resultado = obtener_riegos_pendientes(
            calendario,
            ahora
        )

        self.assertEqual(
            resultado,
            []
        )


    def test_no_notificar_otro_dia(self):

        calendario = [
            {
                "dia": "viernes",
                "hora": "09:00"
            }
        ]

        ahora = datetime(
            2026, 10, 29, 9, 0
        )

        resultado = obtener_riegos_pendientes(
            calendario,
            ahora
        )

        self.assertEqual(
            resultado,
            []
        )


    def test_multiples_riegos_misma_hora(self):

        calendario = [
            {"dia": "jueves", "hora": "09:00"},
            {"dia": "jueves", "hora": "09:00"},
            {"dia": "viernes", "hora": "09:00"}
        ]

        ahora = datetime(
            2026, 10, 29, 9, 0
        )

        resultado = obtener_riegos_pendientes(
            calendario,
            ahora
        )

        self.assertEqual(
            len(resultado),
            2
        )


    @patch("app.leer_calendario")
    @patch("app.obtener_riegos_pendientes")
    def test_api_recordatorios(
        self,
        mock_pendientes,
        mock_calendario
    ):

        app.config["TESTING"] = True

        mock_calendario.return_value = [
            {"dia": "jueves", "hora": "09:00"}
        ]

        mock_pendientes.return_value = [
            {"dia": "jueves", "hora": "09:00"}
        ]

        cliente = app.test_client()

        respuesta = cliente.get(
            "/api/riegos/pendientes"
        )

        self.assertEqual(
            respuesta.status_code,
            200
        )

        datos = respuesta.get_json()

        self.assertEqual(
            len(datos["pendientes"]),
            1
        )

        self.assertIn(
            "fecha",
            datos
        )


if __name__ == "__main__":
    unittest.main()