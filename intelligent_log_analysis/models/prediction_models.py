"""Prediction and machine learning related data models."""

from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field, validator


class PredictionType(str, Enum):
    """Types of predictions that can be made."""
    SYSTEM_FAILURE = "system_failure"
    PERFORMANCE_DEGRADATION = "performance_degradation"
    SECURITY_INCIDENT = "security_incident"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    SERVICE_OUTAGE = "service_outage"
    ANOMALY_ESCALATION = "anomaly_escalation"


class PredictionStatus(str, Enum):
    """Status of a prediction."""
    ACTIVE = "active"
    CONFIRMED = "confirmed"
    FALSE_POSITIVE = "false_positive"
    EXPIRED = "expired"
    SUPERSEDED = "superseded"


class ContributingFactor(BaseModel):
    """A factor that contributes to a prediction."""
    
    factor_id: str = Field(..., description="Unique identifier for this factor")
    factor_type: str = Field(..., description="Type of contributing factor")
    description: str = Field(..., description="Human-readable description")
    weight: float = Field(..., ge=0.0, le=1.0, description="Weight/importance of this factor")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in this factor")
    
    # Evidence
    evidence: Dict[str, Any] = Field(default_factory=dict, description="Supporting evidence")
    log_patterns: List[str] = Field(default_factory=list, description="Related log patterns")
    metrics: Dict[str, float] = Field(default_factory=dict, description="Related metrics")
    
    @validator('description')
    def validate_description(cls, v):
        """Ensure description is not empty."""
        if not v or not v.strip():
            raise ValueError("Description cannot be empty")
        return v.strip()


class PredictionExplanation(BaseModel):
    """Explanation for why a prediction was made."""
    
    # Model information
    model_name: str = Field(..., description="Name of the model that made the prediction")
    model_version: str = Field(..., description="Version of the model")
    algorithm: str = Field(..., description="Algorithm used for prediction")
    
    # Feature importance
    feature_importance: Dict[str, float] = Field(default_factory=dict, description="Feature importance scores")
    contributing_factors: List[ContributingFactor] = Field(default_factory=list, description="Factors contributing to prediction")
    
    # Decision path
    decision_path: List[str] = Field(default_factory=list, description="Decision path through the model")
    threshold_analysis: Dict[str, Any] = Field(default_factory=dict, description="Analysis of thresholds used")
    
    # Similar cases
    similar_historical_cases: List[str] = Field(default_factory=list, description="Similar historical cases")
    
    def add_contributing_factor(self, factor: ContributingFactor) -> None:
        """Add a contributing factor to the explanation."""
        self.contributing_factors.append(factor)
    
    def get_top_factors(self, n: int = 5) -> List[ContributingFactor]:
        """Get the top N contributing factors by weight."""
        return sorted(self.contributing_factors, key=lambda f: f.weight, reverse=True)[:n]


