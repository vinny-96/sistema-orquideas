
import math

from conexion import obtener_conexion


class LecturasDAO:

    def registrar_lectura(
        self,
        sensor_id,
        humedad,
        temperatura,
        distancia_agua_cm=None,
        agua_baja=None
    ):

        if not isinstance(sensor_id, str) or not sensor_id.strip():
            raise ValueError("Debe indicar un sensor válido.")

        humedad = float(humedad)
        temperatura = float(temperatura)

        if not math.isfinite(humedad) or not 0 <= humedad <= 100:
            raise ValueError("La humedad debe estar entre 0 y 100.")

        if not math.isfinite(temperatura) or not -40 <= temperatura <= 85:
            raise ValueError("La temperatura debe ser válida.")

        # Los dos campos del estanque deben venir
        # juntos o estar ausentes.
        if (distancia_agua_cm is None) != (agua_baja is None):
            raise ValueError(
                "La distancia y el estado del agua deben enviarse juntos."
            )

        if distancia_agua_cm is not None:

            if isinstance(distancia_agua_cm, bool):
                raise ValueError("Distancia inválida.")

            distancia_agua_cm = float(distancia_agua_cm)

            if (
                not math.isfinite(distancia_agua_cm)
                or not 2 <= distancia_agua_cm <= 400
            ):
                raise ValueError("Distancia fuera del rango admitido.")

            if not isinstance(agua_baja, bool):
                raise ValueError("Estado del agua inválido.")

        conexion = obtener_conexion()

        try:
            cursor = conexion.cursor()

            try:
                sql = """
                    INSERT INTO lecturas_ambientales
                    (
                        sensor_id,
                        humedad,
                        temperatura,
                        distancia_agua_cm,
                        agua_baja
                    )
                    VALUES (%s, %s, %s, %s, %s)
                """

                cursor.execute(
                    sql,
                    (
                        sensor_id.strip(),
                        humedad,
                        temperatura,
                        distancia_agua_cm,
                        agua_baja
                    )
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
                        distancia_agua_cm,
                        agua_baja,
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
