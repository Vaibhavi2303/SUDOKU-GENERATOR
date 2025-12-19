-- SUDO-GEN Database Initialization Script

-- Create the database used in SudoGenProject.py
CREATE DATABASE IF NOT EXISTS planner;
USE planner;

-- Create the user login table
CREATE TABLE IF NOT EXISTS login (
    username VARCHAR(255) NOT NULL,
    password VARCHAR(255) NOT NULL,
    PRIMARY KEY (username)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Optional: Add a default user for testing
-- Username: admin | Password: password123
INSERT IGNORE INTO login (username, password) VALUES ('admin', 'password123');