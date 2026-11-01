
#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>
#include <WiFiClient.h>

#include "secretos.h"

struct LecturaAmbiental {
  float humedad;
  float temperatura;
};

// En el futuro reemplazaremos esta funcion
// por las lecturas de un sensor fisico.
LecturaAmbiental obtenerLectura() {
  LecturaAmbiental lectura;

  lectura.humedad = random(780, 861) / 10.0;
  lectura.temperatura = random(190, 241) / 10.0;

  return lectura;
}

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
    millis() - inicio < 20000
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

void setup() {
  Serial.begin(115200);
  delay(1000);

  Serial.println();
  Serial.println("Sistema de Monitoreo de Orquideas");
  Serial.println("NodeMCU ESP8266 - Simulador V4");

  randomSeed(micros());
  conectarWiFi();
}

void loop() {
  if (conectarWiFi()) {
    LecturaAmbiental lectura = obtenerLectura();
    enviarMedicion(lectura);
  }

  delay(30000);
}
