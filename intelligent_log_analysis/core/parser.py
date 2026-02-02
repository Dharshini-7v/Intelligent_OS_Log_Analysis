"""Log parsing using the Drain algorithm."""

import re
import hashlib
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime

from ..models.log_models import ParsedLog, LogTemplate, LogLevel
from ..models.config_models import ParserConfig
from ..utils.logging import get_logger
from ..utils.metrics import metrics

logger = get_logger("parser")


@dataclass
class DrainNode:
    """Node in the Drain parsing tree."""
    depth: int
    key_token: Optional[str] = None
    children: Dict[str, 'DrainNode'] = field(default_factory=dict)
    templates: List[LogTemplate] = field(default_factory=list)
    
    def add_child(self, key: str) -> 'DrainNode':
        """Add a child node."""
        if key not in self.children:
            self.children[key] = DrainNode(depth=self.depth + 1, key_token=key)
        return self.children[key]


class DrainParser:
    """Drain algorithm implementation for log template extraction."""
    
    def __init__(self, config: ParserConfig):
        self.config = config
        self.root = DrainNode(depth=0)
        self.templates: Dict[str, LogTemplate] = {}
        
        # Regex patterns for common log formats
        self.timestamp_patterns = [
            r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}',
            r'\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2}',
            r'\w{3} \d{2} \d{2}:\d{2}:\d{2}',
            r'\d{10,13}',  # Unix timestamp
        ]
        
        self.ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
        self.number_pattern = r'\b\d+\b'
        self.hex_pattern = r'\b[0-9a-fA-F]{8,}\b'
        self.path_pattern = r'[/\\][\w/\\.-]*'
        
    def parse(self, log_message: str, source: str) -> Tuple[LogTemplate, Dict[str, Any]]:
        """Parse a log message and extract template and parameters."""
        try:
            # Preprocess the log message
            tokens = self._preprocess(log_message)
            
            # Search for existing template
            template, parameters = self._search_template(tokens, log_message, source)
            
            if template:
                template.update_frequency(source)
                return template, parameters
            else:
                # Create new template
                template = self._create_template(tokens, log_message, source)
                return template, {}
                
        except Exception as e:
            logger.error(f"Error parsing log message: {e}")
            # Return a generic template for unparseable logs
            generic_template = LogTemplate(
                template_id="generic_error",
                pattern="<UNPARSEABLE>",
                frequency=1
            )
            return generic_template, {"raw_message": log_message}
    
    def _preprocess(self, log_message: str) -> List[str]:
        """Preprocess log message into tokens."""
        # Remove extra whitespace and split into tokens
        tokens = log_message.strip().split()
        
        # Replace common variable patterns with wildcards
        processed_tokens = []
        for token in tokens:
            # Replace timestamps
            if any(re.match(pattern, token) for pattern in self.timestamp_patterns):
                processed_tokens.append('<TIMESTAMP>')
            # Replace IP addresses
            elif re.match(self.ip_pattern, token):
                processed_tokens.append('<IP>')
            # Replace file paths
            elif re.match(self.path_pattern, token):
                processed_tokens.append('<PATH>')
            # Replace hex values
            elif re.match(self.hex_pattern, token):
                processed_tokens.append('<HEX>')
            # Replace numbers
            elif re.match(self.number_pattern, token):
                processed_tokens.append('<NUM>')
            else:
                processed_tokens.append(token)
        
        return processed_tokens
    
    def _search_template(self, tokens: List[str], original_message: str, source: str) -> Tuple[Optional[LogTemplate], Dict[str, Any]]:
        """Search for matching template in the Drain tree."""
        if len(tokens) == 0:
            return None, {}
        
        # Navigate through the tree based on token count and first token
        current_node = self.root
        
        # Level 1: Group by token count
        token_count_key = str(len(tokens))
        if token_count_key not in current_node.children:
            return None, {}
        current_node = current_node.children[token_count_key]
        
        # Level 2: Group by first token
        first_token = tokens[0] if tokens else "*"
        if first_token not in current_node.children:
            # Try wildcard
            if "*" in current_node.children:
                current_node = current_node.children["*"]
            else:
                return None, {}
        else:
            current_node = current_node.children[first_token]
        
        # Search through templates at this node
        for template in current_node.templates:
            similarity, parameters = self._calculate_similarity(tokens, template.pattern.split(), original_message)
            if similarity >= self.config.drain_similarity_threshold:
                return template, parameters
        
        return None, {}
    
    def _calculate_similarity(self, tokens1: List[str], tokens2: List[str], original_message: str) -> Tuple[float, Dict[str, Any]]:
        """Calculate similarity between two token sequences."""
        if len(tokens1) != len(tokens2):
            return 0.0, {}
        
        matches = 0
        parameters = {}
        param_count = 0
        
        for i, (t1, t2) in enumerate(zip(tokens1, tokens2)):
            if t1 == t2:
                matches += 1
            elif t2.startswith('<') and t2.endswith('>'):
                # Template has a wildcard, extract parameter
                param_name = f"param_{param_count}"
                parameters[param_name] = self._extract_original_value(original_message, i, t2)
                param_count += 1
                matches += 0.5  # Partial match for wildcards
        
        similarity = matches / len(tokens1) if tokens1 else 0.0
        return similarity, parameters
    
    def _extract_original_value(self, original_message: str, token_index: int, wildcard_type: str) -> str:
        """Extract the original value from the log message."""
        tokens = original_message.split()
        if token_index < len(tokens):
            return tokens[token_index]
        return ""
    
    def _create_template(self, tokens: List[str], original_message: str, source: str) -> LogTemplate:
        """Create a new log template."""
        # Generate template ID
        template_pattern = " ".join(tokens)
        template_id = hashlib.md5(template_pattern.encode()).hexdigest()[:12]
        
        # Create template
        template = LogTemplate(
            template_id=template_id,
            pattern=template_pattern,
            frequency=1
        )
        template.sources.add(source)
        
        # Store template
        self.templates[template_id] = template
        
        # Add to Drain tree
        self._add_to_tree(tokens, template)
        
        logger.debug(f"Created new template: {template_id} - {template_pattern}")
        return template
    
    def _add_to_tree(self, tokens: List[str], template: LogTemplate) -> None:
        """Add template to the Drain tree."""
        current_node = self.root
        
        # Level 1: Group by token count
        token_count_key = str(len(tokens))
        current_node = current_node.add_child(token_count_key)
        
        # Level 2: Group by first token
        first_token = tokens[0] if tokens else "*"
        current_node = current_node.add_child(first_token)
        
        # Add template to this node
        current_node.templates.append(template)
        
        # Limit templates per node
        if len(current_node.templates) > self.config.drain_max_children:
            # Remove oldest template
            current_node.templates.pop(0)
    
    def get_template(self, template_id: str) -> Optional[LogTemplate]:
        """Get template by ID."""
        return self.templates.get(template_id)
    
    def get_all_templates(self) -> List[LogTemplate]:
        """Get all templates."""
        return list(self.templates.values())


