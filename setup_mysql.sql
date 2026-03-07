-- Create the database
CREATE DATABASE IF NOT EXISTS intelligent_log_analysis;

-- Create the user for the application
CREATE USER IF NOT EXISTS 'log_analyzer'@'localhost' IDENTIFIED BY 'LogAnalyzer@2026';

-- Grant all privileges
GRANT ALL PRIVILEGES ON intelligent_log_analysis.* TO 'log_analyzer'@'localhost';

-- Flush privileges to apply changes
FLUSH PRIVILEGES;

-- Verify
SHOW GRANTS FOR 'log_analyzer'@'localhost';
