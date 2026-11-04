Sistema de Monitoreo de Orquídeas
Aplicación web desarrollada con Python y Flask para programar el riego de orquídeas, mostrar recordatorios y consultar mediciones ambientales almacenadas en MySQL/MariaDB.

El proyecto integra un ESP8266 (NodeMCU) conectado por Wi-Fi. En la implementación actual, el dispositivo simula valores de humedad y temperatura para probar la comunicación, el monitoreo y el historial; no realiza mediciones físicas del ambiente.
Funcionalidades
- V1 — Calendario de riego: agregar, visualizar y eliminar horarios de riego por día y hora.
- V2 — Recordatorios: avisos de riego en el navegador, sujetos a los permisos de notificación.
- V3 — Almacenamiento: registro y consulta de mediciones en MySQL/MariaDB.
- V4 — Integración Wi-Fi: recepción de datos enviados por el ESP8266 a la API de Flask.
- V5 — Evaluación de humedad: clasificación como baja, adecuada o alta según límites configurables.
- V6 — Monitoreo en tiempo real: panel unificado con humedad, temperatura, estado del ambiente e información del dispositivo; actualiza la consulta cada 5 segundos.
- V7 — Frecuencia e historial: configuración de la frecuencia de envío del ESP8266 y consulta de los últimos registros históricos desde la web.
Tecnologías
- Python, Flask y unittest.
- MySQL/MariaDB y XAMPP.
- HTML, CSS y JavaScript.
- ESP8266 (NodeMCU) y Wi-Fi.
- Git y GitHub.
Requisitos
- Python y Git instalados.
- XAMPP con MySQL/MariaDB, o una instancia equivalente de MySQL/MariaDB.
- Navegador web actualizado.
- Conexión Wi-Fi para utilizar el ESP8266.
- ESP8266 y Arduino IDE con soporte para la placa correspondiente, solo si se realizarán pruebas con el dispositivo.
Nota: la aplicación web puede ejecutarse sin conectar el ESP8266. En ese caso, mostrará las lecturas existentes en MySQL; para generar otras nuevas es necesario un dispositivo o cliente que envíe solicitudes válidas a la API.
Instalación
1. Obtener el proyecto
git clone https://github.com/vinny-96/sistema-orquideas.git
cd sistema-orquideas
2. Crear y activar el entorno virtual
python -m venv .venv
.\.venv\Scripts\Activate.ps1
3. Instalar las dependencias
python -m pip install -r requirements.txt
4. Preparar la base de datos
1. Abrir el panel de XAMPP e iniciar MySQL.
2. Abrir phpMyAdmin o el cliente SQL que prefieras.
3. Ejecutar o importar database/schema.sql para crear la estructura requerida por el proyecto.
4. Comprobar que los datos de conexión coincidan con la configuración local.
5. Configurar el entorno
Crear una copia de .env.example con el nombre .env y completar los valores solicitados en ese archivo según tu equipo.

En particular, la evaluación de V5 y V6 admite los parámetros:
HUMEDAD_MIN=75
HUMEDAD_MAX=85
Estos valores representan el rango de referencia utilizado por la aplicación (porcentaje de humedad). Pueden ajustarse según los criterios del proyecto; no constituyen por sí solos una recomendación universal para todas las orquídeas.

Seguridad: no subir .env a GitHub ni compartir sus contraseñas o claves de acceso.
6. Iniciar el servidor
python app.py
Abrir la página principal:

http://127.0.0.1:5000/

El servidor incluido con Flask se utiliza para desarrollo y pruebas, no para publicar la aplicación directamente en producción.
Uso del sistema
Calendario y recordatorios (V1 y V2)
Desde la página principal se pueden programar y eliminar horarios de riego. El botón Activar notificaciones solicita, cuando corresponde, permiso al navegador para mostrar recordatorios. Para comprobar los avisos durante las pruebas, mantener abierta la aplicación en un navegador compatible.
Monitoreo ambiental unificado (V5 y V6)
Acceso: http://127.0.0.1:5000/tiempo-real

El panel muestra:
- Última humedad ambiental registrada y su estado: baja, adecuada o alta.
- Temperatura registrada en grados Celsius.
- Límites mínimo y máximo de humedad configurados.
- Identificador y origen reportado para el dispositivo.
- Fecha y hora de la medición y de la última actualización de la pantalla.
- Aviso cuando la última lectura tiene más de 2 minutos.
El navegador consulta la API aproximadamente cada 5 segundos. Este intervalo de actualización no es lo mismo que la frecuencia con la que el ESP8266 envía y registra nuevas mediciones.

La antigua ruta /humedad se conserva por compatibilidad y redirige a /tiempo-real. La API anterior /api/humedad/estado sigue disponible.
Configuración de la frecuencia (V7)
Acceso: http://127.0.0.1:5000/historial/configuracion

Desde esta página se selecciona la frecuencia con la que el ESP8266 envía las lecturas simuladas. Los intervalos disponibles son 10, 30, 60 o 120 segundos.

La configuración se conserva en un archivo JSON local administrado por la aplicación. El ESP8266 consulta periódicamente la API de configuración y aplica el nuevo intervalo sin necesitar que se vuelva a cargar el programa en la placa.
Historial de mediciones (V7)
Acceso: http://127.0.0.1:5000/historial

El historial consulta MySQL y presenta una tabla con fecha y hora, dispositivo, humedad, temperatura y origen de las lecturas. Se muestran primero los registros más recientes y se puede seleccionar entre 10, 20, 50 o 100 resultados. El botón Actualizar historial realiza una nueva consulta sin tener que recargar toda la página.

