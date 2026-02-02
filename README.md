# Intelligent OS Log Analysis System

A comprehensive system for analyzing Operating System logs using Machine Learning, Database Management Systems, and Pattern Recognition Algorithms.

## 🚀 Quick Start

### Prerequisites
```bash
pip install fastapi uvicorn PyJWT python-multipart jinja2 watchdog pydantic pyyaml
```

### Running the Application

#### Option 1: Web Interface (Recommended)
```bash
# Run the main application with web dashboard
python run_demo.py
```
Access at: http://localhost:8000

#### Option 2: Using the main module
```bash
# Run with default settings (port 8000)
python -m intelligent_log_analysis.main

# Run on custom port (if 8000 is busy)
python -m intelligent_log_analysis.main --port 8080

# Run in CLI mode (no web interface)
python -m intelligent_log_analysis.main --cli

# Run with custom config and log level
python -m intelligent_log_analysis.main --config config/custom.yaml --log-level DEBUG
```

#### Port Management
If port 8000 is busy:
```bash
# Check what's using port 8000
python check_port.py --check

# Kill processes using port 8000 (if safe to do so)
python check_port.py --kill

# Or run on a different port
python -m intelligent_log_analysis.main --port 8001
```

## 🔐 Authentication

### Demo Accounts
- **admin** / **admin123** (Administrator)
- **analyst** / **analyst123** (Log Analyst)  
- **demo** / **demo** (Viewer)

### User Registration
- Visit the registration page to create new accounts
- Choose between Viewer and Log Analyst roles
- Administrator accounts are restricted to demo accounts

## 📋 Features

- **Real-time Log Processing** - Monitor and analyze logs as they arrive
- **Pattern Detection** - Identify recurring patterns using advanced algorithms
- **Anomaly Detection** - Detect unusual behavior and security threats
- **ML Predictions** - Predict future system behavior and issues
- **User Management** - Role-based access control and user registration
- **Interactive Dashboard** - Web-based interface with real-time updates
- **WebSocket Streaming** - Live data updates without page refresh

## 🏗️ Project Structure

```
intelligent_log_analysis/
├── core/                 # Core processing components
│   ├── collector.py      # Log collection and monitoring
│   ├── parser.py         # Log parsing and template extraction
│   └── pattern_detector.py # Pattern recognition algorithms
├── models/               # Data models and schemas
├── utils/                # Utility functions and configuration
├── web/                  # Web application and dashboard
│   ├── app.py           # FastAPI application
│   └── templates/       # HTML templates
└── main.py              # Main application entry point
```

## 🛠️ Development

### Configuration
Edit `config/default.yaml` to customize system behavior:
- Log levels and file paths
- Processing parameters
- Database connections
- Alert thresholds

### Adding New Features
1. Implement core logic in `intelligent_log_analysis/core/`
2. Add data models in `intelligent_log_analysis/models/`
3. Update web interface in `intelligent_log_analysis/web/`
4. Add configuration options in `config/default.yaml`

## 📊 System Components

### Log Collector
- Monitors log files for changes
- Handles log rotation and file system events
- Supports multiple log formats

### Log Parser
- Extracts structured data from raw logs
- Implements Drain algorithm for template extraction
- Supports various log formats (syslog, JSON, Apache, etc.)

### Pattern Detector
- Identifies recurring log patterns
- Detects sequence-based patterns
- Calculates pattern confidence scores

### Anomaly Detector
- Rule-based anomaly detection
- Statistical analysis for outlier detection
- Severity-based alert classification

### Web Dashboard
- Real-time log stream visualization
- Pattern and anomaly displays
- User authentication and management
- Interactive charts and statistics

## 🔧 Command Line Options

```bash
python -m intelligent_log_analysis.main --help
```

Options:
- `--config PATH` - Custom configuration file
- `--log-level LEVEL` - Override log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `--port PORT` - Web interface port (default: 8000)
- `--cli` - Run in CLI mode without web interface

## 📝 License

This project is developed for educational purposes as part of an OS Log Analysis and Prediction system using ML, DBMS, and Pattern Algorithms.