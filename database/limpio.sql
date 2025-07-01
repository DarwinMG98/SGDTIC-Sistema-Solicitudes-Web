/*M!999999\- enable the sandbox mode */ 
-- MariaDB dump 10.19-11.7.2-MariaDB, for Win64 (AMD64)
--
-- Host: localhost    Database: sistema_solicitudes
-- ------------------------------------------------------
-- Server version	11.7.2-MariaDB

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*M!100616 SET @OLD_NOTE_VERBOSITY=@@NOTE_VERBOSITY, NOTE_VERBOSITY=0 */;

--
-- Table structure for table `configuracion`
--

DROP TABLE IF EXISTS `configuracion`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `configuracion` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `clave` varchar(50) NOT NULL,
  `valor` varchar(255) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `clave` (`clave`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `configuracion`
--

LOCK TABLES `configuracion` WRITE;
/*!40000 ALTER TABLE `configuracion` DISABLE KEYS */;
INSERT INTO `configuracion` VALUES
(1,'logo_municipio','img/logo_municipio3.png');
/*!40000 ALTER TABLE `configuracion` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `documentos_adjuntos`
--

DROP TABLE IF EXISTS `documentos_adjuntos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `documentos_adjuntos` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `solicitud_id` int(11) DEFAULT NULL,
  `nombre_archivo` varchar(255) DEFAULT NULL,
  `ruta_archivo` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `solicitud_id` (`solicitud_id`),
  CONSTRAINT `documentos_adjuntos_ibfk_1` FOREIGN KEY (`solicitud_id`) REFERENCES `solicitudes` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=17 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `documentos_adjuntos`
--

LOCK TABLES `documentos_adjuntos` WRITE;
/*!40000 ALTER TABLE `documentos_adjuntos` DISABLE KEYS */;
INSERT INTO `documentos_adjuntos` VALUES
(1,25,'DGIP_SAEw_4.pdf','DGIP_SAEw_4.pdf'),
(2,25,'DGIP_SAEw_3.pdf','DGIP_SAEw_3.pdf'),
(3,25,'DGIP_SAEw_2.pdf','DGIP_SAEw_2.pdf'),
(4,25,'243_ISWD732_GR2SW_2025-1_Calificaciones.pdf','243_ISWD732_GR2SW_2025-1_Calificaciones.pdf'),
(5,28,'MarzoElliot.pdf','28_1750182747_b393dbd640aa4b818696128ae007eed3.pdf'),
(6,28,'MarzoDarwin.pdf','28_1750182747_5c069b46c3c945729c917ad24859c093.pdf'),
(7,28,'InformePoryectoBimestre1.pdf','InformePoryectoBimestre1.pdf'),
(8,30,'DGIP_SAEw (4).pdf','30_1750192235_571d65837ee040d8a61e1da1263e2fec.pdf'),
(9,30,'DGIP_SAEw (3).pdf','30_1750192235_83dae0dd2df740769609dd3833af7446.pdf'),
(10,30,'DGIP_SAEw (2).pdf','30_1750192235_95a0c6196d494af08269ff6b75f74eda.pdf'),
(11,30,'InformePoryectoBimestre1.pdf','InformePoryectoBimestre1.pdf'),
(12,33,'DGIP_SAEw (3).pdf','33_1750195564_008badb6db774c8ca08223c9aa559d6f.pdf'),
(13,33,'DGIP_SAEw (2).pdf','33_1750195564_0ae04b53a649455c8fd7207d12188bd8.pdf'),
(14,33,'DGIP_SAEw (1).pdf','33_1750195564_564e86f94783496e8e66b1f5a7f7bdc7.pdf'),
(15,33,'InformePoryectoBimestre1.pdf','InformePoryectoBimestre1.pdf'),
(16,41,'GADDMQ-SGDTIC-UA-2025-0329-M.pdf','41_1750279454_e9d5a6a9e88740feb54f366a29eed3b5.pdf');
/*!40000 ALTER TABLE `documentos_adjuntos` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `firmas`
--

DROP TABLE IF EXISTS `firmas`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `firmas` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `solicitud_id` int(11) DEFAULT NULL,
  `firmante` varchar(100) DEFAULT NULL,
  `tipo` enum('solicitante','aprobador') DEFAULT NULL,
  `fecha_firma` datetime DEFAULT current_timestamp(),
  `ruta_firma` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `solicitud_id` (`solicitud_id`),
  CONSTRAINT `firmas_ibfk_1` FOREIGN KEY (`solicitud_id`) REFERENCES `solicitudes` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `firmas`
--

LOCK TABLES `firmas` WRITE;
/*!40000 ALTER TABLE `firmas` DISABLE KEYS */;
/*!40000 ALTER TABLE `firmas` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `solicitantes`
--

DROP TABLE IF EXISTS `solicitantes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `solicitantes` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `nombre` text DEFAULT NULL,
  `apellido` text DEFAULT NULL,
  `correo` text DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `solicitantes`
--

LOCK TABLES `solicitantes` WRITE;
/*!40000 ALTER TABLE `solicitantes` DISABLE KEYS */;
INSERT INTO `solicitantes` VALUES
(1,'Juan','P├®rez','juan.perez@example.com'),
(2,'Darwin','Guachamin','darwinmario98_@hotmail.com'),
(3,'Darwin','Guachamin','juan.perez@example.com'),
(4,'Daniela','Moran','daniela.moran@quito.gob.ec'),
(5,'Byron','Carpio','byron.carpio@quito.gob.ec'),
(6,'alexandra ','paullan','alexandra.paullan@quito.gob.ec');
/*!40000 ALTER TABLE `solicitantes` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `solicitud_detalle`
--

DROP TABLE IF EXISTS `solicitud_detalle`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `solicitud_detalle` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `solicitud_id` int(11) NOT NULL,
  `fecha` date DEFAULT NULL,
  `nombre_completo` varchar(255) DEFAULT NULL,
  `unidad` varchar(255) DEFAULT NULL,
  `correo` varchar(255) DEFAULT NULL,
  `telefono` varchar(50) DEFAULT NULL,
  `responsable_tecnico` varchar(255) DEFAULT NULL,
  `origen_solicitud` varchar(255) DEFAULT NULL,
  `anteproyecto` varchar(255) DEFAULT NULL,
  `motivo` text DEFAULT NULL,
  `tipo_servidor` varchar(100) DEFAULT NULL,
  `sistema_operativo` varchar(100) DEFAULT NULL,
  `version_so` varchar(100) DEFAULT NULL,
  `vcpu` int(11) DEFAULT NULL,
  `ram` int(11) DEFAULT NULL,
  `disco_sistema` int(11) DEFAULT NULL,
  `disco_datos` int(11) DEFAULT NULL,
  `vida_util` varchar(100) DEFAULT NULL,
  `justificacion_recursos` text DEFAULT NULL,
  `accesos` text DEFAULT NULL,
  `responsable_aplicacion` varchar(255) DEFAULT NULL,
  `unidad_responsable` varchar(255) DEFAULT NULL,
  `contacto_soporte` varchar(255) DEFAULT NULL,
  `observaciones_adicionales` text DEFAULT NULL,
  `firma_solicitante` varchar(255) DEFAULT NULL,
  `cargo_solicitante` varchar(255) DEFAULT NULL,
  `firma_jefe` varchar(255) DEFAULT NULL,
  `cargo_jefe` varchar(255) DEFAULT NULL,
  `nombre_servidor` varchar(100) DEFAULT NULL,
  `ip_servidor` varchar(50) DEFAULT NULL,
  `rol_servidor` varchar(100) DEFAULT NULL,
  `fecha_creacion_servidor` date DEFAULT NULL,
  `motivo_eliminacion` text DEFAULT NULL,
  `validaciones` varchar(250) DEFAULT NULL,
  `motivo_check` varchar(250) DEFAULT NULL,
  `motivo_otro` varchar(250) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `solicitud_id` (`solicitud_id`),
  CONSTRAINT `solicitud_detalle_ibfk_1` FOREIGN KEY (`solicitud_id`) REFERENCES `solicitudes` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=19 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `solicitud_detalle`
--

LOCK TABLES `solicitud_detalle` WRITE;
/*!40000 ALTER TABLE `solicitud_detalle` DISABLE KEYS */;
INSERT INTO `solicitud_detalle` VALUES
(10,24,'2025-06-16','Darwin Guachamin','Pasante','darwinmario98_@hotmail.com','0984083414','si aplica','Correo institucional','nombre','crear servidor','Producci├│n','Windows Server','2020',2,2,2,2,'2 a├▒os','crear servidor','todos los pasantes','Darwin Guachamin','Pasantes','darwin98@gmail.com','Ninguna','Darwin Guachamin','Pasante','','',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(11,25,'2025-06-16','Juan Perez','Pasante','juanperez@hotmail.com','0984083414','no ','Correo institucional','nombre','ascjnekjnfw','Producci├│n','Windows Server','2020',1,1,1,1,'2 a├▒os','asfcewqvg','acwqvqwa','qvcqawvf','qawvqawv','qwvqawv','qwvqwv','Juan Perez','Pasante','','',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(12,27,'2025-06-17','Darwin Guachamin','Pasante','darwinmario98@gmail.com','0984083414','no','','','','','windows','',NULL,NULL,NULL,NULL,'','','','','','','','Darwin Guachamin','Pasante','','','asdwaq','178.255.25','Producci├│n','2025-06-17','ascqweagw','respaldo, no_requerido','migracion, obsolescencia',''),
(13,28,'2025-06-17','Darwin Guachamin','Pasante','darwin98@gmal.comi','0984083414','no','Correo institucional','asfasf','asfasf','Producci├│n','Windows Server','2020',3,2,2,2,'2 a├▒os ','acwevfwesavf','cqwcq','qcwqwc','qcqw','qcwqw','cqwwqc','darwin guachamin','pasante','','',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(14,29,'2025-06-17','Juan Perez','Pasante','darwinmario98_@hotmail.com','0984083414','no','','','','','Windows','',NULL,NULL,NULL,NULL,'','','','','','','','Juan Perez','Pasante','','','asf','172.258.26','Producci├│n, Desarrollo','2025-06-17','fvqawegwg','respaldo, no_requerido','migracion, obsolescencia',''),
(15,30,'2025-06-17','Darwin Guachamin','Pasante','darwinmario98_@hotmail.com','0984083414','no','Correo institucional, Anteproyecto aprobado','asdasd','asdas','Producci├│n, Desarrollo','Linux','2020',2,2,2,2,'2 a├▒os','sdfdf','dfsdf','sdfsd','sdfsd','sdfsd','sdfsd','Darwin Guachamin','Pasante','','',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(16,33,'2025-06-17','Darwin Guachamin','Pasante','darwinmario98_@hotmail.com','0984083414','no','Correo institucional, Anteproyecto aprobado','frdgfd','dfgdf','Producci├│n, Desarrollo','Windows Server','2020',2,2,2,2,'2 a├▒os','ascascdas','asdcasc','ascdas','casc','ascas','ascasc','darwin guachamin','pasante','','',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(17,38,'2025-06-18','darwin guachamin','pasante','darwinmario98_@hotmail.com','0984083414','no',NULL,NULL,NULL,NULL,'windows',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'ewfwefewf','darwin guachamin','pasante','','','scqwc','172.25.254','Producci├│n','2025-06-18','ascfdqwf','respaldo, no_requerido','migracion, falta_uso',''),
(18,41,'2025-06-18','Daniela','infraestrcu','danielamoran@quito.fov.das','0997985834','noi','Correo institucional','ddfaf','asdasdas','Producci├│n','Windows Server','2019',3,100,100,100,'12 ms','faife','centro de computo','Daniela moran','inafrestructura','daniela.moran@quito.gob.ec','ffdfsdf','danielamoran','operadoe it','','',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL);
/*!40000 ALTER TABLE `solicitud_detalle` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `solicitudes`
--

DROP TABLE IF EXISTS `solicitudes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `solicitudes` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `usuario_id` int(11) DEFAULT NULL,
  `tipo` enum('crear','eliminar') NOT NULL,
  `fecha_solicitud` datetime DEFAULT current_timestamp(),
  `estado` enum('pendiente','aprobado','rechazado') DEFAULT 'pendiente',
  `observaciones` text DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `usuario_id` (`usuario_id`),
  CONSTRAINT `solicitudes_ibfk_1` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=42 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `solicitudes`
--

LOCK TABLES `solicitudes` WRITE;
/*!40000 ALTER TABLE `solicitudes` DISABLE KEYS */;
INSERT INTO `solicitudes` VALUES
(24,2,'crear','2025-06-16 11:20:32','aprobado','Falta documentos adjuntos'),
(25,1,'crear','2025-06-16 11:59:20','rechazado','Falta archivos\r\n'),
(27,2,'eliminar','2025-06-17 11:57:39','pendiente','falta observaciones\r\n'),
(28,2,'crear','2025-06-17 12:52:27','aprobado','falta documentos'),
(29,1,'eliminar','2025-06-17 15:17:39','aprobado','Falta observaciones'),
(30,2,'crear','2025-06-17 15:30:35','aprobado','Falta archivos'),
(33,2,'crear','2025-06-17 16:26:04','aprobado','Falta documentos'),
(38,2,'eliminar','2025-06-18 15:21:35','pendiente',NULL),
(41,1,'crear','2025-06-18 15:44:14','pendiente','ffdfsdf');
/*!40000 ALTER TABLE `solicitudes` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `usuarios`
--

DROP TABLE IF EXISTS `usuarios`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `usuarios` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `nombre` varchar(100) DEFAULT NULL,
  `apellido` varchar(100) DEFAULT NULL,
  `correo` varchar(100) DEFAULT NULL,
  `contrase├▒a` varchar(255) DEFAULT NULL,
  `rol` enum('admin','solicitante') NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `correo` (`correo`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `usuarios`
--

LOCK TABLES `usuarios` WRITE;
/*!40000 ALTER TABLE `usuarios` DISABLE KEYS */;
INSERT INTO `usuarios` VALUES
(1,'Administrador',NULL,'admin@correo.com','123456','admin'),
(2,'Solicitante Prueba','Prueba','solicitante@correo.com','123456','solicitante'),
(3,'Admin Ejemplo',NULL,'admin@ejemplo.com','1234','admin');
/*!40000 ALTER TABLE `usuarios` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*M!100616 SET NOTE_VERBOSITY=@OLD_NOTE_VERBOSITY */;

-- Dump completed on 2025-06-18 16:21:29
