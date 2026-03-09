"""Database integration for the Intelligent Log Analysis System."""

import asyncio
import logging
import aiomysql
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from models import LogEntry, LogTemplate, Alert, SystemHealth

logger = logging.getLogger("database")

class DatabaseManager:
    """Manages MySQL database connections and operations."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.pool = None
        
    async def initialize(self) -> None:
        """Initialize database connection pool and create tables."""
        mysql_config = self.config.get("database", {}).get("mysql", {})
        
        # Priority to environment variables for Render deployment
        host = os.getenv("MYSQLHOST", os.getenv("DB_HOST", mysql_config.get("host", "localhost")))
        port = int(os.getenv("MYSQLPORT", os.getenv("DB_PORT", mysql_config.get("port", 3306))))
        user = os.getenv("MYSQLUSER", os.getenv("DB_USER", mysql_config.get("username", "root")))
        password = os.getenv("MYSQLPASSWORD", os.getenv("DB_PASSWORD", mysql_config.get("password", "")))
        db = os.getenv("MYSQLDATABASE", os.getenv("DB_NAME", mysql_config.get("database", "intelligent_log_analysis")))

        try:
            self.pool = await aiomysql.create_pool(
                host=host,
                port=port,
                user=user,
                password=password,
                db=db,
                minsize=1,
                maxsize=mysql_config.get("connection_pool_size", 10),
                autocommit=True
            )
            
            await self._create_tables()
            logger.info("Database initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    async def _create_tables(self) -> None:
        """Create required tables if they don't exist."""
        tables_sql = [
            # Logs table
            """
            CREATE TABLE IF NOT EXISTS logs (
                log_id INT PRIMARY KEY AUTO_INCREMENT,
                timestamp DATETIME NOT NULL,
                service VARCHAR(50),
                log_level VARCHAR(20),
                message TEXT,
                template_id INT,
                ip_address VARCHAR(50),
                username VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            # Templates table
            """
            CREATE TABLE IF NOT EXISTS templates (
                template_id INT PRIMARY KEY AUTO_INCREMENT,
                template_text TEXT NOT NULL,
                occurrence_count INT DEFAULT 1,
                UNIQUE (template_text(255))
            )
            """,
            # Alerts table
            """
            CREATE TABLE IF NOT EXISTS alerts (
                alert_id INT PRIMARY KEY AUTO_INCREMENT,
                log_id INT,
                alert_type VARCHAR(50),
                severity VARCHAR(20),
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (log_id) REFERENCES logs(log_id) ON DELETE CASCADE
            )
            """
        ]
        
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                for sql in tables_sql:
                    await cursor.execute(sql)
    
    async def close(self) -> None:
        """Close database connection pool."""
        if self.pool:
            self.pool.close()
            await self.pool.wait_closed()
    
    async def get_or_create_template(self, template_text: str) -> int:
        """Get template ID or create new template."""
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                # Try to find existing template
                await cursor.execute(
                    "SELECT template_id FROM templates WHERE template_text = %s", 
                    (template_text,)
                )
                row = await cursor.fetchone()
                
                if row:
                    template_id = row[0]
                    # Update occurrence count
                    await cursor.execute(
                        "UPDATE templates SET occurrence_count = occurrence_count + 1 WHERE template_id = %s",
                        (template_id,)
                    )
                    return template_id
                else:
                    # Create new template
                    await cursor.execute(
                        "INSERT INTO templates (template_text, occurrence_count) VALUES (%s, 1)",
                        (template_text,)
                    )
                    return cursor.lastrowid
    
    async def insert_log(self, log: LogEntry) -> int:
        """Insert a log entry into the database."""
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                query = """
                    INSERT INTO logs (timestamp, service, log_level, message, template_id, ip_address, username)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """
                await cursor.execute(query, (
                    log.timestamp, log.service, log.log_level, 
                    log.message, log.template_id, log.ip_address, log.username
                ))
                return cursor.lastrowid
    
    async def insert_alert(self, alert: Alert) -> int:
        """Insert an alert into the database."""
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                query = """
                    INSERT INTO alerts (log_id, alert_type, severity, description)
                    VALUES (%s, %s, %s, %s)
                """
                await cursor.execute(query, (
                    alert.log_id, alert.alert_type, alert.severity, alert.description
                ))
                return cursor.lastrowid
    
    async def get_recent_logs(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent log entries."""
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute(
                    "SELECT * FROM logs ORDER BY timestamp DESC LIMIT %s", 
                    (limit,)
                )
                return await cursor.fetchall()
    
    async def get_recent_alerts(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent alerts."""
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute(
                    "SELECT * FROM alerts ORDER BY created_at DESC LIMIT %s", 
                    (limit,)
                )
                return await cursor.fetchall()
    
    async def get_all_templates(self) -> List[Dict[str, Any]]:
        """Get all log templates/patterns."""
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute(
                    "SELECT * FROM templates ORDER BY occurrence_count DESC"
                )
                return await cursor.fetchall()
    
    async def calculate_health_score(self) -> Dict[str, Any]:
        """Calculate system health score."""
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                # Total logs
                await cursor.execute("SELECT COUNT(*) FROM logs")
                total_logs = (await cursor.fetchone())[0]
                
                if total_logs == 0:
                    return {"health_score": 100.0, "total_logs": 0, "successful_logs": 0, "critical_logs": 0}
                
                # Critical logs (ERROR level)
                await cursor.execute("SELECT COUNT(*) FROM logs WHERE log_level = 'ERROR' OR log_level = 'CRITICAL'")
                critical_logs = (await cursor.fetchone())[0]
                
                successful_logs = total_logs - critical_logs
                health_score = (successful_logs / total_logs) * 100.0
                
                return {
                    "health_score": round(health_score, 2),
                    "total_logs": total_logs,
                    "successful_logs": successful_logs,
                    "critical_logs": critical_logs
                }
