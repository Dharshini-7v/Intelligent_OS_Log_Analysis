"""Main application entry point for the Intelligent OS Log Analysis System."""

import asyncio
import logging
import json
import yaml
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, HTTPException, Form, Depends, Cookie
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from models import LogEntry, Alert, SystemHealth
from database import DatabaseManager
from parser import DrainParser
from collector import LogCollector
from anomaly_detector import AnomalyDetector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("main")

app = FastAPI(title="Intelligent OS Log Analysis System")

# Global instances
db_manager: Optional[DatabaseManager] = None
log_parser: Optional[DrainParser] = None
log_collector: Optional[LogCollector] = None
anomaly_detector: Optional[AnomalyDetector] = None

# WebSocket connections
active_connections: List[WebSocket] = []

# Simple session store (in-memory for now)
active_sessions: Set[str] = set()

# Mock user for initial setup (can be moved to DB later)
DEMO_USERS = {
    "admin": "admin123",
    "analyst": "analyst123",
    "demo": "demo"
}

def load_config():
    """Load configuration from default.yaml."""
    config_path = Path("config/default.yaml")
    if not config_path.exists():
        logger.error(f"Config file not found: {config_path}")
        return {}
    
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

async def broadcast_update(data: Dict[str, Any]):
    """Broadcast updates to all connected WebSocket clients."""
    if not active_connections:
        return
        
    message = json.dumps(data)
    for connection in active_connections.copy():
        try:
            await connection.send_text(message)
        except Exception:
            active_connections.remove(connection)

# --- Authentication Helpers ---

async def get_current_user(session_id: Optional[str] = Cookie(None)):
    """Dependency to check for active session."""
    if not session_id or session_id not in active_sessions:
        raise HTTPException(status_code=302, detail="Not authenticated")
    return session_id

def log_processing_callback(line: str, file_path: str):
    """Callback for processing new log lines in real-time."""
    if not log_collector or not log_collector.loop:
        return
        
    # Use the existing event loop to process the log across threads
    log_collector.loop.call_soon_threadsafe(
        lambda: asyncio.create_task(process_log_entry(line, file_path))
    )

async def process_log_entry(line: str, file_path: str):
    """Process a single log line through the pipeline."""
    if not db_manager or not log_parser or not anomaly_detector:
        return
        
    try:
        # 1. Parse log
        log_entry = log_parser.parse_line(line, file_path)
        if not log_entry:
            return
            
        # 2. Get/Create template
        template_text = log_parser.get_template(log_entry.message)
        template_id = await db_manager.get_or_create_template(template_text)
        log_entry.template_id = template_id
        
        # 3. Store in MySQL
        log_id = await db_manager.insert_log(log_entry)
        log_entry.log_id = log_id
        
        # 4. Check for anomalies
        alert = anomaly_detector.check_for_anomaly(log_entry)
        if alert:
            await db_manager.insert_alert(alert)
            # Broadcast alert to WebSocket
            await broadcast_update({
                "type": "new_alert",
                "data": alert.dict()
            })
            
        # 5. Broadcast log to WebSocket
        await broadcast_update({
            "type": "new_log",
            "data": log_entry.dict(exclude={"timestamp"}),
            "timestamp": log_entry.timestamp.isoformat()
        })
        
        logger.info(f"Processed log entry: {log_entry.service} - {log_entry.log_level}")
        
    except Exception as e:
        logger.error(f"Error processing log entry: {e}")

