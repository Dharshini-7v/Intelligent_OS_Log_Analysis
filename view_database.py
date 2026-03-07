#!/usr/bin/env python3
"""
Database Viewer - View all database content and structure.
This script displays the database schema and data in a formatted way.
"""

import sys
from pathlib import Path
from datetime import datetime

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    import aiomysql
    import asyncio
    from intelligent_log_analysis.utils.config import ConfigManager
except ImportError as e:
    print(f"❌ Error: {e}")
    print("Make sure all dependencies are installed")
    sys.exit(1)


async def view_database():
    """View all database tables and their content."""
    
    print("\n" + "=" * 80)
    print("📊 INTELLIGENT LOG ANALYSIS SYSTEM - DATABASE VIEWER")
    print("=" * 80 + "\n")
    
    # Load configuration
    config_path = project_root / "config" / "default.yaml"
    config_manager = ConfigManager(config_path)
    db_config = config_manager.get_all_config().get("database", {}).get("mysql", {})
    
    # Connect to database
    try:
        conn = await aiomysql.connect(
            host=db_config.get("host", "localhost"),
            port=db_config.get("port", 3306),
            user=db_config.get("username", "log_analyzer"),
            password=db_config.get("password", ""),
            db=db_config.get("database", "intelligent_log_analysis")
        )
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return
    
    try:
        cursor = await conn.cursor()
        
        # Get all table names
        await cursor.execute(
            "SELECT TABLE_NAME FROM information_schema.TABLES WHERE TABLE_SCHEMA = %s",
            (db_config.get("database"),)
        )
        tables = await cursor.fetchall()
        
        print(f"📋 Database: {db_config.get('database')}")
        print(f"👤 User: {db_config.get('username')}")
        print(f"🕐 Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        if not tables:
            print("❌ No tables found in the database!")
            return
        
        print(f"✅ Found {len(tables)} tables:\n")
        
        # Display each table
        for table_name in tables:
            table_name = table_name[0]
            
            # Get table structure
            await cursor.execute(f"DESCRIBE {table_name}")
            columns = await cursor.fetchall()
            
            # Get row count
            await cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            row_count = (await cursor.fetchone())[0]
            
            print(f"\n{'─' * 80}")
            print(f"📄 TABLE: {table_name}")
            print(f"{'─' * 80}")
            print(f"   Rows: {row_count}")
            print(f"\n   Columns:")
            for col in columns:
                col_name, col_type, null, key, default, extra = col
                print(f"      • {col_name:30} | {col_type:20} | Key: {key}")
            
            # Get sample data if table has rows
            if row_count > 0:
                print(f"\n   Sample Data ({min(5, row_count)} rows shown):")
                await cursor.execute(f"SELECT * FROM {table_name} LIMIT 5")
                rows = await cursor.fetchall()
                
                if rows:
                    # Print header
                    col_names = [col[0] for col in columns]
                    print(f"      {' | '.join(col_names)}")
                    print(f"      {'-' * 78}")
                    
                    # Print data
                    for row in rows:
                        row_str = " | ".join(str(val)[:20] for val in row)
                        print(f"      {row_str}")
            else:
                print(f"\n   💾 Table is empty (no data yet)")
        
        print(f"\n{'=' * 80}")
        print("✅ Database view complete!")
        print("=" * 80 + "\n")
        
    except Exception as e:
        print(f"❌ Error viewing database: {e}")
    finally:
        await cursor.close()
        conn.close()


if __name__ == "__main__":
    asyncio.run(view_database())
