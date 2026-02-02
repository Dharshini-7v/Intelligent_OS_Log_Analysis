"""Anomaly detection related data models."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, validator


class SeverityLevel(str, Enum):
    """Severity levels for anomalies."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AnomalyType(str, Enum):
    """Types of anomalies that can be detected."""
    STATISTICAL = "statistical"  # Statistical deviation from baseline
    FREQUENCY = "frequency"  # Unusual frequency patterns
    SEQUENCE = "sequence"  # Unusual sequence patterns
    TEMPORAL = "temporal"  # Time-based anomalies
    CONTEXTUAL = "contextual"  # Context-dependent anomalies
    SECURITY = "security"  # Security-related anomalies


class AnomalyContext(BaseModel):
    """Context information for an anomaly."""
    
    # Baseline information
    baseline_value: Optional[float] = Field(default=None, description="Expected baseline value")
    observed_value: Optional[float] = Field(default=None, description="Actual observed value")
    threshold: Optional[float] = Field(default=None, description="Threshold that was exceeded")
    
    # Pattern context
    expected_pattern: Optional[str] = Field(default=None, description="Expected pattern")
    observed_pattern: Optional[str] = Field(default=None, description="Actual observed pattern")
    
    # Temporal context
    time_window: Optional[str] = Field(default=None, description="Time window for analysis")
    historical_frequency: Optional[float] = Field(default=None, description="Historical frequency")
    current_frequency: Optional[float] = Field(default=None, description="Current frequency")
    
    # Additional metadata
    related_events: List[str] = Field(default_factory=list, description="Related log events or patterns")
    system_state: Dict[str, Any] = Field(default_factory=dict, description="System state at time of anomaly")


