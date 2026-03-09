"""Log collection and real-time file system monitoring using Watchdog."""

import os
import time
import logging
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Callable, Set
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

logger = logging.getLogger("collector")

class LogFileHandler(FileSystemEventHandler):
    """File system event handler to detect log file modifications."""
    
    def __init__(self, collector: 'LogCollector'):
        self.collector = collector
        super().__init__()
    
    def on_modified(self, event):
        """Handle file modification events."""
        if not event.is_directory:
            # Run the processing in the main event loop
            self.collector.on_file_changed(event.src_path)

class LogCollector:
    """Monitors OS log files and collects new entries in real-time."""
    
    def __init__(self, log_paths: List[str], log_callback: Callable[[str, str], None], loop=None):
        self.log_paths = log_paths
        self.log_callback = log_callback
        self.loop = loop
        self.monitored_files: Dict[str, int] = {}  # path: last_position
        self.observer = Observer()
        self.running = False
        
    def start(self):
        """Start monitoring log files."""
        logger.info(f"Starting Log Collector monitoring {len(self.log_paths)} paths...")
        self.running = True
        
        # Initialize positions and start watching directories
        monitored_dirs: Set[str] = set()
        
        for path_str in self.log_paths:
            path = Path(path_str)
            if path.is_file():
                self.monitored_files[str(path)] = path.stat().st_size
                monitored_dirs.add(str(path.parent))
            elif path.is_dir():
                monitored_dirs.add(str(path))
                # Add existing logs in directory
                for log_file in path.glob("*.log"):
                    self.monitored_files[str(log_file)] = log_file.stat().st_size
        
        # Start watching all unique parent directories
        event_handler = LogFileHandler(self)
        for dir_path in monitored_dirs:
            if os.path.exists(dir_path):
                self.observer.schedule(event_handler, dir_path, recursive=False)
                logger.info(f"Monitoring directory: {dir_path}")
        
        self.observer.start()
        logger.info("Log Collector started successfully")
    
    def stop(self):
        """Stop monitoring."""
        self.running = False
        self.observer.stop()
        self.observer.join()
        logger.info("Log Collector stopped")
    
    def on_file_changed(self, file_path: str):
        """Read only new lines from the modified file."""
        if not self.running:
            return
            
        path = Path(file_path)
        # Filter files (if needed)
        if not any(path.match(p) or str(path.parent) == p for p in self.log_paths):
            # Check if it's a new .log file in a monitored directory
            if path.suffix != ".log":
                return
        
        try:
            current_size = path.stat().st_size
            last_pos = self.monitored_files.get(file_path, 0)
            
            # If file was truncated, reset position
            if current_size < last_pos:
                last_pos = 0
            
            if current_size > last_pos:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    f.seek(last_pos)
                    # Read new lines
                    while True:
                        line = f.readline()
                        if not line:
                            break
                        
                        line = line.rstrip('\n\r')
                        if line:
                            # Send to callback
                            self.log_callback(line, file_path)
                    
                    # Update position
                    self.monitored_files[file_path] = f.tell()
                    
        except Exception as e:
            logger.error(f"Error reading log file {file_path}: {e}")
