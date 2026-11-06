
#include <Arduino.h>
#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>
#include <WiFiClient.h>
#include <DHT.h>
#include <math.h>

#include "secretos.h"

// =====================================
// SISTEMA DE MONITOREO DE ORQUIDEAS
// Sensores reales + Flask + MySQL
// Descubrimiento automatico de servidor
// =====================================

// LED disponibles
#define LED_VERDE       D1
#define LED_AMARILLO    D2
#define LED_ROJO        D3

// Sensor DHT22
#define DHT_PIN         D5
#define DHT_TIPO        DHT22

// Sensor ultrasonico
#define TRIG_PIN        D6
#define ECHO_PIN        D7

DHT dht(DHT_PIN, DHT_TIPO);

// =====================================
// CONFIGURACION GENERAL
// =====================================

const char* SENSOR_ID = "ESP8266_REAL_01";

const float HUMEDAD_MINIMA = 75.0;
const float HUMEDAD_MAXIMA = 85.0;

// Pendiente de calibrar con el estanque.
const float DISTANCIA_AGUA_BAJA = 20.0;

const bool LED_ACTIVO_ALTO = true;

const unsigned long VELOCIDAD_OLA_MS = 200UL;

const unsigned long INTERVALO_DHT_MS = 2500UL;
const unsigned long INTERVALO_ULTRASONICO_MS = 1000UL;
const unsigned long INTERVALO_CONSULTA_MS = 5000UL;
const unsigned long INTERVALO_REPORTE_MS = 2500UL;
const unsigned long INTERVALO_RECONEXION_MS = 10000UL;

unsigned long intervaloEnvioMs = 30000UL;

// =====================================
// DESCUBRIMIENTO DEL SERVIDOR
// =====================================

// IP del servidor descubierta.
String servidorBase = "";

// Ultimo octeto conocido del notebook.
// Se prueba primero para acelerar la busqueda.
const uint8_t HOST_PREFERIDO = 118;

// Puerto utilizado por Flask.
const uint16_t PUERTO_FLASK = 5000;

uint8_t siguienteHost = 1;

unsigned long ultimaBusqueda = 0;
unsigned long ultimoIntentoPreferido = 0;

const unsigned long PAUSA_BUSQUEDA_MS = 120UL;
const unsigned long REINTENTO_PREFERIDO_MS = 5000UL;

// =====================================
// ESTRUCTURA DE MEDICIONES
// =====================================

struct LecturaAmbiental {
  float humedad;
  float temperatura;
  float distanciaAgua;
};

LecturaAmbiental lecturaActual = {
  NAN,
  NAN,
  NAN
};

bool humedadValida = false;
bool distanciaValida = false;
bool aguaBaja = false;

// =====================================
// TEMPORIZADORES
// =====================================

unsigned long ultimoDHT = 0;
unsigned long ultimoUltrasonico = 0;
unsigned long ultimoEnvio = 0;
unsigned long ultimaConsulta = 0;
unsigned long ultimoReporte = 0;
unsigned long ultimoIntentoWiFi = 0;
unsigned long ultimoPasoOla = 0;

bool primerDHT = true;
bool primerUltrasonico = true;
bool primerEnvio = true;
bool primeraConsulta = true;
bool primerIntentoWiFi = true;
bool wifiConectadoAnteriormente = false;

// =====================================
// ANIMACION DE OLA
// =====================================

const int secuenciaOla[] = {
  LED_ROJO,
  LED_AMARILLO,
  LED_VERDE,
  LED_AMARILLO
};

const int TOTAL_PASOS = 4;

int pasoOla = 0;
bool olaIniciada = false;

// =====================================
// CONTROL DE LED
// =====================================

void controlarLed(int pin, bool encender) {

  digitalWrite(
    pin,
    (encender == LED_ACTIVO_ALTO) ? HIGH : LOW
  );
}

void apagarLeds() {

  controlarLed(LED_ROJO, false);
  controlarLed(LED_AMARILLO, false);
  controlarLed(LED_VERDE, false);
}

