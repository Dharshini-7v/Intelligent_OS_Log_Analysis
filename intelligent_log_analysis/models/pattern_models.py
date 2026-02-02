"""Pattern detection related data models."""

from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, validator


class PatternType(str, Enum):
    """Types of patterns that can be detected."""
    SEQUENCE = "sequence"  # Sequential patterns in log entries
    FREQUENCY = "frequency"  # Frequency-based patterns
    TEMPORAL = "temporal"  # Time-based patterns
    ANOMALOUS = "anomalous"  # Anomalous patterns
    NORMAL = "normal"  # Normal baseline patterns


class TemporalPattern(BaseModel):
    """Temporal characteristics of a pattern."""
    
    # Time-based statistics
    avg_interval_seconds: float = Field(default=0.0, description="Average time between pattern occurrences")
    min_interval_seconds: float = Field(default=0.0, description="Minimum time between occurrences")
    max_interval_seconds: float = Field(default=0.0, description="Maximum time between occurrences")
    
    # Periodicity
    is_periodic: bool = Field(default=False, description="Whether pattern shows periodic behavior")
    period_seconds: Optional[float] = Field(default=None, description="Period length if periodic")
    
    # Time of day patterns
    hour_distribution: Dict[int, int] = Field(default_factory=dict, description="Distribution by hour of day (0-23)")
    day_distribution: Dict[int, int] = Field(default_factory=dict, description="Distribution by day of week (0-6)")
    
    @validator('avg_interval_seconds', 'min_interval_seconds', 'max_interval_seconds')
    def validate_intervals(cls, v):
        """Ensure intervals are non-negative."""
        if v < 0:
            raise ValueError("Time intervals must be non-negative")
        return v
    
    def update_with_occurrence(self, timestamp: datetime, previous_timestamp: Optional[datetime] = None) -> None:
        """Update temporal statistics with a new occurrence."""
        hour = timestamp.hour
        day = timestamp.weekday()
        
        # Update distributions
        self.hour_distribution[hour] = self.hour_distribution.get(hour, 0) + 1
        self.day_distribution[day] = self.day_distribution.get(day, 0) + 1
        
        # Update intervals if we have a previous timestamp
        if previous_timestamp:
            interval = (timestamp - previous_timestamp).total_seconds()
            
            if self.avg_interval_seconds == 0:
                self.avg_interval_seconds = interval
                self.min_interval_seconds = interval
                self.max_interval_seconds = interval
            else:
                # Update running average (simplified)
                self.avg_interval_seconds = (self.avg_interval_seconds + interval) / 2
                self.min_interval_seconds = min(self.min_interval_seconds, interval)
                self.max_interval_seconds = max(self.max_interval_seconds, interval)


class Pattern(BaseModel):
    """Represents a detected pattern in log data."""
    
    pattern_id: str = Field(..., description="Unique identifier for this pattern")
    sequence: List[str] = Field(..., description="Sequence of template IDs that form this pattern")
    frequency: int = Field(default=1, description="Number of times this pattern has been observed")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Confidence score for pattern validity")
    
    # Classification
    pattern_type: PatternType = Field(default=PatternType.NORMAL, description="Type/classification of this pattern")
    severity: float = Field(default=0.0, ge=0.0, le=1.0, description="Severity score (0=benign, 1=critical)")
    
    # Temporal information
    temporal_info: TemporalPattern = Field(default_factory=TemporalPattern, description="Temporal characteristics")
    first_seen: datetime = Field(default_factory=datetime.now, description="When pattern was first detected")
    last_seen: datetime = Field(default_factory=datetime.now, description="When pattern was last observed")
    
    # Context and metadata
    sources: set[str] = Field(default_factory=set, description="Log sources where pattern appears")
    context: Dict[str, Any] = Field(default_factory=dict, description="Additional context information")
    tags: set[str] = Field(default_factory=set, description="Tags for categorization")
    
    # Statistical information
    avg_duration_seconds: float = Field(default=0.0, description="Average duration of pattern occurrence")
    std_duration_seconds: float = Field(default=0.0, description="Standard deviation of pattern duration")
    
    @validator('sequence')
    def validate_sequence(cls, v):
        """Ensure sequence is not empty."""
        if not v:
            raise ValueError("Pattern sequence cannot be empty")
        return v
    
    @validator('frequency')
    def validate_frequency(cls, v):
        """Ensure frequency is positive."""
        if v < 1:
            raise ValueError("Frequency must be at least 1")
        return v
    
    def update_occurrence(self, source: str, duration_seconds: float = 0.0, context: Optional[Dict[str, Any]] = None) -> None:
        """Update pattern statistics with a new occurrence."""
        self.frequency += 1
        self.last_seen = datetime.now()
        self.sources.add(source)
        
        # Update duration statistics
        if duration_seconds > 0:
            if self.avg_duration_seconds == 0:
                self.avg_duration_seconds = duration_seconds
            else:
                # Simple running average
                self.avg_duration_seconds = (self.avg_duration_seconds + duration_seconds) / 2
        
        # Update context
        if context:
            self.context.update(context)
        
        # Update temporal information
        self.temporal_info.update_with_occurrence(self.last_seen, self.first_seen if self.frequency == 1 else None)
    
    def add_tag(self, tag: str) -> None:
        """Add a tag to this pattern."""
        self.tags.add(tag)
    
    def remove_tag(self, tag: str) -> None:
        """Remove a tag from this pattern."""
        self.tags.discard(tag)
    
    def is_recent(self, threshold: timedelta = timedelta(hours=1)) -> bool:
        """Check if pattern has been seen recently."""
        return datetime.now() - self.last_seen <= threshold
    
    def get_occurrence_rate(self, time_window: timedelta = timedelta(hours=24)) -> float:
        """Calculate occurrence rate per hour within time window."""
        if not self.is_recent(time_window):
            return 0.0
        
        hours = time_window.total_seconds() / 3600
        return self.frequency / hours if hours > 0 else 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "pattern_id": self.pattern_id,
            "sequence": self.sequence,
            "frequency": self.frequency,
            "confidence": self.confidence,
            "pattern_type": self.pattern_type.value,
            "severity": self.severity,
            "temporal_info": {
                "avg_interval_seconds": self.temporal_info.avg_interval_seconds,
                "min_interval_seconds": self.temporal_info.min_interval_seconds,
                "max_interval_seconds": self.temporal_info.max_interval_seconds,
                "is_periodic": self.temporal_info.is_periodic,
                "period_seconds": self.temporal_info.period_seconds,
                "hour_distribution": self.temporal_info.hour_distribution,
                "day_distribution": self.temporal_info.day_distribution
            },
            "first_seen": self.first_seen.isoformat(),
            "last_seen": self.last_seen.isoformat(),
            "sources": list(self.sources),
            "context": self.context,
            "tags": list(self.tags),
            "avg_duration_seconds": self.avg_duration_seconds,
            "std_duration_seconds": self.std_duration_seconds
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Pattern':
        """Create instance from dictionary."""
        data = data.copy()
        
        # Convert temporal info
        if "temporal_info" in data:
            temporal_data = data["temporal_info"]
            data["temporal_info"] = TemporalPattern(**temporal_data)
        
        # Convert timestamps
        data["first_seen"] = datetime.fromisoformat(data["first_seen"])
        data["last_seen"] = datetime.fromisoformat(data["last_seen"])
        
        # Convert sets
        data["sources"] = set(data.get("sources", []))
        data["tags"] = set(data.get("tags", []))
        
        # Convert enum
        data["pattern_type"] = PatternType(data["pattern_type"])
        
        return cls(**data)