class Anomaly(BaseModel):
    """Represents a detected anomaly in log data."""
    
    anomaly_id: str = Field(..., description="Unique identifier for this anomaly")
    timestamp: datetime = Field(..., description="When the anomaly was detected")
    
    # Classification
    anomaly_type: AnomalyType = Field(..., description="Type of anomaly detected")
    severity: SeverityLevel = Field(..., description="Severity level of the anomaly")
    
    # Description and details
    title: str = Field(..., description="Brief title describing the anomaly")
    description: str = Field(..., description="Detailed description of the anomaly")
    
    # Affected data
    affected_logs: List[str] = Field(default_factory=list, description="IDs of log entries involved in the anomaly")
    affected_patterns: List[str] = Field(default_factory=list, description="IDs of patterns involved in the anomaly")
    affected_sources: set[str] = Field(default_factory=set, description="Log sources affected by the anomaly")
    
    # Scoring and confidence
    deviation_score: float = Field(..., ge=0.0, description="Magnitude of deviation from normal")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in anomaly detection")
    risk_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Risk assessment score")
    
    # Context and analysis
    context: AnomalyContext = Field(default_factory=AnomalyContext, description="Contextual information")
    root_cause_analysis: Dict[str, Any] = Field(default_factory=dict, description="Root cause analysis results")
    
    # Status and resolution
    status: str = Field(default="open", description="Status of the anomaly (open, investigating, resolved)")
    acknowledged: bool = Field(default=False, description="Whether anomaly has been acknowledged")
    acknowledged_by: Optional[str] = Field(default=None, description="Who acknowledged the anomaly")
    acknowledged_at: Optional[datetime] = Field(default=None, description="When anomaly was acknowledged")
    
    # Resolution information
    resolved: bool = Field(default=False, description="Whether anomaly has been resolved")
    resolved_by: Optional[str] = Field(default=None, description="Who resolved the anomaly")
    resolved_at: Optional[datetime] = Field(default=None, description="When anomaly was resolved")
    resolution_notes: Optional[str] = Field(default=None, description="Notes about resolution")
    
    # Feedback and learning
    false_positive: Optional[bool] = Field(default=None, description="Whether this was a false positive")
    feedback_notes: Optional[str] = Field(default=None, description="Feedback from administrators")
    
    # Metadata
    tags: set[str] = Field(default_factory=set, description="Tags for categorization")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    @validator('title', 'description')
    def validate_text_fields(cls, v):
        """Ensure text fields are not empty."""
        if not v or not v.strip():
            raise ValueError("Text fields cannot be empty")
        return v.strip()
    
    @validator('deviation_score')
    def validate_deviation_score(cls, v):
        """Ensure deviation score is reasonable."""
        if v < 0:
            raise ValueError("Deviation score must be non-negative")
        return v
    
    def acknowledge(self, acknowledged_by: str, notes: Optional[str] = None) -> None:
        """Acknowledge the anomaly."""
        self.acknowledged = True
        self.acknowledged_by = acknowledged_by
        self.acknowledged_at = datetime.now()
        self.status = "investigating"
        
        if notes:
            self.feedback_notes = notes
    
    def resolve(self, resolved_by: str, resolution_notes: Optional[str] = None) -> None:
        """Mark the anomaly as resolved."""
        self.resolved = True
        self.resolved_by = resolved_by
        self.resolved_at = datetime.now()
        self.status = "resolved"
        
        if resolution_notes:
            self.resolution_notes = resolution_notes
    
    def mark_false_positive(self, feedback_notes: Optional[str] = None) -> None:
        """Mark the anomaly as a false positive."""
        self.false_positive = True
        self.status = "false_positive"
        
        if feedback_notes:
            self.feedback_notes = feedback_notes
    
    def add_tag(self, tag: str) -> None:
        """Add a tag to this anomaly."""
        self.tags.add(tag)
    
    def remove_tag(self, tag: str) -> None:
        """Remove a tag from this anomaly."""
        self.tags.discard(tag)
    
    def get_severity_numeric(self) -> float:
        """Get numeric representation of severity."""
        severity_map = {
            SeverityLevel.LOW: 0.25,
            SeverityLevel.MEDIUM: 0.5,
            SeverityLevel.HIGH: 0.75,
            SeverityLevel.CRITICAL: 1.0
        }
        return severity_map[self.severity]
    
    def is_actionable(self) -> bool:
        """Check if anomaly requires immediate action."""
        return (
            self.severity in [SeverityLevel.HIGH, SeverityLevel.CRITICAL] and
            not self.resolved and
            not self.false_positive
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "anomaly_id": self.anomaly_id,
            "timestamp": self.timestamp.isoformat(),
            "anomaly_type": self.anomaly_type.value,
            "severity": self.severity.value,
            "title": self.title,
            "description": self.description,
            "affected_logs": self.affected_logs,
            "affected_patterns": self.affected_patterns,
            "affected_sources": list(self.affected_sources),
            "deviation_score": self.deviation_score,
            "confidence": self.confidence,
            "risk_score": self.risk_score,
            "context": {
                "baseline_value": self.context.baseline_value,
                "observed_value": self.context.observed_value,
                "threshold": self.context.threshold,
                "expected_pattern": self.context.expected_pattern,
                "observed_pattern": self.context.observed_pattern,
                "time_window": self.context.time_window,
                "historical_frequency": self.context.historical_frequency,
                "current_frequency": self.context.current_frequency,
                "related_events": self.context.related_events,
                "system_state": self.context.system_state
            },
            "root_cause_analysis": self.root_cause_analysis,
            "status": self.status,
            "acknowledged": self.acknowledged,
            "acknowledged_by": self.acknowledged_by,
            "acknowledged_at": self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            "resolved": self.resolved,
            "resolved_by": self.resolved_by,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "resolution_notes": self.resolution_notes,
            "false_positive": self.false_positive,
            "feedback_notes": self.feedback_notes,
            "tags": list(self.tags),
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Anomaly':
        """Create instance from dictionary."""
        data = data.copy()
        
        # Convert context
        if "context" in data:
            context_data = data["context"]
            data["context"] = AnomalyContext(**context_data)
        
        # Convert timestamps
        data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        if data.get("acknowledged_at"):
            data["acknowledged_at"] = datetime.fromisoformat(data["acknowledged_at"])
        if data.get("resolved_at"):
            data["resolved_at"] = datetime.fromisoformat(data["resolved_at"])
        
        # Convert sets
        data["affected_sources"] = set(data.get("affected_sources", []))
        data["tags"] = set(data.get("tags", []))
        
        # Convert enums
        data["anomaly_type"] = AnomalyType(data["anomaly_type"])
        data["severity"] = SeverityLevel(data["severity"])
        
        return cls(**data)