"""Anomaly detection for critical system errors."""

import logging
from typing import Optional
from models import LogEntry, Alert

logger = logging.getLogger("anomaly_detector")

class AnomalyDetector:
    """Detects critical system anomalies and generates alerts."""
    
    def __init__(self):
        # Critical keywords and patterns
        self.critical_keywords = ["ERROR", "FAILED", "CRASH", "FATAL", "CRITICAL", "PANIC"]
        self.failed_login_patterns = ["Failed password", "authentication failure", "Login failed"]
        
    def check_for_anomaly(self, log: LogEntry) -> Optional[Alert]:
        """Check if a log entry represents a critical anomaly."""
        message_upper = log.message.upper()
        
        # Check for failed login attempts
        if any(pattern.upper() in message_upper for pattern in self.failed_login_patterns):
            return Alert(
                log_id=log.log_id or 0,
                alert_type="Security: Failed Login",
                severity="HIGH",
                description=f"Security alert: Detected failed login attempt from {log.ip_address or 'unknown source'} for user {log.username or 'unknown'}"
            )
        
        # Check for system crashes
        if "CRASH" in message_upper or "PANIC" in message_upper:
            return Alert(
                log_id=log.log_id or 0,
                alert_type="System: Crash",
                severity="CRITICAL",
                description=f"Critical alert: System crash detected in service {log.service}"
            )
        
        # Check for general critical errors
        if log.log_level in ["ERROR", "CRITICAL"]:
            return Alert(
                log_id=log.log_id or 0,
                alert_type="System: Critical Error",
                severity="MEDIUM",
                description=f"Error alert: Detected critical error in service {log.service}: {log.message}"
            )
            
        return None
