#!/usr/bin/env python3
"""
Seed demo users into the database for testing.
"""

import hashlib
import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    import aiomysql
    import asyncio
    from intelligent_log_analysis.utils.config import ConfigManager
except ImportError as e:
    print(f"❌ Error: {e}")
    sys.exit(1)


def hash_password(password: str) -> str:
    """Hash password using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()


async def seed_demo_users():
    """Insert demo users into the database."""
    
    print("\n" + "=" * 80)
    print("👥 SEEDING DEMO USERS INTO DATABASE")
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
        
        # Demo users to insert
        demo_users = [
            ("admin", hash_password("admin123"), "admin@loganalysis.com", "System Administrator", "administrator"),
            ("analyst", hash_password("analyst123"), "analyst@loganalysis.com", "Log Analyst", "log_analyst"),
            ("demo", hash_password("demo"), "demo@loganalysis.com", "Demo User", "viewer")
        ]
        
        print("Inserting demo users...\n")
        
        for username, password_hash, email, full_name, role in demo_users:
            try:
                # Check if user already exists
                await cursor.execute(
                    "SELECT id FROM users WHERE username = %s",
                    (username,)
                )
                existing = await cursor.fetchone()
                
                if existing:
                    print(f"⏭️  User '{username}' already exists (skipping)")
                else:
                    # Insert user
                    await cursor.execute(
                        """
                        INSERT INTO users (username, password_hash, email, full_name, role, is_active)
                        VALUES (%s, %s, %s, %s, %s, 1)
                        """,
                        (username, password_hash, email, full_name, role)
                    )
                    print(f"✅ Created user: {username:15} | Role: {role:15} | Email: {email}")
            
            except Exception as e:
                print(f"❌ Error creating user '{username}': {e}")
        
        # Commit changes
        await conn.commit()
        
        print("\n" + "=" * 80)
        
        # Show all users
        await cursor.execute("SELECT username, email, role, created_at FROM users ORDER BY created_at")
        users = await cursor.fetchall()
        
        if users:
            print(f"\n📋 All Users in Database ({len(users)} total):\n")
            print(f"{'Username':<20} | {'Email':<30} | {'Role':<20} | {'Created'}")
            print("-" * 90)
            for user in users:
                username, email, role, created_at = user
                print(f"{username:<20} | {email:<30} | {role:<20} | {created_at}")
        
        print("\n" + "=" * 80)
        print("✅ Demo users seeded successfully!")
        print("\n🔐 You can now log in with:")
        print("   • admin / admin123 (Administrator)")
        print("   • analyst / analyst123 (Log Analyst)")
        print("   • demo / demo (Viewer)")
        print("=" * 80 + "\n")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        await conn.rollback()
    finally:
        await cursor.close()
        conn.close()


if __name__ == "__main__":
    asyncio.run(seed_demo_users())
