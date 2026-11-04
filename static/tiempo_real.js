
/*
=====================================
 V5 + V6 - MONITOREO AMBIENTAL
 Sistema de Monitoreo de Orquideas
=====================================
*/

// Actualizar cada 5 segundos.
const INTERVALO_ACTUALIZACION = 5000;

// Considerar antigua una medicion con mas de 2 minutos.
const LIMITE_ANTIGUEDAD = 2 * 60 * 1000;


// =====================================
// ELEMENTOS DEL PANEL
// =====================================

const panel = document.getElementById("panel-tiempo-real");

// Mediciones
const valorHumedad = document.getElementById("valor-humedad");
const valorTemperatura = document.getElementById("valor-temperatura");

// V5 - Evaluacion de humedad
const estadoHumedad = document.getElementById("estado-humedad");
const mensajeHumedad = document.getElementById("mensaje-humedad");
const humedadMinima = document.getElementById("humedad-minima");
const humedadMaxima = document.getElementById("humedad-maxima");

// Informacion de la medicion
const sensorId = document.getElementById("sensor-id");
const origenMedicion = document.getElementById("origen-medicion");
const fechaMedicion = document.getElementById("fecha-medicion");
const ultimaActualizacion = document.getElementById("ultima-actualizacion");

// Estado de conexion
const estadoConexion = document.getElementById("estado-conexion");
const indicadorConexion = document.getElementById("indicador-conexion");

// Avisos
const avisoAntiguedad = document.getElementById("aviso-antiguedad");
const avisoSimulacion = document.getElementById("aviso-simulacion");

// Boton
const botonActualizar = document.getElementById("actualizar-ahora");

// URL generada por Flask
const API_URL = panel.dataset.apiUrl;

// Evitar consultas simultaneas
let consultando = false;


// =====================================
// CAMBIAR ESTADO DE CONEXION
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

    if (valor === null || valor === undefined || valor === "") {
        return "--";
    }

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
// COMPROBAR ANTIGUEDAD
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
// V5 - MOSTRAR LIMITES DE HUMEDAD
// =====================================

function mostrarLimites(datos) {

    const minimo = formatearNumero(datos.limite_minimo);
    const maximo = formatearNumero(datos.limite_maximo);

    humedadMinima.textContent =
        minimo === "--" ? "--" : minimo + "%";

    humedadMaxima.textContent =
        maximo === "--" ? "--" : maximo + "%";
}


// =====================================
// V5 - MOSTRAR EVALUACION DE HUMEDAD
// =====================================

function mostrarEstadoHumedad(datos) {

    const codigo = datos.codigo;

    estadoHumedad.className = "tr-humedad-estado";

    if (codigo === "adecuada") {

        estadoHumedad.textContent = "Humedad adecuada";

        estadoHumedad.classList.add(
            "tr-humedad-adecuada"
        );

    } else if (codigo === "baja") {

        estadoHumedad.textContent = "Humedad baja";

        estadoHumedad.classList.add(
            "tr-humedad-baja"
        );

    } else if (codigo === "alta") {

        estadoHumedad.textContent = "Humedad alta";

        estadoHumedad.classList.add(
            "tr-humedad-alta"
        );

    } else {

        estadoHumedad.textContent =
            "Evaluacion no disponible";
    }

    mensajeHumedad.textContent =
        datos.mensaje ||
        "No se pudo evaluar la humedad ambiental.";
}


// =====================================
// LIMPIAR DATOS DEL PANEL
// =====================================

function limpiarPanel() {

    valorHumedad.textContent = "--";
    valorTemperatura.textContent = "--";

    estadoHumedad.className = "tr-humedad-estado";
    estadoHumedad.textContent = "Sin mediciones";

    mensajeHumedad.textContent =
        "Todavia no existen mediciones registradas.";

    humedadMinima.textContent = "--";
    humedadMaxima.textContent = "--";

    sensorId.textContent = "--";
    origenMedicion.textContent = "--";
    fechaMedicion.textContent = "--";

    avisoAntiguedad.hidden = true;
    avisoSimulacion.hidden = true;
}


// =====================================
// MOSTRAR MEDICION UNIFICADA
// =====================================

function mostrarMedicion(datos) {

    // V6 - Humedad y temperatura
    valorHumedad.textContent =
        formatearNumero(datos.humedad);

    valorTemperatura.textContent =
        formatearNumero(datos.temperatura);

    // V5 - Evaluacion y limites
    mostrarEstadoHumedad(datos);
    mostrarLimites(datos);

    // Informacion del dispositivo
    sensorId.textContent = datos.sensor_id ?? "--";

    origenMedicion.textContent = datos.origen ?? "--";

    fechaMedicion.textContent = datos.fecha_hora ?? "--";

    // Advertencia de simulacion
    avisoSimulacion.hidden = !datos.simulada;

    // Comprobar antiguedad
    const antigua = comprobarAntiguedad(
        datos.fecha_hora
    );

    if (antigua) {

        cambiarEstado(
            "Conectado al servidor. La ultima medicion es antigua.",
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

            // Mostrar limites aunque no existan mediciones.
            mostrarLimites(datos);

            cambiarEstado(
                datos.mensaje ||
                "Todavia no existen mediciones registradas.",
                "advertencia"
            );

        } else {

            mostrarMedicion(datos);
        }

        // Hora de la ultima consulta exitosa.
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
// ACTUALIZACION MANUAL
// =====================================

botonActualizar.addEventListener(
    "click",
    actualizarMediciones
);


// =====================================
// INICIAR MONITOREO AUTOMATICO
// =====================================

// Primera consulta al abrir la pagina.
actualizarMediciones();

// Repetir cada 5 segundos.
setInterval(
    actualizarMediciones,
    INTERVALO_ACTUALIZACION
);