class LogParser:
    """Main log parser that handles multiple formats and uses Drain algorithm."""
    
    def __init__(self, config: ParserConfig):
        self.config = config
        self.drain_parser = DrainParser(config)
        
        # Format-specific parsers
        self.format_parsers = {
            'syslog': self._parse_syslog,
            'json': self._parse_json,
            'windows_event': self._parse_windows_event,
            'apache': self._parse_apache,
            'nginx': self._parse_nginx
        }
        
        # Common log level patterns
        self.level_patterns = {
            'ERROR': ['ERROR', 'ERR', 'FATAL', 'CRITICAL'],
            'WARNING': ['WARNING', 'WARN', 'WRN'],
            'INFO': ['INFO', 'INFORMATION'],
            'DEBUG': ['DEBUG', 'DBG', 'TRACE']
        }
    
    def parse_log_entry(self, raw_message: str, source: str, log_format: str = 'auto') -> ParsedLog:
        """Parse a raw log entry into a structured ParsedLog object."""
        try:
            start_time = datetime.now()
            
            # Detect format if auto
            if log_format == 'auto':
                log_format = self._detect_format(raw_message)
            
            # Parse using format-specific parser
            if log_format in self.format_parsers:
                parsed_data = self.format_parsers[log_format](raw_message)
            else:
                parsed_data = self._parse_generic(raw_message)
            
            # Extract template using Drain algorithm
            template, parameters = self.drain_parser.parse(parsed_data['message'], source)
            
            # Create ParsedLog object
            parsed_log = ParsedLog(
                timestamp=parsed_data.get('timestamp', datetime.now()),
                source=source,
                level=parsed_data.get('level', LogLevel.INFO),
                template_id=template.template_id,
                parameters=parameters,
                raw_message=raw_message,
                metadata=parsed_data.get('metadata', {}),
                processing_time_ms=(datetime.now() - start_time).total_seconds() * 1000
            )
            
            # Record metrics
            metrics.record_metric("parser.processing_time_ms", parsed_log.processing_time_ms)
            metrics.increment_counter("parser.logs_parsed")
            
            return parsed_log
            
        except Exception as e:
            logger.error(f"Error parsing log entry: {e}")
            metrics.increment_counter("parser.parse_errors")
            
            # Return a basic parsed log for error cases
            return ParsedLog(
                timestamp=datetime.now(),
                source=source,
                level=LogLevel.ERROR,
                template_id="parse_error",
                parameters={},
                raw_message=raw_message,
                metadata={"parse_error": str(e)}
            )
    
    def _detect_format(self, raw_message: str) -> str:
        """Auto-detect log format."""
        # JSON format
        if raw_message.strip().startswith('{') and raw_message.strip().endswith('}'):
            return 'json'
        
        # Syslog format (RFC3164)
        if re.match(r'^<\d+>', raw_message) or re.match(r'^\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}', raw_message):
            return 'syslog'
        
        # Apache/Nginx access log
        if ' - - [' in raw_message or '] "' in raw_message:
            return 'apache'
        
        # Windows Event Log
        if 'EventID' in raw_message or 'Source:' in raw_message:
            return 'windows_event'
        
        return 'generic'
    
    def _parse_syslog(self, raw_message: str) -> Dict[str, Any]:
        """Parse syslog format."""
        # Basic syslog parsing
        timestamp_match = re.search(r'(\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})', raw_message)
        
        if timestamp_match:
            timestamp_str = timestamp_match.group(1)
            try:
                # Add current year since syslog doesn't include it
                current_year = datetime.now().year
                timestamp = datetime.strptime(f"{current_year} {timestamp_str}", "%Y %b %d %H:%M:%S")
            except:
                timestamp = datetime.now()
            
            # Extract message part
            message = raw_message[timestamp_match.end():].strip()
        else:
            timestamp = datetime.now()
            message = raw_message
        
        # Extract log level
        level = self._extract_log_level(message)
        
        return {
            'timestamp': timestamp,
            'level': level,
            'message': message,
            'metadata': {'format': 'syslog'}
        }
    
    def _parse_json(self, raw_message: str) -> Dict[str, Any]:
        """Parse JSON format."""
        import json
        
        try:
            data = json.loads(raw_message)
            
            # Extract common fields
            timestamp = data.get('timestamp', data.get('time', datetime.now()))
            if isinstance(timestamp, str):
                try:
                    timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                except:
                    timestamp = datetime.now()
            
            level_str = data.get('level', data.get('severity', 'INFO')).upper()
            level = LogLevel(level_str) if level_str in [l.value for l in LogLevel] else LogLevel.INFO
            
            message = data.get('message', data.get('msg', raw_message))
            
            return {
                'timestamp': timestamp,
                'level': level,
                'message': message,
                'metadata': {**data, 'format': 'json'}
            }
            
        except json.JSONDecodeError:
            return self._parse_generic(raw_message)
    
    def _parse_windows_event(self, raw_message: str) -> Dict[str, Any]:
        """Parse Windows Event Log format."""
        # Basic Windows event log parsing
        timestamp = datetime.now()
        level = LogLevel.INFO
        
        # Look for common Windows event patterns
        if 'Error' in raw_message or 'Failed' in raw_message:
            level = LogLevel.ERROR
        elif 'Warning' in raw_message:
            level = LogLevel.WARNING
        
        return {
            'timestamp': timestamp,
            'level': level,
            'message': raw_message,
            'metadata': {'format': 'windows_event'}
        }
    
    def _parse_apache(self, raw_message: str) -> Dict[str, Any]:
        """Parse Apache access log format."""
        # Common Log Format: IP - - [timestamp] "request" status size
        apache_pattern = r'(\S+) \S+ \S+ \[([^\]]+)\] "([^"]*)" (\d+) (\S+)'
        match = re.match(apache_pattern, raw_message)
        
        if match:
            ip, timestamp_str, request, status, size = match.groups()
            
            try:
                timestamp = datetime.strptime(timestamp_str, "%d/%b/%Y:%H:%M:%S %z")
            except:
                timestamp = datetime.now()
            
            # Determine log level based on HTTP status
            status_code = int(status) if status.isdigit() else 200
            if status_code >= 500:
                level = LogLevel.ERROR
            elif status_code >= 400:
                level = LogLevel.WARNING
            else:
                level = LogLevel.INFO
            
            return {
                'timestamp': timestamp,
                'level': level,
                'message': raw_message,
                'metadata': {
                    'format': 'apache',
                    'ip': ip,
                    'request': request,
                    'status': status,
                    'size': size
                }
            }
        
        return self._parse_generic(raw_message)
    
    def _parse_nginx(self, raw_message: str) -> Dict[str, Any]:
        """Parse Nginx access log format."""
        # Similar to Apache but with slight differences
        return self._parse_apache(raw_message)  # Use Apache parser as fallback
    
    def _parse_generic(self, raw_message: str) -> Dict[str, Any]:
        """Parse generic log format."""
        # Extract timestamp if present
        timestamp = self._extract_timestamp(raw_message)
        
        # Extract log level
        level = self._extract_log_level(raw_message)
        
        return {
            'timestamp': timestamp,
            'level': level,
            'message': raw_message,
            'metadata': {'format': 'generic'}
        }
    
    def _extract_timestamp(self, message: str) -> datetime:
        """Extract timestamp from log message."""
        for pattern in self.drain_parser.timestamp_patterns:
            match = re.search(pattern, message)
            if match:
                timestamp_str = match.group(0)
                
                # Try different timestamp formats
                formats = [
                    "%Y-%m-%d %H:%M:%S",
                    "%m/%d/%Y %H:%M:%S",
                    "%b %d %H:%M:%S"
                ]
                
                for fmt in formats:
                    try:
                        return datetime.strptime(timestamp_str, fmt)
                    except:
                        continue
                
                # Try Unix timestamp
                try:
                    return datetime.fromtimestamp(int(timestamp_str))
                except:
                    pass
        
        return datetime.now()
    
    def _extract_log_level(self, message: str) -> LogLevel:
        """Extract log level from message."""
        message_upper = message.upper()
        
        for level, patterns in self.level_patterns.items():
            for pattern in patterns:
                if pattern in message_upper:
                    return LogLevel(level)
        
        return LogLevel.INFO
    
    def get_template_stats(self) -> Dict[str, Any]:
        """Get template statistics."""
        templates = self.drain_parser.get_all_templates()
        
        return {
            'total_templates': len(templates),
            'most_frequent': sorted(templates, key=lambda t: t.frequency, reverse=True)[:10],
            'recent_templates': sorted(templates, key=lambda t: t.last_seen, reverse=True)[:10]
        }