
#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>
#include <WiFiClient.h>

#include "secretos.h"


// =====================================
// V7 - CONFIGURACION DE INTERVALOS
// =====================================

// Frecuencia inicial si Flask no responde.
unsigned long intervaloEnvioMs = 30000UL;

// Consultar configuracion cada 5 segundos.
const unsigned long INTERVALO_CONSULTA_MS = 5000UL;

unsigned long ultimoEnvioMs = 0;
unsigned long ultimaConsultaMs = 0;

bool primerEnvio = true;
bool primeraConsulta = true;


// =====================================
// ESTRUCTURA DE MEDICIONES
// =====================================

struct LecturaAmbiental {
  float humedad;
  float temperatura;
};


// =====================================
// MEDICIONES SIMULADAS
// =====================================

LecturaAmbiental obtenerLectura() {

  LecturaAmbiental lectura;

  lectura.humedad = random(780, 861) / 10.0;
  lectura.temperatura = random(190, 241) / 10.0;

  return lectura;
}


// =====================================
// CONEXION WIFI
// =====================================

bool conectarWiFi() {

  if (WiFi.status() == WL_CONNECTED) {
    return true;
  }

  Serial.println("Conectando al Wi-Fi...");

  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  unsigned long inicio = millis();

  while (
    WiFi.status() != WL_CONNECTED &&
    millis() - inicio < 20000UL
  ) {
    delay(500);
    Serial.print(".");
  }

  Serial.println();

  if (WiFi.status() == WL_CONNECTED) {

    Serial.println("Wi-Fi conectado correctamente");

    Serial.print("IP del ESP8266: ");
    Serial.println(WiFi.localIP());

    return true;
  }

  Serial.println("No se pudo conectar al Wi-Fi");

  return false;
}


// =====================================
// V4 - ENVIAR MEDICION A MYSQL
// =====================================

void enviarMedicion(LecturaAmbiental lectura) {

  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("Sin conexion Wi-Fi");
    return;
  }

  WiFiClient cliente;
  HTTPClient http;

  if (!http.begin(cliente, API_URL)) {
    Serial.println("Error al iniciar HTTP");
    return;
  }

  http.setTimeout(5000);

  http.addHeader("Content-Type", "application/json");
  http.addHeader("X-API-Key", API_TOKEN);

  String json = "{\"sensor_id\":\"ESP8266_SIM_01\",";
  json += "\"humedad\":";
  json += String(lectura.humedad, 1);
  json += ",\"temperatura\":";
  json += String(lectura.temperatura, 1);
  json += "}";

  Serial.println();
  Serial.print("Enviando: ");
  Serial.println(json);

  int codigo = http.POST(json);

  Serial.print("Codigo HTTP: ");
  Serial.println(codigo);

  if (codigo > 0) {
    Serial.println(http.getString());
  } else {
    Serial.print("Error HTTP: ");
    Serial.println(http.errorToString(codigo));
  }

  http.end();
}


// =====================================
// V7 - VALIDAR FRECUENCIA
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
// V7 - INTERPRETAR CONFIGURACION JSON
// =====================================

bool procesarConfiguracion(String respuesta) {

  int posicion = respuesta.indexOf(
    "\"intervalo_segundos\""
  );

  if (posicion < 0) {
    Serial.println("V7: No se encontro intervalo_segundos.");
    return false;
  }

  posicion = respuesta.indexOf(':', posicion);

  if (posicion < 0) {
    Serial.println("V7: Formato JSON incorrecto.");
    return false;
  }

  String valor = respuesta.substring(posicion + 1);
  valor.trim();

  int segundos = valor.toInt();

  if (!intervaloPermitido(segundos)) {

    Serial.println("V7: Intervalo no permitido.");
    return false;
  }

  unsigned long nuevoIntervalo =
    (unsigned long)segundos * 1000UL;

  if (intervaloEnvioMs != nuevoIntervalo) {

    intervaloEnvioMs = nuevoIntervalo;

    Serial.println();
    Serial.print("V7: Nueva frecuencia aplicada: ");
    Serial.print(segundos);
    Serial.println(" segundos");

  } else {

    Serial.print("V7: Frecuencia actual: ");
    Serial.print(segundos);
    Serial.println(" segundos");
  }

  return true;
}


// =====================================
// V7 - CONSULTAR CONFIGURACION A FLASK
// =====================================

void consultarConfiguracionHistorial() {

  if (WiFi.status() != WL_CONNECTED) {
    return;
  }

  String urlConfiguracion = String(API_URL);

  if (!urlConfiguracion.endsWith("/api/mediciones")) {

    Serial.println(
      "V7: API_URL debe terminar en /api/mediciones"
    );

    return;
  }

  urlConfiguracion.replace(
    "/api/mediciones",
    "/api/historial/configuracion"
  );

  WiFiClient cliente;
  HTTPClient http;

  if (!http.begin(cliente, urlConfiguracion)) {

    Serial.println("V7: Error al iniciar consulta.");
    return;
  }

  http.setTimeout(4000);

  int codigo = http.GET();

  if (codigo == HTTP_CODE_OK) {

    String respuesta = http.getString();

    procesarConfiguracion(respuesta);

  } else {

    Serial.print("V7: Error de configuracion HTTP: ");
    Serial.println(codigo);

    // Se conserva la ultima frecuencia valida.
  }

  http.end();
}


// =====================================
// INICIALIZACION
// =====================================

void setup() {

  Serial.begin(115200);
  delay(1000);

  Serial.println();
  Serial.println("Sistema de Monitoreo de Orquideas");
  Serial.println("NodeMCU ESP8266 - Simulador V7");

  randomSeed(micros());

  conectarWiFi();
}


// =====================================
// BUCLE PRINCIPAL - CONTROL CON MILLIS
// =====================================

void loop() {

  if (!conectarWiFi()) {

    delay(2000);
    return;
  }

  unsigned long ahora = millis();

  // Consultar si el usuario cambio la frecuencia.
  if (
    primeraConsulta ||
    ahora - ultimaConsultaMs >= INTERVALO_CONSULTA_MS
  ) {

    primeraConsulta = false;
    ultimaConsultaMs = millis();

    consultarConfiguracionHistorial();
  }

  // Enviar una medicion segun el intervalo vigente.
  if (
    primerEnvio ||
    millis() - ultimoEnvioMs >= intervaloEnvioMs
  ) {

    primerEnvio = false;
    ultimoEnvioMs = millis();

    LecturaAmbiental lectura = obtenerLectura();

    enviarMedicion(lectura);
  }

  // Pequeña pausa para evitar un bucle ocupado.
  delay(50);
}
