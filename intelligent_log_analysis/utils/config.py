"""Configuration management utilities."""

import json
import yaml
import asyncio
from pathlib import Path
from typing import Any, Dict, Optional, Union, Callable, List
from pydantic import BaseModel, ValidationError
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from .logging import get_logger

logger = get_logger("config")


class ConfigFileHandler(FileSystemEventHandler):
    """File system event handler for configuration file changes."""
    
    def __init__(self, config_manager: 'ConfigManager'):
        self.config_manager = config_manager
        super().__init__()
    
    def on_modified(self, event):
        """Handle file modification events."""
        if not event.is_directory and event.src_path == str(self.config_manager.config_path):
            logger.info(f"Configuration file {event.src_path} modified, reloading...")
            try:
                self.config_manager.load_config()
            except Exception as e:
                logger.error(f"Error reloading configuration: {e}")


class ConfigManager:
    """Manages system configuration with hot-reload capability."""
    
    def __init__(self, config_path: Union[str, Path], enable_hot_reload: bool = True):
        self.config_path = Path(config_path)
        self._config: Dict[str, Any] = {}
        self._callbacks: Dict[str, List[Callable]] = {}
        self._observer: Optional[Observer] = None
        self._enable_hot_reload = enable_hot_reload
        self._validated_configs: Dict[str, BaseModel] = {}
        
        self.load_config()
        
        if enable_hot_reload:
            self._setup_file_watcher()
    
    def load_config(self) -> None:
        """Load configuration from file."""
        if not self.config_path.exists():
            logger.warning(f"Configuration file {self.config_path} not found, using defaults")
            self._config = {}
            return
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                if self.config_path.suffix.lower() in ['.yaml', '.yml']:
                    self._config = yaml.safe_load(f) or {}
                else:
                    self._config = json.load(f)
            
            logger.info(f"Configuration loaded from {self.config_path}")
            
            # Clear validated configs cache since config changed
            self._validated_configs.clear()
            
            # Notify callbacks
            self._notify_callbacks()
            
        except (json.JSONDecodeError, yaml.YAMLError) as e:
            logger.error(f"Error parsing configuration file: {e}")
            raise
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            raise
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key (supports dot notation)."""
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any, save: bool = False) -> None:
        """Set configuration value by key (supports dot notation)."""
        keys = key.split('.')
        config = self._config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        old_value = config.get(keys[-1])
        config[keys[-1]] = value
        
        # Clear validated configs cache if value changed
        if old_value != value:
            self._validated_configs.clear()
        
        # Save to file if requested
        if save:
            self.save_config()
        
        # Notify callbacks
        self._notify_callbacks()
    
    def update(self, updates: Dict[str, Any], save: bool = False) -> None:
        """Update multiple configuration values."""
        for key, value in updates.items():
            self.set(key, value, save=False)
        
        if save:
            self.save_config()
    
    def save_config(self) -> None:
        """Save current configuration to file."""
        try:
            # Ensure parent directory exists
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                if self.config_path.suffix.lower() in ['.yaml', '.yml']:
                    yaml.safe_dump(self._config, f, default_flow_style=False, indent=2)
                else:
                    json.dump(self._config, f, indent=2)
            
            logger.info(f"Configuration saved to {self.config_path}")
            
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
            raise
    
    def register_callback(self, section: str, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Register callback for configuration changes."""
        if section not in self._callbacks:
            self._callbacks[section] = []
        self._callbacks[section].append(callback)
        
        # Call immediately with current config
        section_config = self.get(section, {})
        try:
            callback(section_config)
        except Exception as e:
            logger.error(f"Error in initial configuration callback: {e}")
    
    def unregister_callback(self, section: str, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Unregister a configuration callback."""
        if section in self._callbacks:
            try:
                self._callbacks[section].remove(callback)
            except ValueError:
                pass
    
    def _notify_callbacks(self) -> None:
        """Notify all registered callbacks of configuration changes."""
        for section, callbacks in self._callbacks.items():
            section_config = self.get(section, {})
            for callback in callbacks:
                try:
                    callback(section_config)
                except Exception as e:
                    logger.error(f"Error in configuration callback for section '{section}': {e}")
    
    def validate_with_model(self, model_class: type[BaseModel], section: Optional[str] = None) -> BaseModel:
        """Validate configuration section with Pydantic model."""
        cache_key = f"{model_class.__name__}:{section or 'root'}"
        
        # Return cached validated config if available
        if cache_key in self._validated_configs:
            return self._validated_configs[cache_key]
        
        config_data = self.get(section) if section else self._config
        
        try:
            validated_config = model_class(**config_data)
            self._validated_configs[cache_key] = validated_config
            return validated_config
        except ValidationError as e:
            logger.error(f"Configuration validation error for {model_class.__name__}: {e}")
            raise
    
    def get_validated_config(self, model_class: type[BaseModel], section: Optional[str] = None) -> BaseModel:
        """Get validated configuration, creating with defaults if section doesn't exist."""
        try:
            return self.validate_with_model(model_class, section)
        except ValidationError:
            # If validation fails, try creating with defaults
            logger.warning(f"Using default configuration for {model_class.__name__}")
            default_config = model_class()
            
            # Save the default config
            if section:
                self.set(section, default_config.model_dump(), save=True)
            
            return default_config
    
    def _setup_file_watcher(self) -> None:
        """Setup file system watcher for hot-reload."""
        if not self.config_path.exists():
            return
        
        try:
            self._observer = Observer()
            event_handler = ConfigFileHandler(self)
            self._observer.schedule(
                event_handler,
                str(self.config_path.parent),
                recursive=False
            )
            self._observer.start()
            logger.info(f"File watcher started for {self.config_path}")
        except Exception as e:
            logger.warning(f"Could not setup file watcher: {e}")
    
    def stop_file_watcher(self) -> None:
        """Stop the file system watcher."""
        if self._observer:
            self._observer.stop()
            self._observer.join()
            self._observer = None
            logger.info("File watcher stopped")
    
    def reload(self) -> None:
        """Manually reload configuration from file."""
        self.load_config()
    
    def get_all_config(self) -> Dict[str, Any]:
        """Get the entire configuration dictionary."""
        return self._config.copy()
    
    def has_section(self, section: str) -> bool:
        """Check if a configuration section exists."""
        return self.get(section) is not None
    
    def remove_section(self, section: str, save: bool = False) -> bool:
        """Remove a configuration section."""
        if section in self._config:
            del self._config[section]
            self._validated_configs.clear()
            
            if save:
                self.save_config()
            
            self._notify_callbacks()
            return True
        return False
    
    def __del__(self):
        """Cleanup when object is destroyed."""
        self.stop_file_watcher()