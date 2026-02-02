#!/usr/bin/env python3
"""
Main launcher for the Intelligent Log Analysis System.

This script launches the complete web-based application with:
- User authentication and registration
- Real-time log processing and monitoring
- Pattern detection and analysis
- Anomaly detection with alerts
- ML-based predictions
- Interactive dashboard
- User management (admin)

This is the main entry point for the project.
"""

import sys
import uvicorn
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def main():
    """Run the intelligent log analysis web application."""
    print("=" * 60)
    print("🧠 INTELLIGENT OS LOG ANALYSIS SYSTEM")
    print("=" * 60)
    print()
    print("📋 Project Overview:")
    print("   • Intelligent OS Log Analysis and Prediction")
    print("   • Using ML, DBMS, and Pattern Algorithms")
    print("   • Real-time log processing and anomaly detection")
    print("   • Web-based dashboard with authentication")
    print()
    print("🔐 Demo Login Accounts:")
    print("   • admin / admin123 (Administrator)")
    print("   • analyst / analyst123 (Log Analyst)")
    print("   • demo / demo (Viewer)")
    print()
    print("🌐 Access the application at: http://localhost:8000")
    print("📝 Create new accounts via the registration page")
    print("=" * 60)
    print()
    
    try:
        from intelligent_log_analysis.web.app import app
        
        # Run the FastAPI application on the standard port
        uvicorn.run(
            app, 
            host="0.0.0.0", 
            port=8000,
            log_level="info"
        )
    except OSError as e:
        if "address already in use" in str(e).lower() or "10048" in str(e):
            print("❌ Port 8000 is already in use!")
            print()
            print("💡 Solutions:")
            print("1. Stop the other application using port 8000")
            print("2. Or run on a different port:")
            print("   python -m intelligent_log_analysis.main --port 8001")
            print()
            sys.exit(1)
        else:
            raise
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure all dependencies are installed:")
        print("pip install fastapi uvicorn PyJWT python-multipart jinja2 watchdog pydantic pyyaml")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error starting application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 Application stopped. Thanks for using the Intelligent Log Analysis System!")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)