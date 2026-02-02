"""Pytest configuration and shared fixtures."""

import pytest
import tempfile
import shutil
from pathlib import Path
from typing import Generator

from intelligent_log_analysis.utils.config import ConfigManager


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for tests."""
    temp_path = Path(tempfile.mkdtemp())
    try:
        yield temp_path
    finally:
        shutil.rmtree(temp_path)


@pytest.fixture
def test_config(temp_dir: Path) -> ConfigManager:
    """Create a test configuration manager."""
    config_file = temp_dir / "test_config.yaml"
    config_file.write_text("""
system:
  log_level: "DEBUG"
  
collector:
  batch_size: 100
  processing_interval_seconds: 1
  
parser:
  drain:
    depth: 3
    similarity_threshold: 0.5
""")
    
    return ConfigManager(config_file)


@pytest.fixture
def sample_log_entries():
    """Sample log entries for testing."""
    return [
        "2024-01-22 10:00:01 INFO User login successful for user123",
        "2024-01-22 10:00:02 ERROR Failed to connect to database",
        "2024-01-22 10:00:03 INFO User logout for user123",
        "2024-01-22 10:00:04 WARNING High memory usage detected: 85%",
        "2024-01-22 10:00:05 INFO User login successful for user456",
    ]