CREATE DATABASE `network_pr1` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci */;
use db_final_project;
CREATE TABLE `router` (
  `client_name` varchar(20) NOT NULL,
  `client_ip` varchar(45) NOT NULL,
  `port` varchar(10) NOT NULL,
  PRIMARY KEY (`client_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


