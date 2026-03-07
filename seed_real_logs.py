#!/usr/bin/env python3
"""
Collect real OS logs from Windows system and insert into database.
This script reads actual Windows Event Logs and stores them in the database.
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
import subprocess

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    import aiomysql
    import asyncio
    from intelligent_log_analysis.utils.config import ConfigManager
except ImportError as e:
    print(f"❌ Error: {e}")
    sys.exit(1)


def get_windows_event_logs():
    """Collect Windows Event Logs using PowerShell."""
    
    print("\n🔍 Collecting Windows Event Logs...\n")
    
    # PowerShell command to get recent event logs
    ps_command = """
    $logs = Get-EventLog -LogName System -Newest 50 | Select-Object TimeGenerated, Source, EventID, Message, EntryType
    if ($logs -is [array]) { $logs | ConvertTo-Json } else { @($logs) | ConvertTo-Json }
    """
    
    try:
        result = subprocess.run(
            ["powershell", "-Command", ps_command],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            return json.loads(result.stdout)
        else:
            print(f"⚠️  Error getting logs: {result.stderr}")
            return []
    except Exception as e:
        print(f"❌ Error: {e}")
        return []


def get_application_event_logs():
    """Collect Application Event Logs."""
    
    print("🔍 Collecting Application Event Logs...\n")
    
    ps_command = """
    $logs = Get-EventLog -LogName Application -Newest 50 | Select-Object TimeGenerated, Source, EventID, Message, EntryType
    if ($logs -is [array]) { $logs | ConvertTo-Json } else { @($logs) | ConvertTo-Json }
    """
    
    try:
        result = subprocess.run(
            ["powershell", "-Command", ps_command],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            return json.loads(result.stdout)
        else:
            print(f"⚠️  Error getting logs: {result.stderr}")
            return []
    except Exception as e:
        print(f"❌ Error: {e}")
        return []


async def insert_logs_to_database(logs_data, log_type="System"):
    """Insert collected logs into the log_templates table."""
    
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
        return 0
    
    try:
        cursor = await conn.cursor()
        
        inserted_count = 0
        
        for idx, log_entry in enumerate(logs_data):
            try:
                # Extract log information
                timestamp = log_entry.get("TimeGenerated", datetime.now().isoformat())
                source = log_entry.get("Source", "Unknown")
                event_id = log_entry.get("EventID", 0)
                message = log_entry.get("Message", "")[:500]  # Truncate long messages
                entry_type = log_entry.get("EntryType", "Information")
                
                # Create template ID
                template_id = f"REAL_{log_type}_{event_id}_{idx}"
                
                # Check if this template already exists
                await cursor.execute(
                    "SELECT id FROM log_templates WHERE template_id = %s",
                    (template_id,)
                )
                existing = await cursor.fetchone()
                
                if not existing:
                    # Insert log template
                    await cursor.execute(
                        """
                        INSERT INTO log_templates 
                        (template_id, template_text, parameter_count, frequency, log_level, source_pattern)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        """,
                        (
                            template_id,
                            message,
                            0,
                            1,
                            entry_type,
                            source
                        )
                    )
                    inserted_count += 1
                    print(f"✅ [{log_type}] {source:20} | ID: {event_id:5} | Type: {entry_type:15} | Msg: {message[:40]}")
            
            except Exception as e:
                print(f"⚠️  Error inserting log entry: {e}")
                continue
        
        # Commit changes
        await conn.commit()
        
        print(f"\n✅ Inserted {inserted_count} real {log_type} logs from Windows Event Log")
        
        return inserted_count
        
    except Exception as e:
        print(f"❌ Error: {e}")
        await conn.rollback()
        return 0
    finally:
        await cursor.close()
        conn.close()


async def show_log_statistics():
    """Show statistics of logs in database."""
    
    config_path = project_root / "config" / "default.yaml"
    config_manager = ConfigManager(config_path)
    db_config = config_manager.get_all_config().get("database", {}).get("mysql", {})
    
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
        
        print("\n" + "=" * 80)
        print("📊 LOG STATISTICS IN DATABASE")
        print("=" * 80 + "\n")
        
        # Get log count by type
        await cursor.execute("""
            SELECT log_level, COUNT(*) as count
            FROM log_templates
            GROUP BY log_level
            ORDER BY count DESC
        """)
        
        results = await cursor.fetchall()
        if results:
            print("Log Count by Level:")
            for log_level, count in results:
                print(f"  {log_level:20} : {count:5} logs")
        
        # Get total logs
        await cursor.execute("SELECT COUNT(*) FROM log_templates")
        total = (await cursor.fetchone())[0]
        
        print(f"\n  {'TOTAL':20} : {total:5} logs")
        
        # Get sources
        await cursor.execute("""
            SELECT source_pattern, COUNT(*) as count
            FROM log_templates
            WHERE source_pattern IS NOT NULL
            GROUP BY source_pattern
            ORDER BY count DESC
            LIMIT 10
        """)
        
        results = await cursor.fetchall()
        if results:
            print("\nTop Log Sources:")
            for source, count in results:
                print(f"  {source:30} : {count:5} logs")
        
        print("\n" + "=" * 80 + "\n")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await cursor.close()
        conn.close()


async def main():
    """Main function."""
    
    print("=" * 80)
    print("🖥️  REAL OS LOG DATA INSERTION - WINDOWS EVENT LOGS")
    print("=" * 80)
    
    # Collect logs
    system_logs = get_windows_event_logs()
    app_logs = get_application_event_logs()
    
    if not system_logs and not app_logs:
        print("\n❌ No logs collected. Make sure you have admin access to Event Logs.")
        return
    
    # Insert into database
    total_inserted = 0
    
    if system_logs:
        print("\n" + "-" * 80)
        print("📝 Inserting System Logs...")
        print("-" * 80 + "\n")
        count = await insert_logs_to_database(system_logs, "System")
        total_inserted += count
    
    if app_logs:
        print("\n" + "-" * 80)
        print("📝 Inserting Application Logs...")
        print("-" * 80 + "\n")
        count = await insert_logs_to_database(app_logs, "Application")
        total_inserted += count
    
    # Show statistics
    await show_log_statistics()
    
    print("=" * 80)
    print(f"✅ Total {total_inserted} real OS logs inserted into database!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
