@echo off
REM Database Viewer Script for Windows
REM Shows all tables and their content

setlocal enabledelayedexpansion

set "MYSQL_PATH=C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe"
set "HOST=localhost"
set "USER=log_analyzer"
set "PASSWORD=LogAnalyzer@2026"
set "DATABASE=intelligent_log_analysis"

echo.
echo ================================================================================
echo DATABASE VIEWER - Intelligent Log Analysis System
echo ================================================================================
echo.
echo Database: %DATABASE%
echo User: %USER%
echo Host: %HOST%
echo.

REM Show all tables
echo.
echo ---- ALL TABLES ----
"%MYSQL_PATH%" -h %HOST% -u %USER% -p%PASSWORD% %DATABASE% -e "SHOW TABLES;"

REM Show users table
echo.
echo ---- USERS TABLE ----
"%MYSQL_PATH%" -h %HOST% -u %USER% -p%PASSWORD% %DATABASE% -e "DESCRIBE users; SELECT * FROM users;"

REM Show log_templates table
echo.
echo ---- LOG TEMPLATES TABLE ----
"%MYSQL_PATH%" -h %HOST% -u %USER% -p%PASSWORD% %DATABASE% -e "DESCRIBE log_templates; SELECT COUNT(*) as 'Total Templates' FROM log_templates;"

REM Show patterns table
echo.
echo ---- PATTERNS TABLE ----
"%MYSQL_PATH%" -h %HOST% -u %USER% -p%PASSWORD% %DATABASE% -e "DESCRIBE patterns; SELECT COUNT(*) as 'Total Patterns' FROM patterns;"

REM Show anomalies table
echo.
echo ---- ANOMALIES TABLE ----
"%MYSQL_PATH%" -h %HOST% -u %USER% -p%PASSWORD% %DATABASE% -e "DESCRIBE anomalies; SELECT COUNT(*) as 'Total Anomalies' FROM anomalies;"

REM Show predictions table
echo.
echo ---- PREDICTIONS TABLE ----
"%MYSQL_PATH%" -h %HOST% -u %USER% -p%PASSWORD% %DATABASE% -e "DESCRIBE predictions; SELECT COUNT(*) as 'Total Predictions' FROM predictions;"

REM Show system_metrics table
echo.
echo ---- SYSTEM METRICS TABLE ----
"%MYSQL_PATH%" -h %HOST% -u %USER% -p%PASSWORD% %DATABASE% -e "DESCRIBE system_metrics; SELECT COUNT(*) as 'Total Metrics' FROM system_metrics;"

echo.
echo ================================================================================
echo Database view complete!
echo ================================================================================
