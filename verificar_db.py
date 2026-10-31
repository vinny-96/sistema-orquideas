import mysql.connector

from conexion import obtener_conexion


def verificar_base_datos():

    conexion = None
    cursor = None

    try:
        conexion = obtener_conexion()
        conexion.autocommit = False

        cursor = conexion.cursor()

        cursor.execute("""
            INSERT INTO lecturas_ambientales
            (sensor_id, humedad, temperatura)
            VALUES (%s, %s, %s)
        """, ("PRUEBA_V3", 80.0, 21.0))

        id_prueba = cursor.lastrowid

        cursor.execute("""
            SELECT sensor_id, humedad, temperatura
            FROM lecturas_ambientales
            WHERE id_lectura = %s
        """, (id_prueba,))

        resultado = cursor.fetchone()

        if resultado is None:
            raise RuntimeError("No se pudo recuperar la lectura.")

        print("Conexión MySQL: CORRECTA")
        print("Inserción de prueba: CORRECTA")
        print("Consulta de prueba: CORRECTA")
        print("Lectura recuperada:", resultado)

    except (mysql.connector.Error, RuntimeError) as error:
        print("ERROR:", error)

    finally:
        if conexion is not None:
            conexion.rollback()

        if cursor is not None:
            cursor.close()

        if conexion is not None:
            conexion.close()


if __name__ == "__main__":
    verificar_base_datos()