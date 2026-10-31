CREATE DATABASE IF NOT EXISTS orquideas_iot
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

USE orquideas_iot;

CREATE TABLE IF NOT EXISTS lecturas_ambientales (

    id_lectura BIGINT AUTO_INCREMENT PRIMARY KEY,

    sensor_id VARCHAR(50) NOT NULL,

    humedad DECIMAL(5,2) NOT NULL,

    temperatura DECIMAL(5,2) NOT NULL,

    fecha_hora DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_fecha_hora (fecha_hora),

    INDEX idx_sensor_fecha (sensor_id, fecha_hora)

) ENGINE=InnoDB;