La consulta admite entre 1 y 100 registros por solicitud; el valor predeterminado de la API es 20.
Integración con ESP8266 (V4 y V7)
El programa de la placa se encuentra en el archivo orquideas_simulador.ino. Localiza ese archivo en la carpeta del simulador dentro del proyecto antes de abrirlo con Arduino IDE.

Para probarlo:
1. Iniciar MySQL y Flask en el computador.
2. Conectar el ESP8266 y el computador a una red desde la que puedan comunicarse.
3. Configurar en el proyecto de Arduino las credenciales Wi-Fi, la dirección de red del servidor Flask y la clave requerida por la API, sin publicarlas en el repositorio.
4. Cargar el programa en el ESP8266 mediante Arduino IDE y revisar el monitor serie.
5. Verificar la recepción de lecturas en /api/tiempo-real y /historial.
6. Cambiar la frecuencia desde /historial/configuracion y comprobar en el monitor serie que se aplique.
Cuando la placa se conecta desde otro equipo, no debe utilizar 127.0.0.1 como dirección del servidor, porque esa dirección corresponde al propio dispositivo. Se necesita la dirección local alcanzable del computador donde se ejecuta Flask.

El archivo secretos.h puede contener credenciales privadas y no debe publicarse. Utilizar un archivo de ejemplo sin contraseñas reales cuando corresponda.
API disponible
Método	Ruta	Descripción
POST	/api/mediciones	Recibe una medición del dispositivo; requiere los datos y la clave de acceso definidos por la API.
GET	/api/humedad/estado	Devuelve la evaluación de humedad de la última lectura (V5).
GET	/api/tiempo-real	Devuelve humedad, temperatura, evaluación y datos del dispositivo (V6).
GET	/api/historial/configuracion	Consulta el intervalo de registro configurado (V7).
POST	/api/historial/configuracion	Actualiza la frecuencia enviando JSON con intervalo_segundos (V7).
GET	/api/historial/lecturas?limite=20	Consulta las últimas mediciones registradas en MySQL (V7).
GET	/api/riegos/pendientes	Consulta recordatorios de riego pendientes (V2).


Ejemplos para consultar desde el navegador:
- http://127.0.0.1:5000/api/tiempo-real
- http://127.0.0.1:5000/api/historial/configuracion
- http://127.0.0.1:5000/api/historial/lecturas?limite=20
Un límite de historial fuera del rango permitido devuelve HTTP 400. Los errores de consulta de MySQL se responden mediante un estado de error apropiado, como HTTP 503 en las rutas de monitoreo probadas.
Pruebas automatizadas
Ejecutar desde la raíz del proyecto, con el entorno virtual activado:
python -m unittest discover -s tests -v
Resultado verificado en V7 (4 de noviembre de 2026): 42 pruebas ejecutadas y 42 aprobadas (OK).

Las pruebas abarcan calendario, recordatorios, recepción de mediciones, acceso a lecturas, evaluación de humedad, monitoreo en tiempo real, configuración de frecuencia y consulta del historial.

Algunas pruebas provocan deliberadamente excepciones simuladas de MySQL utilizando mock; pueden aparecer mensajes de error en la consola aunque las pruebas finalicen correctamente con OK.
Seguridad y limitaciones
- No subir .env, secretos.h, contraseñas ni claves de API a GitHub.
- Verificar .gitignore y los archivos que Git incluirá antes de hacer un commit.
- El proyecto utiliza datos simulados del ESP8266: no se deben interpretar como mediciones físicas del cultivo.
- Las rutas locales de configuración están diseñadas para el entorno de pruebas del proyecto. Antes de exponer la aplicación a Internet, incorporar autenticación, controles de acceso, protección de las credenciales y un servidor apto para producción.
- El panel en tiempo real y el historial muestran valores almacenados; el tiempo entre nuevas lecturas depende de la frecuencia configurada y de que el dispositivo siga enviándolas.
Solución de problemas
Flask no inicia o hay errores de importación
Activar el entorno virtual e instalar las dependencias:
python -m pip install -r requirements.txt
No se pueden consultar las mediciones
Comprobar que MySQL esté iniciado, que .env tenga los parámetros correctos y que exista la tabla creada desde database/schema.sql.
El monitoreo muestra -- o datos antiguos
Comprobar que existan registros en MySQL, que /api/tiempo-real responda y que el ESP8266 esté enviando nuevas mediciones. El aviso de antigüedad aparece cuando la lectura supera los 2 minutos.
El historial aparece vacío
Revisar /api/historial/lecturas?limite=20, la conexión MySQL y la carga de static/historial.js en el navegador.
El ESP8266 no puede comunicarse con Flask
Comprobar la conexión Wi-Fi, la dirección local configurada para el servidor, que el equipo sea accesible desde la red y que las credenciales de la API coincidan.
La frecuencia no cambia
Verificar que /api/historial/configuracion devuelva el nuevo intervalo y revisar las solicitudes del ESP8266 en el monitor serie. La placa debe estar conectada y consultando la configuración.
Estado del proyecto
- V1: Calendario de riego — implementada.
- V2: Recordatorios en el navegador — implementada.
- V3: Registro de mediciones en MySQL — implementada.
- V4: Integración de ESP8266 por Wi-Fi — implementada con datos simulados.
- V5: Evaluación de humedad — implementada.
- V6: Panel unificado de monitoreo ambiental — implementada.
- V7: Frecuencia configurable y consulta visual del historial — implementada y probada.
Repositorio: https://github.com/vinny-96/sistema-orquideas.git