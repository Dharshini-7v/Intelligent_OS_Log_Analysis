"""Pattern detection and analysis for log sequences."""

import asyncio
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple
import hashlib

from ..models.pattern_models import Pattern, PatternType, TemporalPattern
from ..models.log_models import ParsedLog
from ..models.config_models import PatternDetectorConfig
from ..utils.logging import get_logger
from ..utils.metrics import metrics

logger = get_logger("pattern_detector")


class PatternDetector:
    """Detects patterns in log sequences using sliding window analysis."""
    
    def __init__(self, config: PatternDetectorConfig):
        self.config = config
        self.patterns: Dict[str, Pattern] = {}
        self.recent_logs: deque = deque(maxlen=1000)  # Keep recent logs for pattern analysis
        self.template_sequences: Dict[str, List[Tuple[str, datetime]]] = defaultdict(list)
        
        # Pattern analysis state
        self.baseline_patterns: Set[str] = set()
        self.last_baseline_update = datetime.now()
        
    async def analyze_log(self, parsed_log: ParsedLog) -> List[Pattern]:
        """Analyze a new log entry for patterns."""
        detected_patterns = []
        
        try:
            # Add to recent logs
            self.recent_logs.append(parsed_log)
            
            # Track template sequences
            template_id = parsed_log.template_id
            timestamp = parsed_log.timestamp
            source = parsed_log.source
            
            # Add to sequence tracking
            self.template_sequences[source].append((template_id, timestamp))
            
            # Limit sequence length
            max_length = self.config.max_sequence_length * 2
            if len(self.template_sequences[source]) > max_length:
                self.template_sequences[source] = self.template_sequences[source][-max_length:]
            
            # Detect sequence patterns
            sequence_patterns = await self._detect_sequence_patterns(source)
            detected_patterns.extend(sequence_patterns)
            
            # Detect frequency patterns
            frequency_patterns = await self._detect_frequency_patterns()
            detected_patterns.extend(frequency_patterns)
            
            # Update pattern statistics
            for pattern in detected_patterns:
                await self._update_pattern_stats(pattern, parsed_log)
            
            # Update baseline if needed
            await self._update_baseline_if_needed()
            
            return detected_patterns
            
        except Exception as e:
            logger.error(f"Error analyzing log for patterns: {e}")
            return []
    
    async def _detect_sequence_patterns(self, source: str) -> List[Pattern]:
        """Detect sequential patterns in log templates."""
        detected_patterns = []
        
        try:
            sequence = self.template_sequences[source]
            if len(sequence) < 2:
                return detected_patterns
            
            # Look for patterns of different lengths
            for pattern_length in range(2, min(self.config.max_sequence_length + 1, len(sequence))):
                # Extract recent sequences
                for i in range(len(sequence) - pattern_length + 1):
                    seq_templates = [item[0] for item in sequence[i:i + pattern_length]]
                    seq_timestamps = [item[1] for item in sequence[i:i + pattern_length]]
                    
                    # Check if this sequence occurs frequently enough
                    pattern_key = " -> ".join(seq_templates)
                    pattern_id = hashlib.md5(pattern_key.encode()).hexdigest()[:12]
                    
                    if pattern_id in self.patterns:
                        # Update existing pattern
                        pattern = self.patterns[pattern_id]
                        pattern.update_occurrence(source, 0.0)
                        detected_patterns.append(pattern)
                    else:
                        # Check if we should create a new pattern
                        if await self._should_create_pattern(seq_templates, source):
                            pattern = Pattern(
                                pattern_id=pattern_id,
                                sequence=seq_templates,
                                frequency=1,
                                confidence=0.8,
                                pattern_type=PatternType.SEQUENCE
                            )
                            pattern.sources.add(source)
                            self.patterns[pattern_id] = pattern
                            detected_patterns.append(pattern)
            
        except Exception as e:
            logger.error(f"Error detecting sequence patterns: {e}")
        
        return detected_patterns
    
    async def _detect_frequency_patterns(self) -> List[Pattern]:
        """Detect frequency-based patterns."""
        detected_patterns = []
        
        try:
            # Count template frequencies in recent time window
            cutoff_time = datetime.now() - timedelta(minutes=self.config.short_window_minutes)
            recent_templates = defaultdict(int)
            
            for log in self.recent_logs:
                if log.timestamp >= cutoff_time:
                    recent_templates[log.template_id] += 1
            
            # Identify high-frequency templates
            for template_id, frequency in recent_templates.items():
                if frequency >= self.config.frequency_threshold:
                    pattern_id = f"freq_{template_id}"
                    
                    if pattern_id in self.patterns:
                        pattern = self.patterns[pattern_id]
                        pattern.frequency = frequency
                        detected_patterns.append(pattern)
                    else:
                        pattern = Pattern(
                            pattern_id=pattern_id,
                            sequence=[template_id],
                            frequency=frequency,
                            confidence=min(1.0, frequency / (self.config.frequency_threshold * 2)),
                            pattern_type=PatternType.FREQUENCY
                        )
                        self.patterns[pattern_id] = pattern
                        detected_patterns.append(pattern)
            
        except Exception as e:
            logger.error(f"Error detecting frequency patterns: {e}")
        
        return detected_patterns
    
    async def _should_create_pattern(self, sequence: List[str], source: str) -> bool:
        """Determine if a sequence should become a pattern."""
        # Count occurrences of this sequence in recent history
        sequence_str = " -> ".join(sequence)
        count = 0
        
        # Look through recent sequences
        recent_sequences = self.template_sequences[source][-50:]  # Last 50 entries
        
        for i in range(len(recent_sequences) - len(sequence) + 1):
            seq_slice = [item[0] for item in recent_sequences[i:i + len(sequence)]]
            if seq_slice == sequence:
                count += 1
        
        return count >= 3  # Require at least 3 occurrences
    
    async def _update_pattern_stats(self, pattern: Pattern, parsed_log: ParsedLog) -> None:
        """Update pattern statistics."""
        try:
            # Update temporal information
            pattern.temporal_info.update_with_occurrence(
                parsed_log.timestamp,
                pattern.last_seen if pattern.frequency > 1 else None
            )
            
            # Classify pattern type based on frequency and timing
            if pattern.frequency > self.config.frequency_threshold * 2:
                pattern.pattern_type = PatternType.FREQUENT
            elif pattern.temporal_info.is_periodic:
                pattern.pattern_type = PatternType.TEMPORAL
            
            # Update confidence based on consistency
            if pattern.frequency > 10:
                pattern.confidence = min(1.0, pattern.confidence + 0.1)
            
        except Exception as e:
            logger.error(f"Error updating pattern stats: {e}")
    
    async def _update_baseline_if_needed(self) -> None:
        """Update baseline patterns if enough time has passed."""
        try:
            now = datetime.now()
            hours_since_update = (now - self.last_baseline_update).total_seconds() / 3600
            
            if hours_since_update >= self.config.baseline_update_hours:
                await self._update_baseline()
                self.last_baseline_update = now
                
        except Exception as e:
            logger.error(f"Error updating baseline: {e}")
    
    async def _update_baseline(self) -> None:
        """Update the baseline of normal patterns."""
        try:
            # Consider patterns that have been stable for a while as baseline
            stable_patterns = []
            
            for pattern in self.patterns.values():
                age_hours = (datetime.now() - pattern.first_seen).total_seconds() / 3600
                if (age_hours >= self.config.baseline_days * 24 and 
                    pattern.frequency >= self.config.frequency_threshold and
                    pattern.confidence >= self.config.confidence_threshold):
                    stable_patterns.append(pattern.pattern_id)
            
            self.baseline_patterns.update(stable_patterns)
            logger.info(f"Updated baseline with {len(stable_patterns)} stable patterns")
            
        except Exception as e:
            logger.error(f"Error updating baseline: {e}")
    
    def classify_pattern(self, pattern: Pattern) -> PatternType:
        """Classify a pattern as normal or anomalous."""
        try:
            # Check if pattern is in baseline
            if pattern.pattern_id in self.baseline_patterns:
                return PatternType.NORMAL
            
            # Check frequency and confidence
            if (pattern.frequency < self.config.frequency_threshold or 
                pattern.confidence < self.config.confidence_threshold):
                return PatternType.ANOMALOUS
            
            # Check temporal characteristics
            if pattern.temporal_info.is_periodic:
                return PatternType.TEMPORAL
            
            if pattern.frequency > self.config.frequency_threshold * 3:
                return PatternType.FREQUENT
            
            return PatternType.NORMAL
            
        except Exception as e:
            logger.error(f"Error classifying pattern: {e}")
            return PatternType.NORMAL
    
    def get_pattern_stats(self) -> Dict[str, any]:
        """Get pattern detection statistics."""
        try:
            total_patterns = len(self.patterns)
            pattern_types = defaultdict(int)
            
            for pattern in self.patterns.values():
                pattern_types[pattern.pattern_type.value] += 1
            
            return {
                'total_patterns': total_patterns,
                'baseline_patterns': len(self.baseline_patterns),
                'pattern_types': dict(pattern_types),
                'recent_logs_count': len(self.recent_logs)
            }
            
        except Exception as e:
            logger.error(f"Error getting pattern stats: {e}")
            return {}
    
    def get_recent_patterns(self, limit: int = 20) -> List[Pattern]:
        """Get recently detected patterns."""
        try:
            sorted_patterns = sorted(
                self.patterns.values(),
                key=lambda p: p.last_seen,
                reverse=True
            )
            return sorted_patterns[:limit]
            
        except Exception as e:
            logger.error(f"Error getting recent patterns: {e}")
            return []
    
    def get_frequent_patterns(self, limit: int = 10) -> List[Pattern]:
        """Get most frequent patterns."""
        try:
            sorted_patterns = sorted(
                self.patterns.values(),
                key=lambda p: p.frequency,
                reverse=True
            )
            return sorted_patterns[:limit]
            
        except Exception as e:
            logger.error(f"Error getting frequent patterns: {e}")
            return []