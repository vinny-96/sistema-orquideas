import os
from pathlib import Path

import mysql.connector
from dotenv import load_dotenv


RUTA_ENV = Path(__file__).resolve().parent / ".env"

load_dotenv(RUTA_ENV)


def obtener_conexion():

    conexion = mysql.connector.connect(
        host=os.getenv("DB_HOST", "127.0.0.1"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "orquideas_iot"),
        connection_timeout=5
    )

    return conexion
