import tempfile
import unittest

from pathlib import Path
from unittest.mock import patch

from app import app, leer_calendario


class TestCalendario(unittest.TestCase):

    def setUp(self):

        self.directorio = tempfile.TemporaryDirectory()

        self.addCleanup(
            self.directorio.cleanup
        )

        archivo_prueba = (
            Path(self.directorio.name)
            / "calendario.json"
        )

        parche = patch(
            "app.CALENDARIO_FILE",
            archivo_prueba
        )

        parche.start()

        self.addCleanup(
            parche.stop
        )

        app.config["TESTING"] = True

        self.cliente = app.test_client()


    def test_pagina_inicial(self):

        respuesta = self.cliente.get("/")

        self.assertEqual(
            respuesta.status_code,
            200
        )


    def test_guardar_horario(self):

        respuesta = self.cliente.post(
            "/calendario",
            data={
                "dia": "lunes",
                "hora": "09:00"
            }
        )

        self.assertEqual(
            respuesta.status_code,
            302
        )

        self.assertEqual(
            leer_calendario(),
            [
                {
                    "dia": "lunes",
                    "hora": "09:00"
                }
            ]
        )


    def test_no_permitir_duplicados(self):

        datos = {
            "dia": "martes",
            "hora": "10:00"
        }

        self.cliente.post(
            "/calendario",
            data=datos
        )

        self.cliente.post(
            "/calendario",
            data=datos
        )

        self.assertEqual(
            len(leer_calendario()),
            1
        )


    def test_rechazar_dia_invalido(self):

        self.cliente.post(
            "/calendario",
            data={
                "dia": "dia_invalido",
                "hora": "09:00"
            }
        )

        self.assertEqual(
            leer_calendario(),
            []
        )


    def test_eliminar_horario(self):

        datos = {
            "dia": "viernes",
            "hora": "15:00"
        }

        self.cliente.post(
            "/calendario",
            data=datos
        )

        self.cliente.post(
            "/calendario/eliminar",
            data=datos
        )

        self.assertEqual(
            leer_calendario(),
            []
        )


if __name__ == "__main__":
    unittest.main()