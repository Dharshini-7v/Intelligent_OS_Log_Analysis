"""Main entry point for the Intelligent Log Analysis System."""

import asyncio
import signal
import sys
import uvicorn
from pathlib import Path
from typing import Optional

from .utils.config import ConfigManager
from .utils.logging import setup_logging, get_logger


class IntelligentLogAnalysisSystem:
    """Main system orchestrator."""
    
    def __init__(self, config_path: Optional[str] = None):
        # Initialize configuration
        default_config = Path(__file__).parent.parent / "config" / "default.yaml"
        self.config = ConfigManager(config_path or default_config)
        
        # Setup logging
        log_level = self.config.get("system.log_level", "INFO")
        log_file = self.config.get("system.log_file")
        setup_logging(level=log_level, log_file=log_file)
        
        self.logger = get_logger("main")
        self.logger.info("Intelligent Log Analysis System initializing...")
        
        # System components (will be initialized in later tasks)
        self.collector = None
        self.parser = None
        self.pattern_detector = None
        self.ml_engine = None
        self.anomaly_detector = None
        self.alert_system = None
        self.web_server = None
        
        # Control flags
        self.running = False
        self.shutdown_event = asyncio.Event()
    
    async def start(self, web_mode: bool = True, port: int = 8000) -> None:
        """Start the log analysis system."""
        self.logger.info("Starting Intelligent Log Analysis System...")
        self.running = True
        
        try:
            # Initialize components
            await self._initialize_components()
            
            if web_mode:
                # Start web interface
                await self._start_web_interface(port)
            else:
                # Start main processing loop (CLI mode)
                await self._run_main_loop()
            
        except Exception as e:
            self.logger.error(f"Error starting system: {e}")
            raise
    
    async def stop(self) -> None:
        """Stop the log analysis system gracefully."""
        self.logger.info("Stopping Intelligent Log Analysis System...")
        self.running = False
        self.shutdown_event.set()
        
        # Cleanup components
        await self._cleanup_components()
        
        self.logger.info("System stopped successfully")
    
    async def _start_web_interface(self, port: int) -> None:
        """Start the web interface."""
        self.logger.info(f"Starting web interface on port {port}...")
        
        try:
            from .web.app import app
            
            # Configure uvicorn
            config = uvicorn.Config(
                app=app,
                host="0.0.0.0",
                port=port,
                log_level="info",
                access_log=True
            )
            
            # Start server
            server = uvicorn.Server(config)
            await server.serve()
            
        except OSError as e:
            if "address already in use" in str(e).lower() or "10048" in str(e):
                self.logger.error(f"Port {port} is already in use!")
                print(f"\n❌ Port {port} is already in use!")
                print("\n💡 Solutions:")
                print("1. Stop the other application using the port")
                print(f"2. Or run on a different port: python -m intelligent_log_analysis.main --port {port + 1}")
                print("3. Or find and kill the process using the port")
                raise
            else:
                raise
        except ImportError as e:
            self.logger.error(f"Web interface dependencies missing: {e}")
            self.logger.info("Install with: pip install fastapi uvicorn PyJWT python-multipart jinja2")
            raise
        except Exception as e:
            self.logger.error(f"Error starting web interface: {e}")
            raise
    
    async def _initialize_components(self) -> None:
        """Initialize all system components."""
        self.logger.info("Initializing system components...")
        
        try:
            # Initialize database first
            from .storage.database import initialize_database
            await initialize_database(self.config.get_all_config())
            self.logger.info("Database initialized successfully")
            
            # Initialize core components
            from .core.collector import LogCollector
            from .core.parser import LogParser
            from .core.pattern_detector import PatternDetector
            
            # Create instances with configuration
            self.collector = LogCollector(self.config)
            self.parser = LogParser(self.config)
            self.pattern_detector = PatternDetector(self.config)
            
            self.logger.info("Core components initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Error initializing components: {e}")
            # Continue with basic functionality even if some components fail
            self.logger.warning("Some components failed to initialize, continuing with basic functionality")
    
    async def _cleanup_components(self) -> None:
        """Cleanup all system components."""
        self.logger.info("Cleaning up system components...")
        
        # Cleanup database connections
        try:
            from .storage.database import close_database
            await close_database()
            self.logger.info("Database connections closed")
        except Exception as e:
            self.logger.error(f"Error closing database: {e}")
        
        # Cleanup components if they exist
        if self.collector:
            try:
                await self.collector.stop()
            except Exception as e:
                self.logger.error(f"Error stopping collector: {e}")
        
        if self.parser:
            try:
                # Parser cleanup if needed
                pass
            except Exception as e:
                self.logger.error(f"Error stopping parser: {e}")
        
        self.logger.info("Components cleaned up successfully")
    
    async def _run_main_loop(self) -> None:
        """Main processing loop for CLI mode."""
        self.logger.info("Starting main processing loop...")
        
        while self.running:
            try:
                # Basic processing logic
                if self.collector and self.parser:
                    # Process logs if components are available
                    pass
                
                await asyncio.sleep(1)
                
                # Check for shutdown
                if self.shutdown_event.is_set():
                    break
                    
            except Exception as e:
                self.logger.error(f"Error in main loop: {e}")
                await asyncio.sleep(5)  # Brief pause before retry
    
    def _setup_signal_handlers(self) -> None:
        """Setup signal handlers for graceful shutdown."""
        def signal_handler(signum, frame):
            self.logger.info(f"Received signal {signum}, initiating shutdown...")
            asyncio.create_task(self.stop())
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)


async def main() -> None:
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Intelligent Log Analysis System")
    parser.add_argument(
        "--config", 
        type=str, 
        help="Path to configuration file"
    )
    parser.add_argument(
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Override log level"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Web interface port (default: 8000)"
    )
    parser.add_argument(
        "--cli",
        action="store_true",
        help="Run in CLI mode (no web interface)"
    )
    
    args = parser.parse_args()
    
    # Create and start system
    system = IntelligentLogAnalysisSystem(config_path=args.config)
    
    # Override log level if specified
    if args.log_level:
        system.config.set("system.log_level", args.log_level)
    
    # Setup signal handlers
    system._setup_signal_handlers()
    
    # Print startup information
    print("=" * 60)
    print("🧠 INTELLIGENT OS LOG ANALYSIS SYSTEM")
    print("=" * 60)
    print()
    print("📋 Project: OS Log Analysis & Prediction using ML, DBMS, and Pattern Algorithms")
    print()
    
    if not args.cli:
        print("🔐 Demo Login Accounts:")
        print("   • admin / admin123 (Administrator)")
        print("   • analyst / analyst123 (Log Analyst)")
        print("   • demo / demo (Viewer)")
        print()
        print(f"🌐 Web Interface: http://localhost:{args.port}")
        print("📝 Create new accounts via the registration page")
    else:
        print("🖥️  Running in CLI mode")
    
    print("=" * 60)
    print()
    
    try:
        await system.start(web_mode=not args.cli, port=args.port)
    except KeyboardInterrupt:
        await system.stop()
    except Exception as e:
        system.logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())