#!/usr/bin/env python3
"""
Port management utility for the Intelligent Log Analysis System.
Helps check and manage port 8000 usage.
"""

import subprocess
import sys
import re


def check_port_usage(port=8000):
    """Check what's using the specified port."""
    try:
        # Run netstat to check port usage
        result = subprocess.run(
            ["netstat", "-ano"], 
            capture_output=True, 
            text=True, 
            timeout=10
        )
        
        if result.returncode != 0:
            print(f"❌ Failed to check port usage: {result.stderr}")
            return None
        
        # Look for the port in the output
        lines = result.stdout.split('\n')
        port_lines = [line for line in lines if f":{port}" in line and "LISTENING" in line]
        
        if not port_lines:
            print(f"✅ Port {port} is available")
            return None
        
        print(f"⚠️  Port {port} is in use:")
        for line in port_lines:
            parts = line.split()
            if len(parts) >= 5:
                protocol = parts[0]
                local_addr = parts[1]
                state = parts[3]
                pid = parts[4]
                print(f"   {protocol} {local_addr} {state} (PID: {pid})")
        
        return port_lines
        
    except subprocess.TimeoutExpired:
        print("❌ Timeout checking port usage")
        return None
    except Exception as e:
        print(f"❌ Error checking port usage: {e}")
        return None


def kill_process_on_port(port=8000):
    """Kill processes using the specified port."""
    port_lines = check_port_usage(port)
    
    if not port_lines:
        return
    
    print(f"\n🔧 Attempting to free port {port}...")
    
    for line in port_lines:
        parts = line.split()
        if len(parts) >= 5:
            pid = parts[4]
            try:
                # Kill the process
                subprocess.run(["taskkill", "/F", "/PID", pid], 
                             capture_output=True, check=True)
                print(f"✅ Killed process {pid}")
            except subprocess.CalledProcessError as e:
                print(f"❌ Failed to kill process {pid}: {e}")
            except Exception as e:
                print(f"❌ Error killing process {pid}: {e}")
    
    # Check again
    print(f"\n🔍 Checking port {port} again...")
    check_port_usage(port)


def main():
    """Main function."""
    print("🔍 Port Management Utility")
    print("=" * 30)
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--kill":
            kill_process_on_port(8000)
        elif sys.argv[1] == "--check":
            check_port_usage(8000)
        elif sys.argv[1].startswith("--port="):
            port = int(sys.argv[1].split("=")[1])
            check_port_usage(port)
        else:
            print("Usage:")
            print("  python check_port.py --check     # Check port 8000")
            print("  python check_port.py --kill      # Kill processes on port 8000")
            print("  python check_port.py --port=8001 # Check specific port")
    else:
        check_port_usage(8000)
        print("\nOptions:")
        print("  --check  : Check port usage")
        print("  --kill   : Kill processes using port 8000")
        print("  --port=N : Check specific port number")


if __name__ == "__main__":
    main()