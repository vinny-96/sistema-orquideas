
import json
from pathlib import Path


# ==============================
# V7 - CONFIGURACION DEL HISTORIAL
# ==============================

ARCHIVO_CONFIGURACION = (
    Path(__file__).resolve().parent
    / "data"
    / "configuracion_historial.json"
)

INTERVALO_PREDETERMINADO = 30

INTERVALOS_PERMITIDOS = [10, 30, 60, 120]


def validar_intervalo(intervalo):
    """
    Comprueba que el intervalo sea válido.
    """

    if isinstance(intervalo, bool):
        raise ValueError("Intervalo no permitido.")

    try:
        intervalo = int(intervalo)
    except (ValueError, TypeError):
        raise ValueError("El intervalo debe ser un número.")

    if intervalo not in INTERVALOS_PERMITIDOS:
        raise ValueError(
            "El intervalo debe ser 10, 30, 60 o 120 segundos."
        )

    return intervalo


def obtener_configuracion():
    """
    Lee la frecuencia configurada.
    Si no existe el archivo, utiliza 30 segundos.
    """

    if not ARCHIVO_CONFIGURACION.exists():
        return {
            "intervalo_segundos": INTERVALO_PREDETERMINADO
        }

    with open(
        ARCHIVO_CONFIGURACION,
        "r",
        encoding="utf-8"
    ) as archivo:
        configuracion = json.load(archivo)

    intervalo = validar_intervalo(
        configuracion["intervalo_segundos"]
    )

    return {
        "intervalo_segundos": intervalo
    }


def guardar_configuracion(intervalo):
    """
    Guarda la nueva frecuencia del historial.
    """

    intervalo = validar_intervalo(intervalo)

    ARCHIVO_CONFIGURACION.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    configuracion = {
        "intervalo_segundos": intervalo
    }

    archivo_temporal = (
        ARCHIVO_CONFIGURACION.with_suffix(".tmp")
    )

    with open(
        archivo_temporal,
        "w",
        encoding="utf-8"
    ) as archivo:
        json.dump(
            configuracion,
            archivo,
            indent=4,
            ensure_ascii=False
        )

    archivo_temporal.replace(
        ARCHIVO_CONFIGURACION
    )

    return configuracion
