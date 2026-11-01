
import os
import unittest
from unittest.mock import patch

from app import app


class TestAPISensores(unittest.TestCase):

    def setUp(self):
        self.clave = "clave-exclusiva-de-pruebas"
        self.patcher = patch.dict(
            os.environ,
            {"SENSOR_API_KEY": self.clave}
        )
        self.patcher.start()
        self.addCleanup(self.patcher.stop)

        app.config["TESTING"] = True
        self.cliente = app.test_client()

    def test_rechazar_sin_clave(self):
        respuesta = self.cliente.post(
            "/api/mediciones",
            json={
                "sensor_id": "ESP32_SIM_01",
                "humedad": 80,
                "temperatura": 21
            }
        )

        self.assertEqual(respuesta.status_code, 401)

    @patch("api_sensores.LecturasDAO")
    def test_guardar_medicion(self, mock_dao):
        mock_dao.return_value.registrar_lectura.return_value = 1

        respuesta = self.cliente.post(
            "/api/mediciones",
            headers={"X-API-Key": self.clave},
            json={
                "sensor_id": "ESP32_SIM_01",
                "humedad": 80,
                "temperatura": 21
            }
        )

        self.assertEqual(respuesta.status_code, 201)
        self.assertEqual(
            respuesta.get_json()["id_lectura"],
            1
        )

        mock_dao.return_value.registrar_lectura.assert_called_once()

    def test_rechazar_humedad_invalida(self):
        respuesta = self.cliente.post(
            "/api/mediciones",
            headers={"X-API-Key": self.clave},
            json={
                "sensor_id": "ESP32_SIM_01",
                "humedad": 150,
                "temperatura": 21
            }
        )

        self.assertEqual(respuesta.status_code, 400)

    def test_rechazar_temperatura_invalida(self):
        respuesta = self.cliente.post(
            "/api/mediciones",
            headers={"X-API-Key": self.clave},
            json={
                "sensor_id": "ESP32_SIM_01",
                "humedad": 80,
                "temperatura": 100
            }
        )

        self.assertEqual(respuesta.status_code, 400)

    def test_rechazar_json_invalido(self):
        respuesta = self.cliente.post(
            "/api/mediciones",
            headers={"X-API-Key": self.clave},
            data="{mal-formado",
            content_type="application/json"
        )

        self.assertEqual(respuesta.status_code, 400)


if __name__ == "__main__":
    unittest.main()