class Prediction(BaseModel):
    """Represents a prediction made by the ML engine."""
    
    prediction_id: str = Field(..., description="Unique identifier for this prediction")
    timestamp: datetime = Field(default_factory=datetime.now, description="When the prediction was made")
    
    # Prediction details
    prediction_type: PredictionType = Field(..., description="Type of event being predicted")
    predicted_event: str = Field(..., description="Description of the predicted event")
    probability: float = Field(..., ge=0.0, le=1.0, description="Probability of the event occurring")
    
    # Time horizon
    time_horizon: timedelta = Field(..., description="Time window for when event is expected")
    earliest_time: datetime = Field(..., description="Earliest time event could occur")
    latest_time: datetime = Field(..., description="Latest time event could occur")
    most_likely_time: Optional[datetime] = Field(default=None, description="Most likely time for event")
    
    # Confidence and uncertainty
    confidence_interval: Tuple[float, float] = Field(..., description="Confidence interval for probability")
    uncertainty: float = Field(default=0.0, ge=0.0, le=1.0, description="Uncertainty in the prediction")
    model_confidence: float = Field(..., ge=0.0, le=1.0, description="Model's confidence in prediction")
    
    # Explanation and reasoning
    explanation: PredictionExplanation = Field(..., description="Explanation for the prediction")
    
    # Impact assessment
    potential_impact: str = Field(..., description="Description of potential impact")
    impact_severity: float = Field(default=0.5, ge=0.0, le=1.0, description="Severity of potential impact")
    affected_systems: List[str] = Field(default_factory=list, description="Systems that could be affected")
    
    # Recommendations
    recommended_actions: List[str] = Field(default_factory=list, description="Recommended preventive actions")
    mitigation_strategies: List[str] = Field(default_factory=list, description="Mitigation strategies")
    monitoring_suggestions: List[str] = Field(default_factory=list, description="Additional monitoring suggestions")
    
    # Status and validation
    status: PredictionStatus = Field(default=PredictionStatus.ACTIVE, description="Current status of prediction")
    validation_deadline: datetime = Field(..., description="When prediction should be validated")
    
    # Feedback and learning
    actual_outcome: Optional[bool] = Field(default=None, description="Whether prediction came true")
    outcome_timestamp: Optional[datetime] = Field(default=None, description="When outcome was determined")
    feedback_notes: Optional[str] = Field(default=None, description="Feedback from administrators")
    accuracy_score: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Accuracy score after validation")
    
    # Metadata
    tags: set[str] = Field(default_factory=set, description="Tags for categorization")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    @validator('predicted_event', 'potential_impact')
    def validate_text_fields(cls, v):
        """Ensure text fields are not empty."""
        if not v or not v.strip():
            raise ValueError("Text fields cannot be empty")
        return v.strip()
    
    @validator('time_horizon')
    def validate_time_horizon(cls, v):
        """Ensure time horizon is positive."""
        if v.total_seconds() <= 0:
            raise ValueError("Time horizon must be positive")
        return v
    
    @validator('confidence_interval')
    def validate_confidence_interval(cls, v):
        """Ensure confidence interval is valid."""
        lower, upper = v
        if not (0 <= lower <= upper <= 1):
            raise ValueError("Confidence interval must be [lower, upper] where 0 <= lower <= upper <= 1")
        return v
    
    def validate_time_consistency(self):
        """Ensure time fields are consistent."""
        if self.earliest_time >= self.latest_time:
            raise ValueError("Earliest time must be before latest time")
        
        if self.most_likely_time and not (self.earliest_time <= self.most_likely_time <= self.latest_time):
            raise ValueError("Most likely time must be between earliest and latest times")
        
        return self
    
    def is_expired(self) -> bool:
        """Check if prediction has expired."""
        return datetime.now() > self.latest_time
    
    def is_due_for_validation(self) -> bool:
        """Check if prediction is due for validation."""
        return datetime.now() >= self.validation_deadline
    
    def is_high_confidence(self, threshold: float = 0.8) -> bool:
        """Check if prediction has high confidence."""
        return self.probability >= threshold and self.model_confidence >= threshold
    
    def validate_outcome(self, outcome: bool, notes: Optional[str] = None) -> None:
        """Validate the prediction outcome."""
        self.actual_outcome = outcome
        self.outcome_timestamp = datetime.now()
        
        if notes:
            self.feedback_notes = notes
        
        # Update status
        if outcome:
            self.status = PredictionStatus.CONFIRMED
        else:
            self.status = PredictionStatus.FALSE_POSITIVE
        
        # Calculate accuracy score
        if outcome:
            self.accuracy_score = self.probability
        else:
            self.accuracy_score = 1.0 - self.probability
    
    def add_tag(self, tag: str) -> None:
        """Add a tag to this prediction."""
        self.tags.add(tag)
    
    def remove_tag(self, tag: str) -> None:
        """Remove a tag from this prediction."""
        self.tags.discard(tag)
    
    def get_time_until_event(self) -> Optional[timedelta]:
        """Get time until most likely event occurrence."""
        if self.most_likely_time:
            return max(timedelta(0), self.most_likely_time - datetime.now())
        return None
    
    def get_urgency_score(self) -> float:
        """Calculate urgency score based on probability, impact, and time."""
        time_factor = 1.0
        if self.most_likely_time:
            hours_until = (self.most_likely_time - datetime.now()).total_seconds() / 3600
            time_factor = max(0.1, 1.0 / max(1.0, hours_until / 24))  # Higher urgency for sooner events
        
        return self.probability * self.impact_severity * time_factor
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "prediction_id": self.prediction_id,
            "timestamp": self.timestamp.isoformat(),
            "prediction_type": self.prediction_type.value,
            "predicted_event": self.predicted_event,
            "probability": self.probability,
            "time_horizon": self.time_horizon.total_seconds(),
            "earliest_time": self.earliest_time.isoformat(),
            "latest_time": self.latest_time.isoformat(),
            "most_likely_time": self.most_likely_time.isoformat() if self.most_likely_time else None,
            "confidence_interval": list(self.confidence_interval),
            "uncertainty": self.uncertainty,
            "model_confidence": self.model_confidence,
            "explanation": {
                "model_name": self.explanation.model_name,
                "model_version": self.explanation.model_version,
                "algorithm": self.explanation.algorithm,
                "feature_importance": self.explanation.feature_importance,
                "contributing_factors": [
                    {
                        "factor_id": f.factor_id,
                        "factor_type": f.factor_type,
                        "description": f.description,
                        "weight": f.weight,
                        "confidence": f.confidence,
                        "evidence": f.evidence,
                        "log_patterns": f.log_patterns,
                        "metrics": f.metrics
                    }
                    for f in self.explanation.contributing_factors
                ],
                "decision_path": self.explanation.decision_path,
                "threshold_analysis": self.explanation.threshold_analysis,
                "similar_historical_cases": self.explanation.similar_historical_cases
            },
            "potential_impact": self.potential_impact,
            "impact_severity": self.impact_severity,
            "affected_systems": self.affected_systems,
            "recommended_actions": self.recommended_actions,
            "mitigation_strategies": self.mitigation_strategies,
            "monitoring_suggestions": self.monitoring_suggestions,
            "status": self.status.value,
            "validation_deadline": self.validation_deadline.isoformat(),
            "actual_outcome": self.actual_outcome,
            "outcome_timestamp": self.outcome_timestamp.isoformat() if self.outcome_timestamp else None,
            "feedback_notes": self.feedback_notes,
            "accuracy_score": self.accuracy_score,
            "tags": list(self.tags),
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Prediction':
        """Create instance from dictionary."""
        data = data.copy()
        
        # Convert explanation
        if "explanation" in data:
            exp_data = data["explanation"]
            contributing_factors = []
            for f_data in exp_data.get("contributing_factors", []):
                contributing_factors.append(ContributingFactor(**f_data))
            exp_data["contributing_factors"] = contributing_factors
            data["explanation"] = PredictionExplanation(**exp_data)
        
        # Convert timestamps
        data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        data["earliest_time"] = datetime.fromisoformat(data["earliest_time"])
        data["latest_time"] = datetime.fromisoformat(data["latest_time"])
        data["validation_deadline"] = datetime.fromisoformat(data["validation_deadline"])
        
        if data.get("most_likely_time"):
            data["most_likely_time"] = datetime.fromisoformat(data["most_likely_time"])
        if data.get("outcome_timestamp"):
            data["outcome_timestamp"] = datetime.fromisoformat(data["outcome_timestamp"])
        
        # Convert time horizon
        data["time_horizon"] = timedelta(seconds=data["time_horizon"])
        
        # Convert confidence interval
        data["confidence_interval"] = tuple(data["confidence_interval"])
        
        # Convert sets
        data["tags"] = set(data.get("tags", []))
        
        # Convert enums
        data["prediction_type"] = PredictionType(data["prediction_type"])
        data["status"] = PredictionStatus(data["status"])
        
        return cls(**data)