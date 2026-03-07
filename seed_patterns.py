#!/usr/bin/env python3
"""
Seed sample patterns into the patterns table.
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timedelta

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    import aiomysql
    import asyncio
    from intelligent_log_analysis.utils.config import ConfigManager
except ImportError as e:
    print(f"❌ Error: {e}")
    sys.exit(1)


async def seed_patterns():
    """Insert sample patterns into the database."""
    
    print("\n" + "=" * 80)
    print("📊 INSERTING SAMPLE PATTERNS INTO DATABASE")
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
        
        # Sample patterns to insert
        patterns = [
            {
                "pattern_id": "PAT_001",
                "pattern_type": "sequential",
                "sequence": json.dumps(["login_attempt", "permission_denied", "login_attempt"]),
                "frequency": 45,
                "confidence": 0.92,
                "is_anomalous": False
            },
            {
                "pattern_id": "PAT_002",
                "pattern_type": "sequential",
                "sequence": json.dumps(["error_memory_low", "process_killed", "system_restart"]),
                "frequency": 12,
                "confidence": 0.87,
                "is_anomalous": False
            },
            {
                "pattern_id": "PAT_003",
                "pattern_type": "frequency",
                "sequence": json.dumps(["authentication_failure"]),
                "frequency": 128,
                "confidence": 0.95,
                "is_anomalous": True
            },
            {
                "pattern_id": "PAT_004",
                "pattern_type": "sequential",
                "sequence": json.dumps(["file_accessed", "file_modified", "file_deleted"]),
                "frequency": 8,
                "confidence": 0.78,
                "is_anomalous": False
            },
            {
                "pattern_id": "PAT_005",
                "pattern_type": "frequency",
                "sequence": json.dumps(["timeout_error"]),
                "frequency": 267,
                "confidence": 0.88,
                "is_anomalous": True
            },
            {
                "pattern_id": "PAT_006",
                "pattern_type": "sequential",
                "sequence": json.dumps(["request_sent", "connection_timeout", "retry_attempt"]),
                "frequency": 34,
                "confidence": 0.85,
                "is_anomalous": False
            },
            {
                "pattern_id": "PAT_007",
                "pattern_type": "frequency",
                "sequence": json.dumps(["critical_system_error"]),
                "frequency": 5,
                "confidence": 0.99,
                "is_anomalous": True
            },
            {
                "pattern_id": "PAT_008",
                "pattern_type": "sequential",
                "sequence": json.dumps(["service_start", "initialization", "service_ready"]),
                "frequency": 23,
                "confidence": 0.91,
                "is_anomalous": False
            }
        ]
        
        print("Inserting patterns...\n")
        
        inserted_count = 0
        for pattern in patterns:
            try:
                # Check if pattern already exists
                await cursor.execute(
                    "SELECT id FROM patterns WHERE pattern_id = %s",
                    (pattern["pattern_id"],)
                )
                existing = await cursor.fetchone()
                
                if existing:
                    print(f"⏭️  Pattern '{pattern['pattern_id']}' already exists (skipping)")
                else:
                    # Insert pattern
                    await cursor.execute(
                        """
                        INSERT INTO patterns 
                        (pattern_id, pattern_type, sequence, frequency, confidence, is_anomalous, first_detected, last_detected)
                        VALUES (%s, %s, %s, %s, %s, %s, NOW(), NOW())
                        """,
                        (
                            pattern["pattern_id"],
                            pattern["pattern_type"],
                            pattern["sequence"],
                            pattern["frequency"],
                            pattern["confidence"],
                            pattern["is_anomalous"]
                        )
                    )
                    anomalous_badge = "⚠️ ANOMALOUS" if pattern["is_anomalous"] else "✅ NORMAL"
                    print(f"✅ Created: {pattern['pattern_id']:15} | Type: {pattern['pattern_type']:12} | Freq: {pattern['frequency']:3} | Conf: {pattern['confidence']:.2f} | {anomalous_badge}")
                    inserted_count += 1
            
            except Exception as e:
                print(f"❌ Error inserting pattern '{pattern['pattern_id']}': {e}")
        
        # Commit changes
        await conn.commit()
        
        print("\n" + "=" * 80)
        
        # Show all patterns
        await cursor.execute("""
            SELECT pattern_id, pattern_type, frequency, confidence, is_anomalous, first_detected 
            FROM patterns 
            ORDER BY first_detected DESC
        """)
        records = await cursor.fetchall()
        
        if records:
            print(f"\n📋 All Patterns in Database ({len(records)} total):\n")
            print(f"{'Pattern ID':<15} | {'Type':<12} | {'Freq':<5} | {'Conf':<6} | {'Status':<12} | {'Detected'}")
            print("-" * 100)
            for record in records:
                pattern_id, pattern_type, frequency, confidence, is_anomalous, first_detected = record
                status = "⚠️ ANOMALOUS" if is_anomalous else "✅ NORMAL"
                print(f"{pattern_id:<15} | {pattern_type:<12} | {frequency:<5} | {confidence:<6.2f} | {status:<12} | {first_detected}")
        
        print("\n" + "=" * 80)
        print(f"✅ Successfully inserted {inserted_count} patterns!")
        print("=" * 80 + "\n")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        await conn.rollback()
    finally:
        await cursor.close()
        conn.close()


if __name__ == "__main__":
    asyncio.run(seed_patterns())