@app.on_event("startup")
async def startup_event():
    """Initialize system components on startup."""
    global db_manager, log_parser, log_collector, anomaly_detector
    
    logger.info("Initializing Intelligent OS Log Analysis System...")
    
    # 1. Load config
    config = load_config()
    
    # 2. Initialize Database
    db_manager = DatabaseManager(config)
    await db_manager.initialize()
    
    # 3. Initialize Parser and Detector
    log_parser = DrainParser()
    anomaly_detector = AnomalyDetector()
    
    # 4. Initialize Collector
    # Priority paths for real log monitoring
    log_paths = [
        "/var/log/syslog", 
        "/var/log/auth.log", 
        "/var/log/messages",
        "logs" # Local logs directory
    ]
    
    # Ensure logs directory exists for Render
    os.makedirs("logs", exist_ok=True)
    system_log = Path("logs/system.log")
    if not system_log.exists():
        with open(system_log, "w") as f:
            f.write("")

    loop = asyncio.get_event_loop()
    log_collector = LogCollector(log_paths, log_processing_callback, loop=loop)
    log_collector.start()
    
    logger.info("System startup complete")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup components on shutdown."""
    if log_collector:
        log_collector.stop()
    if db_manager:
        await db_manager.close()
    logger.info("System shutdown complete")

# --- API Endpoints ---

@app.get("/login", response_class=HTMLResponse)
async def login_get():
    """Serve the login page."""
    login_path = Path("dashboard/login.html")
    if not login_path.exists():
        return "<h1>Login page not found</h1>"
    with open(login_path, 'r') as f:
        return f.read()

@app.post("/login")
async def login_post(username: str = Form(...), password: str = Form(...)):
    """Handle login form submission."""
    if username in DEMO_USERS and DEMO_USERS[username] == password:
        session_id = f"session_{username}_{id(username)}"
        active_sessions.add(session_id)
        response = JSONResponse(content={"status": "success"})
        response.set_cookie(key="session_id", value=session_id, httponly=True)
        return response
    
    raise HTTPException(status_code=401, detail="Invalid credentials")

@app.get("/logout")
async def logout(session_id: str = Depends(get_current_user)):
    """Handle logout."""
    if session_id in active_sessions:
        active_sessions.remove(session_id)
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie(key="session_id")
    return response

@app.get("/logs", response_class=JSONResponse)
async def get_logs(limit: int = 100, _=Depends(get_current_user)):
    """Get last 100 logs from MySQL."""
    if not db_manager:
        raise HTTPException(status_code=500, detail="Database not initialized")
    
    logs = await db_manager.get_recent_logs(limit)
    # Convert datetimes to strings for JSON
    for log in logs:
        if "timestamp" in log and log["timestamp"]:
            log["timestamp"] = log["timestamp"].isoformat()
        if "created_at" in log and log["created_at"]:
            log["created_at"] = log["created_at"].isoformat()
            
    return logs

@app.get("/alerts", response_class=JSONResponse)
async def get_alerts(limit: int = 50, _=Depends(get_current_user)):
    """Get system alerts from MySQL."""
    if not db_manager:
        raise HTTPException(status_code=500, detail="Database not initialized")
        
    alerts = await db_manager.get_recent_alerts(limit)
    for alert in alerts:
        if "created_at" in alert and alert["created_at"]:
            alert["created_at"] = alert["created_at"].isoformat()
            
    return alerts

@app.get("/health", response_class=JSONResponse)
async def get_health(_=Depends(get_current_user)):
    """Calculate and return system health score."""
    if not db_manager:
        raise HTTPException(status_code=500, detail="Database not initialized")
        
    return await db_manager.calculate_health_score()

@app.get("/patterns", response_class=JSONResponse)
async def get_patterns(_=Depends(get_current_user)):
    """Get all log templates/patterns."""
    if not db_manager:
        raise HTTPException(status_code=500, detail="Database not initialized")
        
    return await db_manager.get_all_templates()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, session_id: Optional[str] = Cookie(None)):
    """WebSocket endpoint for real-time dashboard updates."""
    if not session_id or session_id not in active_sessions:
        await websocket.close(code=1008)
        return
        
    await websocket.accept()
    active_connections.append(websocket)
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        active_connections.remove(websocket)

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Serve the real-time dashboard or redirect to login."""
    session_id = request.cookies.get("session_id")
    if not session_id or session_id not in active_sessions:
        return RedirectResponse(url="/login", status_code=302)
        
    dashboard_path = Path("dashboard/dashboard.html")
    if not dashboard_path.exists():
        return "<h1>Dashboard file not found</h1>"
    
    with open(dashboard_path, 'r') as f:
        return f.read()
