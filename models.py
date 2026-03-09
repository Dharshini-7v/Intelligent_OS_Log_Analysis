"""Data models for the Intelligent OS Log Analysis System."""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

class LogEntry(BaseModel):
    """Model for a parsed log entry."""
    log_id: Optional[int] = None
    timestamp: datetime
    service: str
    log_level: str
    message: str
    template_id: Optional[int] = None
    ip_address: Optional[str] = None
    username: Optional[str] = None
    created_at: Optional[datetime] = None

class LogTemplate(BaseModel):
    """Model for a log template."""
    template_id: Optional[int] = None
    template_text: str
    occurrence_count: int = 1

class Alert(BaseModel):
    """Model for a system alert."""
    alert_id: Optional[int] = None
    log_id: int
    alert_type: str
    severity: str
    description: str
    created_at: Optional[datetime] = None

class SystemHealth(BaseModel):
    """Model for system health score."""
    health_score: float
    total_logs: int
    successful_logs: int
    critical_logs: int
