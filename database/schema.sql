-- =====================================================================
-- Cloud-Based Weather Information Management System
-- Database Design & DDL Schema Script for MySQL 8.0+ / AWS RDS / GCP Cloud SQL
-- =====================================================================

CREATE DATABASE IF NOT EXISTS weather_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE weather_db;

-- ---------------------------------------------------------------------
-- Table 1: users
-- Stores registered accounts, passwords, preferences and units
-- ---------------------------------------------------------------------
DROP TABLE IF EXISTS search_history;
DROP TABLE IF EXISTS favorite_cities;
DROP TABLE IF EXISTS users;

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(64) NOT NULL UNIQUE,
    email VARCHAR(120) NOT NULL UNIQUE,
    password_hash VARCHAR(256) NOT NULL,
    full_name VARCHAR(100) NULL,
    preferred_units VARCHAR(10) DEFAULT 'metric' COMMENT 'metric for Celsius, imperial for Fahrenheit',
    default_city VARCHAR(100) DEFAULT 'New York',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_username (username),
    INDEX idx_user_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------
-- Table 2: favorite_cities
-- Stores bookmarked locations for quick weather monitoring
-- ---------------------------------------------------------------------
CREATE TABLE favorite_cities (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    city_name VARCHAR(100) NOT NULL,
    country_code VARCHAR(10) NULL,
    latitude DECIMAL(10, 7) NULL,
    longitude DECIMAL(10, 7) NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_fav_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT uq_user_city UNIQUE (user_id, city_name),
    INDEX idx_fav_user (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------
-- Table 3: search_history
-- Records weather search queries and historic snapshots
-- ---------------------------------------------------------------------
CREATE TABLE search_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    query_text VARCHAR(100) NOT NULL,
    temperature DECIMAL(5, 2) NULL,
    weather_condition VARCHAR(100) NULL,
    icon VARCHAR(20) NULL,
    searched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_history_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE ON UPDATE CASCADE,
    INDEX idx_history_user (user_id),
    INDEX idx_history_date (searched_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================================
-- Sample Seed Data for Testing & Verification
-- Note: Default password is 'Admin@123' (hashed using bcrypt)
-- =====================================================================
INSERT INTO users (username, email, password_hash, full_name, preferred_units, default_city)
VALUES (
    'admin',
    'admin@weathercloud.com',
    '$2b$12$q7r2Y9kC1eUu7n4vR4yN6.T2k8yI7Z4hP8a6p0Vz4u9g6qE2m8xW.', -- sample bcrypt hash
    'System Administrator',
    'metric',
    'London'
);

INSERT INTO favorite_cities (user_id, city_name, country_code, latitude, longitude)
VALUES 
    (1, 'London', 'GB', 51.5074, -0.1278),
    (1, 'Tokyo', 'JP', 35.6762, 139.6503),
    (1, 'New York', 'US', 40.7128, -74.0060);

INSERT INTO search_history (user_id, query_text, temperature, weather_condition, icon)
VALUES 
    (1, 'London', 15.5, 'Scattered Clouds', '03d'),
    (1, 'Tokyo', 22.0, 'Clear Sky', '01d'),
    (1, 'Paris', 18.2, 'Light Rain', '10d');
