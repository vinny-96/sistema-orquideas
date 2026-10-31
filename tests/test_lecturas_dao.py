import unittest
from unittest.mock import patch, MagicMock

from lecturas_dao import LecturasDAO


class TestLecturasDAO(unittest.TestCase):

    @patch("lecturas_dao.obtener_conexion")
    def test_registrar_lectura(self, mock_conectar):

        conexion = MagicMock()
        cursor = conexion.cursor.return_value

        cursor.lastrowid = 1
        mock_conectar.return_value = conexion

        dao = LecturasDAO()

        resultado = dao.registrar_lectura(
            "SENSOR_01",
            80.0,
            21.0
        )

        self.assertEqual(resultado, 1)
        cursor.execute.assert_called_once()
        conexion.commit.assert_called_once()
        conexion.close.assert_called_once()


    @patch("lecturas_dao.obtener_conexion")
    def test_rechazar_humedad_invalida(self, mock_conectar):

        dao = LecturasDAO()

        with self.assertRaises(ValueError):
            dao.registrar_lectura(
                "SENSOR_01",
                110,
                21
            )

        mock_conectar.assert_not_called()


    @patch("lecturas_dao.obtener_conexion")
    def test_rechazar_sensor_vacio(self, mock_conectar):

        dao = LecturasDAO()

        with self.assertRaises(ValueError):
            dao.registrar_lectura(
                "",
                80,
                21
            )

        mock_conectar.assert_not_called()


    @patch("lecturas_dao.obtener_conexion")
    def test_consultar_lecturas(self, mock_conectar):

        conexion = MagicMock()
        cursor = conexion.cursor.return_value

        cursor.fetchall.return_value = [
            {
                "id_lectura": 1,
                "sensor_id": "SENSOR_01",
                "humedad": 80,
                "temperatura": 21
            }
        ]

        mock_conectar.return_value = conexion

        dao = LecturasDAO()

        resultado = dao.obtener_ultimas_lecturas(10)

        self.assertEqual(len(resultado), 1)
        self.assertEqual(resultado[0]["sensor_id"], "SENSOR_01")

        cursor.execute.assert_called_once()
        conexion.close.assert_called_once()


    @patch("lecturas_dao.obtener_conexion")
    def test_limite_invalido(self, mock_conectar):

        dao = LecturasDAO()

        with self.assertRaises(ValueError):
            dao.obtener_ultimas_lecturas(0)

        mock_conectar.assert_not_called()


if __name__ == "__main__":
    unittest.main()