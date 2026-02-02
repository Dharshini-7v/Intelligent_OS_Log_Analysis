#!/usr/bin/env python3
"""
Database setup script for the Intelligent Log Analysis System.
This script helps you set up PostgreSQL and InfluxDB for the project.
"""

import asyncio
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from intelligent_log_analysis.utils.config import ConfigManager
from intelligent_log_analysis.storage.database import DatabaseManager


async def setup_database():
    """Set up the database connections and tables."""
    print("🗄️  Setting up Intelligent Log Analysis Database")
    print("=" * 50)
    
    # Load configuration
    config_path = project_root / "config" / "default.yaml"
    config_manager = ConfigManager(config_path)
    
    # Create database manager
    db_manager = DatabaseManager(config_manager.get_all_config())
    
    try:
        # Initialize database connections
        print("📡 Initializing database connections...")
        await db_manager.initialize()
        
        print("✅ Database setup completed successfully!")
        print()
        print("📋 Database Status:")
        
        # Check PostgreSQL
        if db_manager.pg_pool:
            print("  ✅ PostgreSQL: Connected")
            print("     - Tables created/verified")
            print("     - Ready for user data, patterns, anomalies, predictions")
        elif db_manager.mysql_pool:
            print("  ✅ MySQL: Connected")
            print("     - Tables created/verified")
            print("     - Ready for user data, patterns, anomalies, predictions")
        else:
            print("  ❌ Relational Database: Not connected")
            print("     - Check PostgreSQL or MySQL configuration in config/default.yaml")
            print("     - Ensure PostgreSQL or MySQL is running")
        
        # Check InfluxDB
        if db_manager.influx_client:
            print("  ✅ InfluxDB: Connected")
            print("     - Ready for time-series log data")
        else:
            print("  ❌ InfluxDB: Not connected")
            print("     - Check configuration in config/default.yaml")
            print("     - Ensure InfluxDB is running")
        
        print()
        print("🚀 You can now run the application:")
        print("   python run_demo.py")
        
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        print()
        print("💡 Troubleshooting:")
        print("1. Check if PostgreSQL is running:")
        print("   - Windows: Check Services or run 'pg_ctl status'")
        print("   - Linux/Mac: 'sudo systemctl status postgresql'")
        print()
        print("2. Check if InfluxDB is running:")
        print("   - Visit http://localhost:8086 in your browser")
        print("   - Or run 'influx ping'")
        print()
        print("3. Verify database configuration in config/default.yaml")
        print("4. Install missing dependencies:")
        print("   pip install asyncpg aiomysql influxdb-client")
        
    finally:
        # Close connections
        await db_manager.close()


def print_database_info():
    """Print database configuration information."""
    print("📊 Database Configuration Guide")
    print("=" * 50)
    print()
    
    print("🐘 PostgreSQL Setup:")
    print("1. Install PostgreSQL")
    print("2. Create database:")
    print("   CREATE DATABASE intelligent_log_analysis;")
    print("   CREATE USER log_analyzer WITH PASSWORD 'your_password';")
    print("   GRANT ALL PRIVILEGES ON DATABASE intelligent_log_analysis TO log_analyzer;")
    print()
    
    print("🐬 MySQL Setup (Alternative to PostgreSQL):")
    print("1. Install MySQL")
    print("2. Create database:")
    print("   CREATE DATABASE intelligent_log_analysis;")
    print("   CREATE USER 'log_analyzer'@'localhost' IDENTIFIED BY 'your_password';")
    print("   GRANT ALL PRIVILEGES ON intelligent_log_analysis.* TO 'log_analyzer'@'localhost';")
    print("   FLUSH PRIVILEGES;")
    print()
    
    print("📈 InfluxDB Setup:")
    print("1. Install InfluxDB 2.x")
    print("2. Create organization and bucket:")
    print("   influx org create -n intelligent-log-analysis")
    print("   influx bucket create -n logs -o intelligent-log-analysis")
    print("3. Generate token and update config/default.yaml")
    print()
    
    print("⚙️  Configuration File: config/default.yaml")
    print("Update the database section with your credentials:")
    print("""
database:
  # PostgreSQL (preferred)
  postgresql:
    host: "localhost"
    port: 5432
    database: "intelligent_log_analysis"
    username: "log_analyzer"
    password: "your_password"
    
  # MySQL (alternative to PostgreSQL)
  mysql:
    host: "localhost"
    port: 3306
    database: "intelligent_log_analysis"
    username: "log_analyzer"
    password: "your_password"
    
  # InfluxDB (time-series data)
  influxdb:
    url: "http://localhost:8086"
    token: "your_influxdb_token"
    org: "intelligent-log-analysis"
    bucket: "logs"
""")


async def main():
    """Main function."""
    if len(sys.argv) > 1 and sys.argv[1] == "--info":
        print_database_info()
        return
    
    try:
        await setup_database()
    except KeyboardInterrupt:
        print("\n🛑 Setup cancelled by user")
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    print("Use --info flag to see database configuration guide")
    print()
    asyncio.run(main())