void mostrarEstadoHumedad() {

  apagarLeds();

  if (!humedadValida) return;

  float humedad = lecturaActual.humedad;

  if (humedad < HUMEDAD_MINIMA) {

    controlarLed(LED_ROJO, true);

  } else if (humedad > HUMEDAD_MAXIMA) {

    controlarLed(LED_AMARILLO, true);

  } else {

    controlarLed(LED_VERDE, true);
  }
}

void animarAlertaAgua(unsigned long ahora) {

  if (!olaIniciada) {

    olaIniciada = true;
    pasoOla = 0;
    ultimoPasoOla = ahora;

  } else if (
    ahora - ultimoPasoOla >= VELOCIDAD_OLA_MS
  ) {

    ultimoPasoOla = ahora;
    pasoOla = (pasoOla + 1) % TOTAL_PASOS;
  }

  apagarLeds();
  controlarLed(secuenciaOla[pasoOla], true);
}

void actualizarLeds(unsigned long ahora) {

  if (distanciaValida && aguaBaja) {

    animarAlertaAgua(ahora);

  } else {

    olaIniciada = false;
    pasoOla = 0;

    mostrarEstadoHumedad();
  }
}

// =====================================
// LEER DHT22
// =====================================

void actualizarDHT() {

  float humedad = dht.readHumidity();
  float temperatura = dht.readTemperature();

  if (
    isnan(humedad) ||
    isnan(temperatura) ||
    humedad < 0 ||
    humedad > 100 ||
    temperatura < -40 ||
    temperatura > 85
  ) {

    humedadValida = false;
    Serial.println("ERROR: lectura DHT22");
    return;
  }

  lecturaActual.humedad = humedad;
  lecturaActual.temperatura = temperatura;

  humedadValida = true;
}

// =====================================
// LEER ULTRASONICO
// =====================================

float medirDistancia() {

  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);

  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);

  unsigned long duracion = pulseIn(
    ECHO_PIN,
    HIGH,
    30000UL
  );

  if (duracion == 0) {
    return NAN;
  }

  float distancia = duracion * 0.0343 / 2.0;

  if (distancia < 2 || distancia > 400) {
    return NAN;
  }

  return distancia;
}

void actualizarUltrasonico() {

  float distancia = medirDistancia();

  if (isnan(distancia)) {

    distanciaValida = false;
    aguaBaja = false;

    Serial.println(
      "ERROR: lectura del ultrasonico"
    );

    return;
  }

  lecturaActual.distanciaAgua = distancia;
  distanciaValida = true;

  aguaBaja = (
    distancia >= DISTANCIA_AGUA_BAJA
  );
}

// =====================================
// REINICIAR BUSQUEDA DEL SERVIDOR
// =====================================

void limpiarServidor() {

  servidorBase = "";

  siguienteHost = 1;
  ultimaBusqueda = 0;
  ultimoIntentoPreferido = 0;

  primeraConsulta = true;
  primerEnvio = true;
}

// =====================================
// MANTENER WIFI
// =====================================

void mantenerWiFi(unsigned long ahora) {

  if (WiFi.status() == WL_CONNECTED) {

    if (!wifiConectadoAnteriormente) {

      wifiConectadoAnteriormente = true;

      limpiarServidor();

      Serial.println();
      Serial.println("Wi-Fi conectado");

      Serial.print("IP del ESP8266: ");
      Serial.println(WiFi.localIP());

      Serial.print("Mascara de red: ");
      Serial.println(WiFi.subnetMask());

      Serial.print("Puerta de enlace: ");
      Serial.println(WiFi.gatewayIP());

      Serial.println("Buscando servidor Flask...");
    }

    return;
  }

  if (wifiConectadoAnteriormente) {

    wifiConectadoAnteriormente = false;
    limpiarServidor();

    Serial.println("Wi-Fi desconectado");
  }

  if (
    primerIntentoWiFi ||
    ahora - ultimoIntentoWiFi >=
      INTERVALO_RECONEXION_MS
  ) {

    primerIntentoWiFi = false;
    ultimoIntentoWiFi = ahora;

    Serial.println("Conectando al Wi-Fi...");

    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  }
}

