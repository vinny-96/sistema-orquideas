from datetime import datetime


DIAS_SEMANA = [
    "lunes",
    "martes",
    "miercoles",
    "jueves",
    "viernes",
    "sabado",
    "domingo"
]


def obtener_riegos_pendientes(calendario, ahora=None):

    if ahora is None:
        ahora = datetime.now()

    dia_actual = DIAS_SEMANA[ahora.weekday()]
    hora_actual = ahora.strftime("%H:%M")

    pendientes = []

    for riego in calendario:

        if (
            riego.get("dia") == dia_actual
            and riego.get("hora") == hora_actual
        ):
            pendientes.append(riego)

    return pendientes