"""Log parsing using the Drain algorithm and regex extraction."""

import re
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from models import LogEntry

logger = logging.getLogger("parser")

class DrainParser:
    """Drain algorithm implementation for log template extraction and field parsing."""
    
    def __init__(self, depth: int = 4, similarity_threshold: float = 0.5):
        self.depth = depth
        self.similarity_threshold = similarity_threshold
        self.templates: Dict[str, str] = {}
        
        # Regex patterns for field extraction
        self.ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
        self.pid_pattern = r'\[(\d+)\]'
        # Syslog format: timestamp hostname service[pid]: message
        self.syslog_pattern = r'^\w{3}\s+\d+\s+\d{2}:\d{2}:\d{2}\s+\S+\s+([^:\[\s]+)(?:\[(\d+)\])?:\s*(.*)$'
        self.timestamp_pattern = r'^(\w{3}\s+\d+\s+\d{2}:\d{2}:\d{2})'
        
    def parse_line(self, line: str, source: str = "system") -> Optional[LogEntry]:
        """Parse a single log line into a LogEntry object."""
        line = line.strip()
        if not line:
            return None
            
        try:
            # 1. Try to parse as standard Syslog
            syslog_match = re.match(self.syslog_pattern, line)
            if syslog_match:
                service = syslog_match.group(1)
                # pid = syslog_match.group(2)
                message = syslog_match.group(3)
                
                timestamp_match = re.search(self.timestamp_pattern, line)
                timestamp_str = timestamp_match.group(1)
                current_year = datetime.now().year
                timestamp = datetime.strptime(f"{current_year} {timestamp_str}", "%Y %b %d %H:%M:%S")
            else:
                # Fallback to basic extraction
                timestamp_match = re.search(self.timestamp_pattern, line)
                timestamp = datetime.now()
                if timestamp_match:
                    timestamp_str = timestamp_match.group(1)
                    current_year = datetime.now().year
                    try:
                        timestamp = datetime.strptime(f"{current_year} {timestamp_str}", "%Y %b %d %H:%M:%S")
                    except: pass
                
                service = "system"
                message = line
            
            # Extract IP address
            ip_match = re.search(self.ip_pattern, line)
            ip_address = ip_match.group(0) if ip_match else None
            
            # Extract username
            username = None
            if "for user" in line:
                username_match = re.search(r'for user (\w+)', line)
                username = username_match.group(1) if username_match else None
            elif "Failed password for" in line:
                username_match = re.search(r'Failed password for (\w+)', line)
                username = username_match.group(1) if username_match else None
            
            # Determine log level
            log_level = "INFO"
            if any(err in line.upper() for err in ["ERROR", "CRITICAL", "FAILED", "FAILURE", "FATAL"]):
                log_level = "ERROR"
            elif any(warn in line.upper() for warn in ["WARNING", "WARN"]):
                log_level = "WARNING"
            
            return LogEntry(
                timestamp=timestamp,
                service=service,
                log_level=log_level,
                message=message,
                ip_address=ip_address,
                username=username
            )
            
        except Exception as e:
            logger.error(f"Error parsing log line: {e}")
            return None
    
    def get_template(self, message: str) -> str:
        """Extract a generic template from the log message using Drain logic."""
        # Preprocess: Replace numbers and common variables with placeholders
        tokens = message.split()
        template_tokens = []
        
        for token in tokens:
            # Replace numbers
            if re.match(r'^\d+$', token):
                template_tokens.append("<NUM>")
            # Replace IP addresses
            elif re.match(self.ip_pattern, token):
                template_tokens.append("<IP>")
            # Replace hex values
            elif re.match(r'^0x[0-9a-fA-F]+$', token):
                template_tokens.append("<HEX>")
            else:
                template_tokens.append(token)
        
        return " ".join(template_tokens)