// =====================================
// BUSCAR SERVIDOR FLASK
// =====================================

void buscarServidorFlask() {

  if (WiFi.status() != WL_CONNECTED) return;
  if (servidorBase.length() > 0) return;

  unsigned long ahora = millis();

  if (
    ahora - ultimaBusqueda <
    PAUSA_BUSQUEDA_MS
  ) {
    return;
  }

  ultimaBusqueda = ahora;

  // Optimizado para redes /24,
  // como la red del celular utilizada.

  uint8_t octeto;

  if (
    ultimoIntentoPreferido == 0 ||
    ahora - ultimoIntentoPreferido >=
      REINTENTO_PREFERIDO_MS
  ) {

    octeto = HOST_PREFERIDO;
    ultimoIntentoPreferido = ahora;

  } else {

    octeto = siguienteHost;

    if (siguienteHost >= 254) {

      siguienteHost = 1;
      Serial.println(
        "Continuando busqueda de Flask..."
      );

    } else {

      siguienteHost++;
    }
  }

  IPAddress ipLocal = WiFi.localIP();

  IPAddress candidato(
    ipLocal[0],
    ipLocal[1],
    ipLocal[2],
    octeto
  );

  // Ignorar el ESP y la puerta de enlace.

  if (
    candidato == ipLocal ||
    candidato == WiFi.gatewayIP()
  ) {
    return;
  }

  // Comprobar si existe un servidor
  // escuchando en el puerto 5000.

  WiFiClient prueba;
  prueba.setTimeout(200);

  if (!prueba.connect(candidato, PUERTO_FLASK)) {
    return;
  }

  prueba.stop();

  // Verificar que sea nuestra API.

  String base = "http://";
  base += candidato.toString();
  base += ":5000";

  String url = base;
  url += "/api/historial/configuracion";

  WiFiClient cliente;
  HTTPClient http;

  if (!http.begin(cliente, url)) {
    return;
  }

  http.setTimeout(1500);

  int codigo = http.GET();

  if (codigo == HTTP_CODE_OK) {

    String respuesta = http.getString();

    if (
      respuesta.indexOf(
        "\"intervalo_segundos\""
      ) >= 0
    ) {

      servidorBase = base;

      primeraConsulta = true;
      primerEnvio = true;

      Serial.println();
      Serial.println("==========================");
      Serial.println("SERVIDOR FLASK ENCONTRADO");
      Serial.println(servidorBase);
      Serial.println("==========================");
    }
  }

  http.end();
}

// =====================================
// V7: VALIDAR INTERVALOS
// =====================================

bool intervaloPermitido(int segundos) {

  return (
    segundos == 10 ||
    segundos == 30 ||
    segundos == 60 ||
    segundos == 120
  );
}

// =====================================
// V7: PROCESAR CONFIGURACION
// =====================================

bool procesarConfiguracion(String respuesta) {

  int posicion = respuesta.indexOf(
    "\"intervalo_segundos\""
  );

  if (posicion < 0) {
    Serial.println(
      "No se encontro intervalo_segundos"
    );
    return false;
  }

  posicion = respuesta.indexOf(':', posicion);

  if (posicion < 0) {
    return false;
  }

  String valor = respuesta.substring(posicion + 1);
  valor.trim();

  int segundos = valor.toInt();

  if (!intervaloPermitido(segundos)) {
    Serial.println("Intervalo no permitido");
    return false;
  }

  unsigned long nuevoIntervalo =
    (unsigned long)segundos * 1000UL;

  if (intervaloEnvioMs != nuevoIntervalo) {

    intervaloEnvioMs = nuevoIntervalo;

    Serial.print("Nueva frecuencia: ");
    Serial.print(segundos);
    Serial.println(" segundos");
  }

  return true;
}

