-- SUDO-GEN Table Schema
-- This file defines the structure of the login table.

CREATE TABLE IF NOT EXISTS `login` (
  `username` VARCHAR(255) NOT NULL,
  `password` VARCHAR(255) NOT NULL,
  PRIMARY KEY (`username`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;