// =====================================
// RF2 - NOTIFICACIONES DE RIEGO
// =====================================

const botonActivar = document.getElementById(
    "activar-notificaciones"
);

const estadoNotificaciones = document.getElementById(
    "estado-notificaciones"
);

const alertaRiego = document.getElementById(
    "alerta-riego"
);

const textoAlerta = document.getElementById(
    "texto-alerta-riego"
);

const botonCerrarAlerta = document.getElementById(
    "cerrar-alerta"
);

const avisosEnMemoria = new Set();

let revisando = false;


// =====================================
// ESTADO DEL PERMISO
// =====================================

function actualizarEstado() {

    if (!("Notification" in window)) {

        estadoNotificaciones.textContent =
            "Este navegador no permite notificaciones del sistema.";

        botonActivar.disabled = true;
        return;
    }

    if (!window.isSecureContext) {

        estadoNotificaciones.textContent =
            "Las notificaciones requieren HTTPS o localhost.";

        botonActivar.disabled = true;
        return;
    }

    if (Notification.permission === "granted") {

        estadoNotificaciones.textContent =
            "Notificaciones activadas.";

        botonActivar.disabled = true;

    } else if (Notification.permission === "denied") {

        estadoNotificaciones.textContent =
            "Notificaciones bloqueadas por el navegador.";

        botonActivar.disabled = true;

    } else {

        estadoNotificaciones.textContent =
            "Activa los avisos para recibir recordatorios de riego.";

    }
}


// =====================================
// SOLICITAR PERMISO
// =====================================

async function activarNotificaciones() {

    if (!("Notification" in window)) {
        actualizarEstado();
        return;
    }

    if (!window.isSecureContext) {
        actualizarEstado();
        return;
    }

    try {

        await Notification.requestPermission();

    } catch (error) {

        console.error(
            "No se pudo solicitar el permiso:",
            error
        );
    }

    actualizarEstado();
}


// =====================================
// EVITAR RECORDATORIOS DUPLICADOS
// =====================================

function avisoRegistrado(clave) {

    if (avisosEnMemoria.has(clave)) {
        return true;
    }

    try {

        return localStorage.getItem(clave) === "1";

    } catch (error) {

        return false;
    }
}


function registrarAviso(clave) {

    avisosEnMemoria.add(clave);

    try {

        localStorage.setItem(clave, "1");

    } catch (error) {

        console.warn(
            "No se pudo guardar el historial local de avisos."
        );
    }
}


// =====================================
// MOSTRAR AVISO EN LA PÁGINA
// =====================================

function mostrarAlerta(mensaje) {

    textoAlerta.textContent = mensaje;

    alertaRiego.hidden = false;
}


// =====================================
// CONSULTAR HORARIOS PENDIENTES
// =====================================

async function revisarRecordatorios() {

    if (revisando) {
        return;
    }

    revisando = true;

    try {

        const respuesta = await fetch(
            "/api/riegos/pendientes",
            {
                cache: "no-store"
            }
        );

        if (!respuesta.ok) {
            throw new Error("Error consultando recordatorios.");
        }

        const datos = await respuesta.json();

        const pendientes = datos.pendientes || [];

        const nuevos = pendientes.filter((riego) => {

            const clave =
                `riego:${datos.fecha}:${riego.dia}:${riego.hora}`;

            return !avisoRegistrado(clave);
        });

        if (nuevos.length === 0) {
            return;
        }

        const horarios = nuevos.map(
            riego => `${riego.dia} a las ${riego.hora}`
        );

        const mensaje =
            "Es momento de regar tus orquídeas. " +
            horarios.join(", ") + ".";

        // Aviso visible dentro de la aplicación
        mostrarAlerta(mensaje);

        // Notificación del navegador
        if (
            "Notification" in window &&
            Notification.permission === "granted"
        ) {

            try {

                new Notification(
                    "Recordatorio de riego",
                    {
                        body: mensaje,
                        tag: `riego-${datos.fecha}`
                    }
                );

            } catch (error) {

                console.error(
                    "No se pudo mostrar la notificación:",
                    error
                );
            }
        }

        // Marcar como notificados
        nuevos.forEach((riego) => {

            const clave =
                `riego:${datos.fecha}:${riego.dia}:${riego.hora}`;

            registrarAviso(clave);
        });

    } catch (error) {

        console.error(
            "Error al revisar recordatorios:",
            error
        );

    } finally {

        revisando = false;
    }
}


// =====================================
// EVENTOS
// =====================================

botonActivar.addEventListener(
    "click",
    activarNotificaciones
);

botonCerrarAlerta.addEventListener(
    "click",
    () => {
        alertaRiego.hidden = true;
    }
);


// =====================================
// INICIAR MONITOREO
// =====================================

actualizarEstado();

revisarRecordatorios();

// Revisar cada 10 segundos
setInterval(revisarRecordatorios, 10000);

// Revisar al volver a la pestaña
document.addEventListener(
    "visibilitychange",
    () => {

        if (!document.hidden) {
            revisarRecordatorios();
        }
    }
);