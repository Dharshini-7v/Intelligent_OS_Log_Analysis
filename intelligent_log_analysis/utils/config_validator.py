"""Configuration validation utilities."""

from typing import Dict, List, Any, Optional, Tuple
from pydantic import ValidationError

from ..models.config_models import SystemConfig
from .logging import get_logger

logger = get_logger("config_validator")


class ConfigValidator:
    """Validates system configuration and provides helpful error messages."""
    
    @staticmethod
    def validate_system_config(config_data: Dict[str, Any]) -> Tuple[bool, List[str], Optional[SystemConfig]]:
        """
        Validate complete system configuration.
        
        Returns:
            Tuple of (is_valid, error_messages, validated_config)
        """
        errors = []
        validated_config = None
        
        try:
            validated_config = SystemConfig(**config_data)
            return True, [], validated_config
        except ValidationError as e:
            for error in e.errors():
                field_path = " -> ".join(str(loc) for loc in error["loc"])
                error_msg = f"{field_path}: {error['msg']}"
                errors.append(error_msg)
            
            return False, errors, None
    
    @staticmethod
    def validate_component_config(
        component_name: str, 
        config_data: Dict[str, Any], 
        system_config: SystemConfig
    ) -> Tuple[bool, List[str]]:
        """
        Validate configuration for a specific component.
        
        Args:
            component_name: Name of the component (e.g., 'collector', 'parser')
            config_data: Configuration data for the component
            system_config: Full system configuration for context
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        try:
            component_config = system_config.get_component_config(component_name)
            # If we get here, the config is valid
            return True, []
        except ValueError as e:
            errors.append(str(e))
        except ValidationError as e:
            for error in e.errors():
                field_path = " -> ".join(str(loc) for loc in error["loc"])
                error_msg = f"{component_name}.{field_path}: {error['msg']}"
                errors.append(error_msg)
        
        return False, errors
    
    @staticmethod
    def check_database_connectivity(db_config: Dict[str, Any]) -> List[str]:
        """
        Check database connectivity configuration.
        
        Returns:
            List of warning messages
        """
        warnings = []
        
        # Check InfluxDB configuration
        if not db_config.get("influxdb_token"):
            warnings.append("InfluxDB token is empty - authentication may fail")
        
        if db_config.get("influxdb_url", "").startswith("http://"):
            warnings.append("InfluxDB URL uses HTTP - consider HTTPS for production")
        
        # Check PostgreSQL configuration
        if not db_config.get("postgresql_password"):
            warnings.append("PostgreSQL password is empty - authentication may fail")
        
        # Check retention policies
        retention = db_config.get("retention_policies", {})
        if retention.get("raw_logs_days", 0) > 90:
            warnings.append("Raw logs retention > 90 days may consume significant storage")
        
        return warnings
    
    @staticmethod
    def check_performance_settings(perf_config: Dict[str, Any]) -> List[str]:
        """
        Check performance configuration for potential issues.
        
        Returns:
            List of warning messages
        """
        warnings = []
        
        max_entries = perf_config.get("max_log_entries_per_second", 0)
        max_memory = perf_config.get("max_memory_usage_mb", 0)
        
        if max_entries > 50000:
            warnings.append(f"Very high log processing rate ({max_entries}/sec) - ensure adequate resources")
        
        if max_memory > 8192:
            warnings.append(f"High memory limit ({max_memory}MB) - monitor system resources")
        
        if max_memory < 512:
            warnings.append(f"Low memory limit ({max_memory}MB) - may impact performance")
        
        # Check auto-scaling thresholds
        scale_up = perf_config.get("scale_up_threshold", 0.8)
        scale_down = perf_config.get("scale_down_threshold", 0.3)
        
        if scale_up - scale_down < 0.2:
            warnings.append("Small gap between scale up/down thresholds may cause oscillation")
        
        return warnings
    
    @staticmethod
    def check_alert_configuration(alert_config: Dict[str, Any]) -> List[str]:
        """
        Check alert system configuration.
        
        Returns:
            List of warning messages
        """
        warnings = []
        
        # Check if any notification method is enabled
        email_enabled = alert_config.get("email_enabled", False)
        webhook_enabled = alert_config.get("webhook_enabled", False)
        
        if not email_enabled and not webhook_enabled:
            warnings.append("No notification channels enabled - alerts will not be delivered")
        
        # Check rate limiting
        max_alerts = alert_config.get("max_alerts_per_minute", 10)
        if max_alerts > 100:
            warnings.append(f"High alert rate limit ({max_alerts}/min) may cause notification flooding")
        
        # Check thresholds
        pred_threshold = alert_config.get("prediction_confidence_threshold", 0.8)
        anomaly_threshold = alert_config.get("anomaly_severity_threshold", 0.6)
        
        if pred_threshold < 0.5:
            warnings.append("Low prediction confidence threshold may generate many false positives")
        
        if anomaly_threshold < 0.3:
            warnings.append("Low anomaly severity threshold may generate many low-priority alerts")
        
        return warnings
    
    @staticmethod
    def generate_config_report(config_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a comprehensive configuration validation report.
        
        Returns:
            Dictionary containing validation results and recommendations
        """
        report = {
            "valid": False,
            "errors": [],
            "warnings": [],
            "recommendations": [],
            "components": {}
        }
        
        # Validate overall configuration
        is_valid, errors, validated_config = ConfigValidator.validate_system_config(config_data)
        report["valid"] = is_valid
        report["errors"] = errors
        
        if not is_valid:
            return report
        
        # Check individual components
        components = ["collector", "parser", "pattern_detector", "ml_engine", 
                     "anomaly_detector", "alert_system", "database", "performance"]
        
        for component in components:
            component_data = config_data.get(component, {})
            comp_valid, comp_errors = ConfigValidator.validate_component_config(
                component, component_data, validated_config
            )
            
            report["components"][component] = {
                "valid": comp_valid,
                "errors": comp_errors
            }
        
        # Collect warnings from specific checks
        db_warnings = ConfigValidator.check_database_connectivity(config_data.get("database", {}))
        perf_warnings = ConfigValidator.check_performance_settings(config_data.get("performance", {}))
        alert_warnings = ConfigValidator.check_alert_configuration(config_data.get("alert_system", {}))
        
        report["warnings"].extend(db_warnings)
        report["warnings"].extend(perf_warnings)
        report["warnings"].extend(alert_warnings)
        
        # Generate recommendations
        recommendations = []
        
        if not config_data.get("database", {}).get("influxdb_token"):
            recommendations.append("Set up InfluxDB authentication token for secure access")
        
        if not config_data.get("alert_system", {}).get("email_enabled"):
            recommendations.append("Configure email notifications for critical alerts")
        
        if config_data.get("system", {}).get("log_level") == "DEBUG":
            recommendations.append("Use INFO or WARNING log level in production for better performance")
        
        report["recommendations"] = recommendations
        
        return report