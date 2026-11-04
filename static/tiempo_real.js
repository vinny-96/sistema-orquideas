
/* =====================================
   V6 - MONITOREO EN TIEMPO REAL
   Sistema de Monitoreo de Orquídeas
===================================== */

// Actualizar cada 5 segundos.
const INTERVALO_ACTUALIZACION = 5000;

// Considerar antigua una medición con más de 2 minutos.
const LIMITE_ANTIGUEDAD = 2 * 60 * 1000;


// =====================================
// ELEMENTOS DEL PANEL
// =====================================

const panel = document.getElementById("panel-tiempo-real");

const valorHumedad = document.getElementById("valor-humedad");
const valorTemperatura = document.getElementById("valor-temperatura");

const sensorId = document.getElementById("sensor-id");
const origenMedicion = document.getElementById("origen-medicion");
const fechaMedicion = document.getElementById("fecha-medicion");
const ultimaActualizacion = document.getElementById("ultima-actualizacion");

const estadoConexion = document.getElementById("estado-conexion");
const indicadorConexion = document.getElementById("indicador-conexion");

const avisoAntiguedad = document.getElementById("aviso-antiguedad");
const avisoSimulacion = document.getElementById("aviso-simulacion");

const botonActualizar = document.getElementById("actualizar-ahora");

// URL generada por Flask.
const API_URL = panel.dataset.apiUrl;

// Evita consultas simultáneas.
let consultando = false;


// =====================================
// CAMBIAR ESTADO DE CONEXIÓN
// =====================================

function cambiarEstado(mensaje, tipo) {

    estadoConexion.textContent = mensaje;

    indicadorConexion.className = "tr-indicador";

    if (tipo === "activo") {
        indicadorConexion.classList.add("activo");
    }

    if (tipo === "error") {
        indicadorConexion.classList.add("error");
    }

    if (tipo === "advertencia") {
        indicadorConexion.classList.add("advertencia");
    }
}


// =====================================
// FORMATEAR VALORES
// =====================================

function formatearNumero(valor) {

    const numero = Number(valor);

    if (!Number.isFinite(numero)) {
        return "--";
    }

    return numero.toFixed(1);
}


// =====================================
// CONVERTIR FECHA DE MYSQL
// =====================================

function convertirFecha(fechaTexto) {

    if (typeof fechaTexto !== "string") {
        return null;
    }

    const coincidencia = fechaTexto.match(
        /^(\d{4})-(\d{2})-(\d{2}) (\d{2}):(\d{2}):(\d{2})$/
    );

    if (!coincidencia) {
        return null;
    }

    const fecha = new Date(
        Number(coincidencia[1]),
        Number(coincidencia[2]) - 1,
        Number(coincidencia[3]),
        Number(coincidencia[4]),
        Number(coincidencia[5]),
        Number(coincidencia[6])
    );

    if (Number.isNaN(fecha.getTime())) {
        return null;
    }

    return fecha;
}


// =====================================
// COMPROBAR ANTIGÜEDAD
// =====================================

function comprobarAntiguedad(fechaTexto) {

    const fecha = convertirFecha(fechaTexto);

    if (!fecha) {
        avisoAntiguedad.hidden = false;
        return true;
    }

    const diferencia = Date.now() - fecha.getTime();

    const antigua = (
        diferencia > LIMITE_ANTIGUEDAD ||
        diferencia < -LIMITE_ANTIGUEDAD
    );

    avisoAntiguedad.hidden = !antigua;

    return antigua;
}


// =====================================
// LIMPIAR DATOS DEL PANEL
// =====================================

function limpiarPanel() {

    valorHumedad.textContent = "--";
    valorTemperatura.textContent = "--";

    sensorId.textContent = "--";
    origenMedicion.textContent = "--";
    fechaMedicion.textContent = "--";

    avisoAntiguedad.hidden = true;
    avisoSimulacion.hidden = true;
}


// =====================================
// MOSTRAR MEDICIÓN
// =====================================

function mostrarMedicion(datos) {

    valorHumedad.textContent = formatearNumero(
        datos.humedad
    );

    valorTemperatura.textContent = formatearNumero(
        datos.temperatura
    );

    sensorId.textContent = datos.sensor_id ?? "--";

    origenMedicion.textContent = datos.origen ?? "--";

    fechaMedicion.textContent = datos.fecha_hora ?? "--";

    avisoSimulacion.hidden = !datos.simulada;

    const antigua = comprobarAntiguedad(
        datos.fecha_hora
    );

    if (antigua) {

        cambiarEstado(
            "Conectado al servidor. La última medición es antigua.",
            "advertencia"
        );

    } else {

        cambiarEstado(
            "Conectado. Mediciones actualizadas.",
            "activo"
        );

    }
}


// =====================================
// CONSULTAR API DE FLASK
// =====================================

async function actualizarMediciones() {

    if (consultando) {
        return;
    }

    consultando = true;
    botonActualizar.disabled = true;

    try {

        const respuesta = await fetch(API_URL, {
            method: "GET",
            cache: "no-store"
        });

        if (!respuesta.ok) {
            throw new Error(
                "Error HTTP: " + respuesta.status
            );
        }

        const datos = await respuesta.json();

        if (!datos.hay_datos) {

            limpiarPanel();

            cambiarEstado(
                datos.mensaje ||
                "Todavía no existen mediciones registradas.",
                "advertencia"
            );

        } else {

            mostrarMedicion(datos);

        }

        // Hora de la última consulta exitosa al servidor.
        ultimaActualizacion.textContent =
            new Date().toLocaleTimeString("es-CL");

    } catch (error) {

        console.error(
            "Error al actualizar mediciones:",
            error
        );

        cambiarEstado(
            "No se pudieron consultar las mediciones. Comprueba Flask y MySQL.",
            "error"
        );

    } finally {

        consultando = false;
        botonActualizar.disabled = false;

    }
}


// =====================================
// BOTÓN DE ACTUALIZACIÓN MANUAL
// =====================================

botonActualizar.addEventListener(
    "click",
    actualizarMediciones
);


// =====================================
// INICIAR MONITOREO AUTOMÁTICO
// =====================================

// Primera consulta al abrir la página.
actualizarMediciones();

// Repetir cada 5 segundos.
setInterval(
    actualizarMediciones,
    INTERVALO_ACTUALIZACION
);
