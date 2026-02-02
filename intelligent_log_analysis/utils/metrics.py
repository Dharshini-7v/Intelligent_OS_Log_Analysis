"""Metrics collection and monitoring utilities."""

import time
from collections import defaultdict, deque
from contextlib import contextmanager
from dataclasses import dataclass, field
from threading import Lock
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from .logging import get_logger

logger = get_logger("metrics")


@dataclass
class MetricValue:
    """Represents a single metric measurement."""
    value: float
    timestamp: datetime
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class MetricStats:
    """Statistical summary of metric values."""
    count: int
    sum: float
    min: float
    max: float
    avg: float
    
    @classmethod
    def from_values(cls, values: List[float]) -> 'MetricStats':
        """Create stats from list of values."""
        if not values:
            return cls(0, 0.0, 0.0, 0.0, 0.0)
        
        return cls(
            count=len(values),
            sum=sum(values),
            min=min(values),
            max=max(values),
            avg=sum(values) / len(values)
        )


class MetricsCollector:
    """Collects and manages system performance metrics."""
    
    def __init__(self, retention_period: timedelta = timedelta(hours=24)):
        self.retention_period = retention_period
        self._metrics: Dict[str, deque] = defaultdict(lambda: deque())
        self._counters: Dict[str, int] = defaultdict(int)
        self._gauges: Dict[str, float] = defaultdict(float)
        self._lock = Lock()
    
    def record_metric(self, name: str, value: float, tags: Optional[Dict[str, str]] = None) -> None:
        """Record a metric value with optional tags."""
        with self._lock:
            metric = MetricValue(
                value=value,
                timestamp=datetime.now(),
                tags=tags or {}
            )
            
            self._metrics[name].append(metric)
            self._cleanup_old_metrics(name)
    
    def increment_counter(self, name: str, value: int = 1, tags: Optional[Dict[str, str]] = None) -> None:
        """Increment a counter metric."""
        with self._lock:
            key = self._make_key(name, tags)
            self._counters[key] += value
    
    def set_gauge(self, name: str, value: float, tags: Optional[Dict[str, str]] = None) -> None:
        """Set a gauge metric value."""
        with self._lock:
            key = self._make_key(name, tags)
            self._gauges[key] = value
    
    def get_metric_stats(self, name: str, since: Optional[datetime] = None) -> MetricStats:
        """Get statistical summary of a metric."""
        with self._lock:
            if name not in self._metrics:
                return MetricStats(0, 0.0, 0.0, 0.0, 0.0)
            
            cutoff = since or (datetime.now() - self.retention_period)
            values = [
                m.value for m in self._metrics[name]
                if m.timestamp >= cutoff
            ]
            
            return MetricStats.from_values(values)
    
    def get_counter_value(self, name: str, tags: Optional[Dict[str, str]] = None) -> int:
        """Get current counter value."""
        with self._lock:
            key = self._make_key(name, tags)
            return self._counters.get(key, 0)
    
    def get_gauge_value(self, name: str, tags: Optional[Dict[str, str]] = None) -> float:
        """Get current gauge value."""
        with self._lock:
            key = self._make_key(name, tags)
            return self._gauges.get(key, 0.0)
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """Get all current metrics as a dictionary."""
        with self._lock:
            result = {
                'metrics': {},
                'counters': dict(self._counters),
                'gauges': dict(self._gauges)
            }
            
            for name, values in self._metrics.items():
                if values:
                    result['metrics'][name] = self.get_metric_stats(name)
            
            return result
    
    @contextmanager
    def timer(self, name: str, tags: Optional[Dict[str, str]] = None):
        """Context manager for timing operations."""
        start_time = time.time()
        try:
            yield
        finally:
            duration = time.time() - start_time
            self.record_metric(name, duration, tags)
    
    def _make_key(self, name: str, tags: Optional[Dict[str, str]]) -> str:
        """Create a unique key for tagged metrics."""
        if not tags:
            return name
        
        tag_str = ','.join(f"{k}={v}" for k, v in sorted(tags.items()))
        return f"{name}[{tag_str}]"
    
    def _cleanup_old_metrics(self, name: str) -> None:
        """Remove metrics older than retention period."""
        cutoff = datetime.now() - self.retention_period
        metrics = self._metrics[name]
        
        while metrics and metrics[0].timestamp < cutoff:
            metrics.popleft()


# Global metrics collector instance
metrics = MetricsCollector()