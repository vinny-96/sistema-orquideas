
# Sistema de Monitoreo de Orquídeas

Sistema web desarrollado en Python y Flask para gestionar
el riego de orquídeas y monitorear las condiciones ambientales.

## Funcionalidades

- Calendario para programar días y horarios de riego.
- Notificaciones de recordatorio en el navegador.
- Almacenamiento de mediciones en MySQL.
- Recepción de mediciones mediante un ESP8266 conectado por Wi-Fi.
- Monitoreo de humedad ambiental.
- Visualización de humedad y temperatura.

## Tecnologías utilizadas

- Python
- Flask
- MySQL/MariaDB
- XAMPP
- HTML, CSS y JavaScript
- ESP8266 (NodeMCU)
- Git y GitHub

## Requisitos para ejecutar el proyecto

- Python instalado.
- Git instalado.
- XAMPP con MySQL/MariaDB.
- Un navegador web.
- Conexión Wi-Fi para las pruebas con ESP8266.

El ESP8266 es opcional para realizar pruebas simuladas
desde un computador.

## Instalación

### 1. Descargar el proyecto

Abrir PowerShell o una terminal y ejecutar:

```powershell
git clone https://github.com/vinny-96/sistema-orquideas.git
cd sistema-orquideas
```

### 2. Crear el entorno virtual

```powershell
python -m venv .venv
```

Activarlo en PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 3. Instalar dependencias

```powershell
python -m pip install -r requirements.txt
```

### 4. Configurar la base de datos

1. Abrir XAMPP Control Panel.
2. Iniciar MySQL.
3. Abrir phpMyAdmin.
4. Crear o importar la base de datos utilizando
   el archivo `database/schema.sql`.

### 5. Configurar las variables de entorno

Copiar `.env.example` y renombrar la copia como `.env`.

Configurar los datos de conexión MySQL según el equipo.

No compartir el archivo `.env`, ya que puede contener
contraseñas y otras credenciales privadas.

### 6. Iniciar el servidor

```powershell
python app.py
```

Abrir en el navegador:

http://127.0.0.1:5000

## Ejecutar las pruebas

```powershell
python -m unittest discover -s tests -v
```

## Estado del proyecto

- V1: Calendario de riego.
- V2: Notificaciones.
- V3: Almacenamiento en MySQL.
- V4: Integración ESP8266.
- V5: Monitoreo de humedad.
- V6: Visualización de humedad y temperatura en tiempo real (implementada).
- V7: Configuración de la frecuencia del historial (pendiente).

## Seguridad

Los archivos `.env` y `secretos.h` contienen
configuración privada y no deben subirse a GitHub.


## Monitoreo en tiempo real (V6)

El sistema permite consultar las últimas mediciones de
humedad y temperatura registradas en MySQL.

### Acceder al monitoreo

1. Iniciar MySQL desde XAMPP.
2. Ejecutar el servidor Flask:

```powershell
python app.py
```

3. Abrir el navegador:

http://127.0.0.1:5000

4. Seleccionar el botón **Humedad y temperatura en tiempo real**.

También se puede acceder directamente desde:

http://127.0.0.1:5000/tiempo-real

### Funcionamiento

El panel consulta automáticamente la API cada 5 segundos.

Muestra:

- Humedad ambiental en porcentaje.
- Temperatura ambiental en grados Celsius.
- Identificador del dispositivo.
- Origen de la medición.
- Fecha y hora del registro.
- Hora de la última actualización del panel.

Si la última medición tiene más de 2 minutos,
se muestra una advertencia de lectura antigua.

**Importante:** el panel consulta la base de datos cada
5 segundos, pero los valores solamente cambian cuando
se reciben nuevas mediciones.

### API disponible

La última medición puede consultarse en:

http://127.0.0.1:5000/api/tiempo-real

El servidor responde utilizando formato JSON.

### Uso sin ESP8266

El sistema web puede ejecutarse sin tener conectado
un dispositivo físico.

En ese caso, se pueden consultar las mediciones
que ya existan en la base de datos.

Para generar nuevas lecturas es necesario utilizar
un ESP8266 configurado o un cliente que envíe datos
válidos a la API de mediciones.

### Aviso sobre datos simulados

Actualmente, el ESP8266 utilizado en el proyecto
genera mediciones simuladas de humedad y temperatura.

Estas mediciones sirven para comprobar el funcionamiento
del sistema, pero no representan necesariamente las
condiciones ambientales reales de las orquídeas.

## Solución de problemas frecuentes

### Error de conexión MySQL

Comprobar que el servicio MySQL esté iniciado en XAMPP
y que los parámetros del archivo `.env` sean correctos.

### Error 404 en el navegador

Comprobar que Flask esté ejecutándose y que se esté
utilizando la dirección correcta.

### El panel muestra valores antiguos

Verificar que el ESP8266 o el cliente de pruebas
continúe enviando nuevas mediciones.

### El panel muestra -- en los valores

Comprobar que:

1. MySQL esté funcionando.
2. Existan registros en la tabla de mediciones.
3. La API `/api/tiempo-real` responda correctamente.
4. El archivo `static/tiempo_real.js` cargue sin errores.

### Error al instalar dependencias

Comprobar que el entorno virtual esté activado y ejecutar:

```powershell
python -m pip install -r requirements.txt
```

## Pruebas del sistema

Para comprobar las funcionalidades implementadas,
ejecutar:

```powershell
python -m unittest discover -s tests -v
```

En V6, el sistema cuenta con 32 pruebas automatizadas.

