import math

from conexion import obtener_conexion


class LecturasDAO:

    def registrar_lectura(
        self,
        sensor_id,
        humedad,
        temperatura
    ):

        if not isinstance(sensor_id, str) or not sensor_id.strip():
            raise ValueError("Debe indicar un sensor válido.")

        humedad = float(humedad)
        temperatura = float(temperatura)

        if not math.isfinite(humedad) or not 0 <= humedad <= 100:
            raise ValueError("La humedad debe estar entre 0 y 100.")

        if not math.isfinite(temperatura):
            raise ValueError("La temperatura debe ser válida.")

        conexion = obtener_conexion()

        try:
            cursor = conexion.cursor()

            try:
                sql = """
                INSERT INTO lecturas_ambientales
                (sensor_id, humedad, temperatura)
                VALUES (%s, %s, %s)
                """

                cursor.execute(
                    sql,
                    (sensor_id.strip(), humedad, temperatura)
                )

                conexion.commit()

                return cursor.lastrowid

            finally:
                cursor.close()

        finally:
            conexion.close()


    def obtener_ultimas_lecturas(self, limite=10):

        if not isinstance(limite, int) or not 1 <= limite <= 100:
            raise ValueError("El límite debe estar entre 1 y 100.")

        conexion = obtener_conexion()

        try:
            cursor = conexion.cursor(dictionary=True)

            try:
                sql = """
                SELECT
                    id_lectura,
                    sensor_id,
                    humedad,
                    temperatura,
                    fecha_hora
                FROM lecturas_ambientales
                ORDER BY fecha_hora DESC, id_lectura DESC
                LIMIT %s
                """

                cursor.execute(sql, (limite,))

                return cursor.fetchall()

            finally:
                cursor.close()

        finally:
            conexion.close()