// =====================================
// V7: CONSULTAR CONFIGURACION
// =====================================

void consultarConfiguracionHistorial() {

  if (
    WiFi.status() != WL_CONNECTED ||
    servidorBase.length() == 0
  ) {
    return;
  }

  String url =
    servidorBase +
    "/api/historial/configuracion";

  WiFiClient cliente;
  HTTPClient http;

  if (!http.begin(cliente, url)) {
    return;
  }

  http.setTimeout(2000);

  int codigo = http.GET();

  if (codigo == HTTP_CODE_OK) {

    procesarConfiguracion(http.getString());

  } else {

    Serial.print("Configuracion HTTP: ");
    Serial.println(codigo);

    if (codigo < 0) {

      Serial.println(
        "Servidor inaccesible. Buscando de nuevo..."
      );

      limpiarServidor();
    }
  }

  http.end();
}

// =====================================
// ENVIAR MEDICIONES A FLASK
// =====================================

void enviarMedicion() {

  if (
    WiFi.status() != WL_CONNECTED ||
    servidorBase.length() == 0
  ) {
    return;
  }

  if (!humedadValida) {

    Serial.println(
      "DHT22 sin lectura valida. Envio cancelado."
    );

    return;
  }

  String url =
    servidorBase + "/api/mediciones";

  WiFiClient cliente;
  HTTPClient http;

  if (!http.begin(cliente, url)) {

    Serial.println("Error al iniciar HTTP");
    return;
  }

  http.setTimeout(2500);

  http.addHeader(
    "Content-Type",
    "application/json"
  );

  http.addHeader(
    "X-API-Key",
    API_TOKEN
  );

  String json = "{\"sensor_id\":\"";
  json += SENSOR_ID;
  json += "\",\"humedad\":";
  json += String(lecturaActual.humedad, 2);
  json += ",\"temperatura\":";
  json += String(lecturaActual.temperatura, 2);

  // Datos opcionales del estanque.
  // Todavia no se guardan en MySQL.

  if (distanciaValida) {

    json += ",\"distancia_agua_cm\":";
    json += String(
      lecturaActual.distanciaAgua,
      2
    );

    json += ",\"agua_baja\":";
    json += (aguaBaja ? "true" : "false");
  }

  json += "}";

  Serial.println();
  Serial.print("Enviando a Flask: ");
  Serial.println(json);

  int codigo = http.POST(json);

  Serial.print("Codigo HTTP: ");
  Serial.println(codigo);

  if (codigo > 0) {

    Serial.println(http.getString());

  } else {

    Serial.print("Error HTTP: ");
    Serial.println(http.errorToString(codigo));

    Serial.println(
      "Conexion perdida. Buscando Flask..."
    );

    limpiarServidor();
  }

  http.end();
}

// =====================================
// MONITOR SERIE
// =====================================

void mostrarReporte() {

  Serial.println();
  Serial.println("-----------------------------");

  if (humedadValida) {

    Serial.print("Humedad real: ");
    Serial.print(lecturaActual.humedad, 2);
    Serial.println(" %");

    Serial.print("Temperatura real: ");
    Serial.print(lecturaActual.temperatura, 2);
    Serial.println(" C");

    if (
      lecturaActual.humedad < HUMEDAD_MINIMA
    ) {

      Serial.println("Estado: HUMEDAD BAJA");

    } else if (
      lecturaActual.humedad > HUMEDAD_MAXIMA
    ) {

      Serial.println("Estado: HUMEDAD ALTA");

    } else {

      Serial.println("Estado: HUMEDAD ADECUADA");
    }

  } else {

    Serial.println("DHT22: lectura invalida");
  }

  if (distanciaValida) {

    Serial.print("Distancia al agua: ");
    Serial.print(
      lecturaActual.distanciaAgua,
      2
    );
    Serial.println(" cm");

    if (aguaBaja) {

      Serial.println("ALERTA: AGUA BAJA");
      Serial.println("LED: ANIMACION DE OLA");

    } else {

      Serial.println("Agua suficiente");
      Serial.println("LED: MODO HUMEDAD");
    }

  } else {

    Serial.println(
      "Ultrasonico: lectura no disponible"
    );
  }

  Serial.print("Wi-Fi: ");

  Serial.println(
    WiFi.status() == WL_CONNECTED
      ? "CONECTADO"
      : "DESCONECTADO"
  );

  Serial.print("Servidor Flask: ");

  if (servidorBase.length() > 0) {
    Serial.println(servidorBase);
  } else {
    Serial.println("BUSCANDO...");
  }

  Serial.print("Frecuencia de envio: ");
  Serial.print(intervaloEnvioMs / 1000UL);
  Serial.println(" segundos");
}

