"""Log-related data models."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field, validator


class LogLevel(str, Enum):
    """Log severity levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogSource(BaseModel):
    """Configuration for a log source."""
    path: str = Field(..., description="Path to log file or directory")
    format: str = Field(default="auto", description="Log format (auto, syslog, json, etc.)")
    recursive: bool = Field(default=False, description="Monitor subdirectories recursively")
    patterns: list[str] = Field(default_factory=list, description="File patterns to match")
    enabled: bool = Field(default=True, description="Whether this source is enabled")


class ParsedLog(BaseModel):
    """Represents a parsed log entry with extracted structure."""
    
    timestamp: datetime = Field(..., description="When the log entry occurred")
    source: str = Field(..., description="Source file or system that generated the log")
    level: LogLevel = Field(..., description="Log severity level")
    template_id: str = Field(..., description="ID of the log template this entry matches")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Extracted parameters from the log message")
    raw_message: str = Field(..., description="Original raw log message")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    # Processing metadata
    processed_at: datetime = Field(default_factory=datetime.now, description="When this log was processed")
    processing_time_ms: float = Field(default=0.0, description="Time taken to process this log in milliseconds")
    
    @validator('timestamp')
    def validate_timestamp(cls, v):
        """Ensure timestamp is not in the future."""
        if v > datetime.now():
            raise ValueError("Log timestamp cannot be in the future")
        return v
    
    @validator('raw_message')
    def validate_raw_message(cls, v):
        """Ensure raw message is not empty."""
        if not v or not v.strip():
            raise ValueError("Raw message cannot be empty")
        return v.strip()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "source": self.source,
            "level": self.level.value,
            "template_id": self.template_id,
            "parameters": self.parameters,
            "raw_message": self.raw_message,
            "metadata": self.metadata,
            "processed_at": self.processed_at.isoformat(),
            "processing_time_ms": self.processing_time_ms
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ParsedLog':
        """Create instance from dictionary."""
        data = data.copy()
        data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        data["processed_at"] = datetime.fromisoformat(data["processed_at"])
        data["level"] = LogLevel(data["level"])
        return cls(**data)


class LogTemplate(BaseModel):
    """Represents a log message template extracted by parsing."""
    
    template_id: str = Field(..., description="Unique identifier for this template")
    pattern: str = Field(..., description="Template pattern with placeholders")
    parameter_types: Dict[str, str] = Field(default_factory=dict, description="Types of extracted parameters")
    frequency: int = Field(default=1, description="Number of times this template has been seen")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Confidence score for this template")
    
    # Temporal information
    first_seen: datetime = Field(default_factory=datetime.now, description="When this template was first observed")
    last_seen: datetime = Field(default_factory=datetime.now, description="When this template was last observed")
    
    # Statistics
    avg_parameters: int = Field(default=0, description="Average number of parameters per instance")
    sources: set[str] = Field(default_factory=set, description="Sources that have used this template")
    
    @validator('frequency')
    def validate_frequency(cls, v):
        """Ensure frequency is positive."""
        if v < 1:
            raise ValueError("Frequency must be at least 1")
        return v
    
    @validator('pattern')
    def validate_pattern(cls, v):
        """Ensure pattern is not empty."""
        if not v or not v.strip():
            raise ValueError("Pattern cannot be empty")
        return v.strip()
    
    def update_frequency(self, source: str) -> None:
        """Update frequency and metadata when template is matched."""
        self.frequency += 1
        self.last_seen = datetime.now()
        self.sources.add(source)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "template_id": self.template_id,
            "pattern": self.pattern,
            "parameter_types": self.parameter_types,
            "frequency": self.frequency,
            "confidence": self.confidence,
            "first_seen": self.first_seen.isoformat(),
            "last_seen": self.last_seen.isoformat(),
            "avg_parameters": self.avg_parameters,
            "sources": list(self.sources)
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LogTemplate':
        """Create instance from dictionary."""
        data = data.copy()
        data["first_seen"] = datetime.fromisoformat(data["first_seen"])
        data["last_seen"] = datetime.fromisoformat(data["last_seen"])
        data["sources"] = set(data.get("sources", []))
        return cls(**data)