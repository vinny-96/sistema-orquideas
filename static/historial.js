
/*
=====================================
 V7 - HISTORIAL DE MEDICIONES
 Sistema de Monitoreo de Orquideas
=====================================
*/

// =====================================
// ELEMENTOS DEL HISTORIAL
// =====================================

const panelHistorial = document.getElementById(
    "panel-historial"
);

const limiteHistorial = document.getElementById(
    "limite-historial"
);

const botonHistorial = document.getElementById(
    "actualizar-historial"
);

const estadoHistorial = document.getElementById(
    "estado-historial"
);

const filasHistorial = document.getElementById(
    "filas-historial"
);

// URL generada desde Flask.
const API_HISTORIAL = panelHistorial.dataset.apiUrl;

let consultandoHistorial = false;


// =====================================
// FORMATEAR NUMEROS
// =====================================

function formatearValor(valor, unidad) {

    if (
        valor === null ||
        valor === undefined ||
        valor === ""
    ) {
        return "--";
    }

    const numero = Number(valor);

    if (!Number.isFinite(numero)) {
        return "--";
    }

    return numero.toFixed(1) + " " + unidad;
}


// =====================================
// CREAR CELDA DE LA TABLA
// =====================================

function crearCelda(texto) {

    const celda = document.createElement("td");

    // textContent evita interpretar datos
    // del servidor como codigo HTML.
    celda.textContent = texto;

    return celda;
}


// =====================================
// MOSTRAR MENSAJE EN LA TABLA
// =====================================

function mostrarMensajeTabla(mensaje) {

    filasHistorial.replaceChildren();

    const fila = document.createElement("tr");

    const celda = crearCelda(mensaje);

    celda.colSpan = 5;
    celda.className = "hist-sin-datos";

    fila.appendChild(celda);
    filasHistorial.appendChild(fila);
}


// =====================================
// MOSTRAR MEDICIONES
// =====================================

function mostrarLecturas(lecturas) {

    filasHistorial.replaceChildren();

    if (lecturas.length === 0) {

        mostrarMensajeTabla(
            "Todavia no hay mediciones registradas."
        );

        return;
    }

    for (const lectura of lecturas) {

        const fila = document.createElement("tr");

        fila.appendChild(
            crearCelda(lectura.fecha_hora ?? "--")
        );

        fila.appendChild(
            crearCelda(lectura.sensor_id ?? "--")
        );

        fila.appendChild(
            crearCelda(
                formatearValor(lectura.humedad, "%")
            )
        );

        fila.appendChild(
            crearCelda(
                formatearValor(lectura.temperatura, "°C")
            )
        );

        fila.appendChild(
            crearCelda(lectura.origen ?? "--")
        );

        filasHistorial.appendChild(fila);
    }
}


// =====================================
// CONSULTAR API DEL HISTORIAL
// =====================================

async function cargarHistorial() {

    if (consultandoHistorial) {
        return;
    }

    consultandoHistorial = true;
    botonHistorial.disabled = true;

    estadoHistorial.textContent =
        "Consultando registros de MySQL...";

    try {

        const url = new URL(
            API_HISTORIAL,
            window.location.origin
        );

        url.searchParams.set(
            "limite",
            limiteHistorial.value
        );

        const respuesta = await fetch(url.toString(), {
            method: "GET",
            cache: "no-store"
        });

        if (!respuesta.ok) {

            throw new Error(
                "Error HTTP: " + respuesta.status
            );
        }

        const datos = await respuesta.json();

        if (!Array.isArray(datos.lecturas)) {

            throw new Error(
                "Formato de historial invalido."
            );
        }

        mostrarLecturas(datos.lecturas);

        estadoHistorial.textContent =
            "Se encontraron " +
            datos.total +
            " registros.";

    } catch (error) {

        console.error(
            "Error al consultar historial:",
            error
        );

        mostrarMensajeTabla(
            "No se pudo cargar el historial."
        );

        estadoHistorial.textContent =
            "Error al consultar las mediciones. " +
            "Comprueba Flask y MySQL.";

    } finally {

        consultandoHistorial = false;
        botonHistorial.disabled = false;
    }
}


// =====================================
// EVENTOS DE LA PAGINA
// =====================================

// Actualizar manualmente.
botonHistorial.addEventListener(
    "click",
    cargarHistorial
);

// Cambiar cantidad de registros.
limiteHistorial.addEventListener(
    "change",
    cargarHistorial
);

// Primera consulta al abrir la pagina.
cargarHistorial();