// =====================================
// SETUP
// =====================================

void setup() {

  Serial.begin(115200);
  delay(1000);

  // LED
  pinMode(LED_ROJO, OUTPUT);
  pinMode(LED_AMARILLO, OUTPUT);
  pinMode(LED_VERDE, OUTPUT);

  apagarLeds();

  // Ultrasonico
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  digitalWrite(TRIG_PIN, LOW);

  // DHT22
  dht.begin();

  // Wi-Fi
  WiFi.mode(WIFI_STA);
  WiFi.persistent(false);
  WiFi.setAutoReconnect(true);

  Serial.println();
  Serial.println("==========================");
  Serial.println("MONITOREO DE ORQUIDEAS");
  Serial.println("ESP8266 - SENSORES REALES");
  Serial.println("BUSQUEDA AUTOMATICA FLASK");
  Serial.println("==========================");
}

// =====================================
// LOOP PRINCIPAL
// =====================================

void loop() {

  unsigned long ahora = millis();

  // ---------------------------------
  // LEER DHT22
  // ---------------------------------

  if (
    primerDHT ||
    ahora - ultimoDHT >=
      INTERVALO_DHT_MS
  ) {

    primerDHT = false;
    ultimoDHT = ahora;

    actualizarDHT();
  }

  // ---------------------------------
  // LEER ULTRASONICO
  // ---------------------------------

  if (
    primerUltrasonico ||
    ahora - ultimoUltrasonico >=
      INTERVALO_ULTRASONICO_MS
  ) {

    primerUltrasonico = false;
    ultimoUltrasonico = ahora;

    actualizarUltrasonico();
  }

  // ---------------------------------
  // CONTROLAR LED
  // ---------------------------------

  actualizarLeds(millis());

  // ---------------------------------
  // MANTENER WIFI
  // ---------------------------------

  mantenerWiFi(millis());

  // ---------------------------------
  // LOCALIZAR FLASK
  // ---------------------------------

  if (
    WiFi.status() == WL_CONNECTED &&
    servidorBase.length() == 0
  ) {

    buscarServidorFlask();
  }

  // ---------------------------------
  // OPERACIONES CON EL SERVIDOR
  // ---------------------------------

  if (
    WiFi.status() == WL_CONNECTED &&
    servidorBase.length() > 0
  ) {

    // Consultar frecuencia V7.

    if (
      primeraConsulta ||
      millis() - ultimaConsulta >=
        INTERVALO_CONSULTA_MS
    ) {

      primeraConsulta = false;
      ultimaConsulta = millis();

      consultarConfiguracionHistorial();
    }

    // Enviar mediciones reales.

    if (
      servidorBase.length() > 0 &&
      humedadValida &&
      (
        primerEnvio ||
        millis() - ultimoEnvio >=
          intervaloEnvioMs
      )
    ) {

      primerEnvio = false;
      ultimoEnvio = millis();

      enviarMedicion();
    }
  }

  // ---------------------------------
  // MOSTRAR ESTADO
  // ---------------------------------

  if (
    millis() - ultimoReporte >=
    INTERVALO_REPORTE_MS
  ) {

    ultimoReporte = millis();
    mostrarReporte();
  }

  delay(5);
}
