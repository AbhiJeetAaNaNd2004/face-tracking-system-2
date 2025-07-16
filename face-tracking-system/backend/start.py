#!/usr/bin/env python3
"""
Face Tracking System - Startup Script
=====================================

Simple startup script for the Face Tracking System backend.
This script provides an easy way to start the application with
proper configuration and error handling.

Usage:
    python start.py [options]

Options:
    --host HOST         Host to bind to (default: 0.0.0.0)
    --port PORT         Port to bind to (default: 8000)
    --workers WORKERS   Number of worker processes (default: 1)
    --reload            Enable auto-reload for development
    --log-level LEVEL   Log level (default: info)
"""

import os
import sys
import argparse
import uvicorn
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Face Tracking System Backend Server",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Host to bind to"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind to"
    )
    
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Number of worker processes"
    )
    
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for development"
    )
    
    parser.add_argument(
        "--log-level",
        type=str,
        default="info",
        choices=["critical", "error", "warning", "info", "debug", "trace"],
        help="Log level"
    )
    
    parser.add_argument(
        "--env",
        type=str,
        default=".env",
        help="Environment file path"
    )
    
    return parser.parse_args()

def check_environment():
    """Check if environment is properly configured."""
    required_env_vars = ["SECRET_KEY", "DB_HOST", "DB_NAME", "DB_USER"]
    missing_vars = []
    
    for var in required_env_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("Please ensure your .env file is properly configured.")
        return False
    
    return True

def check_dependencies():
    """Check if required dependencies are installed."""
    try:
        import fastapi
        import uvicorn
        import sqlalchemy
        import cv2
        import numpy
        return True
    except ImportError as e:
        print(f"❌ Missing required dependency: {e}")
        print("Please install dependencies with: pip install -r requirements.txt")
        return False

def main():
    """Main entry point."""
    args = parse_args()
    
    print("🚀 Starting Face Tracking System Backend...")
    print(f"   Host: {args.host}")
    print(f"   Port: {args.port}")
    print(f"   Workers: {args.workers}")
    print(f"   Reload: {args.reload}")
    print(f"   Log Level: {args.log_level}")
    print()
    
    # Check environment file
    env_file = Path(args.env)
    if not env_file.exists():
        print(f"⚠️  Environment file {args.env} not found. Using defaults.")
    else:
        print(f"✅ Using environment file: {args.env}")
        # Load environment variables
        from dotenv import load_dotenv
        load_dotenv(env_file)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Check environment
    if not check_environment():
        sys.exit(1)
    
    print("✅ All checks passed. Starting server...")
    print()
    
    # Configure uvicorn settings
    config = {
        "app": "app.main:app",
        "host": args.host,
        "port": args.port,
        "log_level": args.log_level,
        "access_log": True,
    }
    
    if args.reload:
        config["reload"] = True
        config["reload_dirs"] = ["app", "core", "db", "utils", "tasks"]
    else:
        config["workers"] = args.workers
    
    try:
        uvicorn.run(**config)
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"\n❌ Server error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()