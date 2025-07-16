"""
Centralized logging configuration for the Face Tracking System.
Provides structured logging with rotation, different log levels, and
formatting for better debugging and monitoring.
"""

import os
import sys
import logging
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from pathlib import Path
from typing import Optional

from app.config import settings

class ColoredFormatter(logging.Formatter):
    """Custom formatter to add colors to console output"""
    
    # Color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }
    
    def format(self, record):
        # Add color to levelname
        if record.levelname in self.COLORS:
            record.levelname = f"{self.COLORS[record.levelname]}{record.levelname}{self.COLORS['RESET']}"
        return super().format(record)

def setup_logging(
    log_level: Optional[str] = None,
    log_file: Optional[str] = None,
    console_output: bool = True
) -> logging.Logger:
    """
    Setup centralized logging configuration.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file (optional)
        console_output: Whether to output to console
        
    Returns:
        Configured logger instance
    """
    
    # Use settings defaults if not provided
    log_level = log_level or settings.LOG_LEVEL
    log_file = log_file or settings.LOG_FILE
    
    # Convert string level to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Create logs directory if it doesn't exist
    if log_file:
        log_dir = Path(log_file).parent
        log_dir.mkdir(parents=True, exist_ok=True)
    
    # Create root logger
    logger = logging.getLogger("FaceTrackingSystem")
    logger.setLevel(numeric_level)
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Create formatters
    file_formatter = logging.Formatter(
        fmt='%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    console_formatter = ColoredFormatter(
        fmt='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # Add file handler if log file specified
    if log_file:
        try:
            # Use timed rotating file handler
            file_handler = TimedRotatingFileHandler(
                filename=log_file,
                when='midnight',
                interval=1,
                backupCount=30,  # Keep 30 days of logs
                encoding='utf-8'
            )
            file_handler.setLevel(numeric_level)
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            print(f"Warning: Could not setup file logging: {e}")
    
    # Add console handler if enabled
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(numeric_level)
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
    
    # Add error handler for stderr
    error_handler = logging.StreamHandler(sys.stderr)
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(console_formatter)
    logger.addHandler(error_handler)
    
    return logger

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific module/class.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(f"FaceTrackingSystem.{name}")

def log_request(logger: logging.Logger, method: str, path: str, status_code: int, duration: float):
    """
    Log HTTP request information.
    
    Args:
        logger: Logger instance
        method: HTTP method
        path: Request path
        status_code: Response status code
        duration: Request duration in seconds
    """
    level = logging.INFO
    if status_code >= 400:
        level = logging.WARNING
    if status_code >= 500:
        level = logging.ERROR
    
    logger.log(
        level,
        f"{method} {path} - {status_code} - {duration:.3f}s"
    )

def log_exception(logger: logging.Logger, message: str, exc_info=True):
    """
    Log exception with full traceback.
    
    Args:
        logger: Logger instance
        message: Error message
        exc_info: Whether to include exception info
    """
    logger.error(message, exc_info=exc_info)

def log_face_detection(logger: logging.Logger, camera_id: int, faces_detected: int, processing_time: float):
    """
    Log face detection results.
    
    Args:
        logger: Logger instance
        camera_id: Camera identifier
        faces_detected: Number of faces detected
        processing_time: Processing time in seconds
    """
    logger.info(
        f"Camera {camera_id}: Detected {faces_detected} faces in {processing_time:.3f}s"
    )

def log_authentication(logger: logging.Logger, username: str, success: bool, ip_address: str):
    """
    Log authentication attempts.
    
    Args:
        logger: Logger instance
        username: Username attempting login
        success: Whether authentication was successful
        ip_address: Client IP address
    """
    status = "SUCCESS" if success else "FAILED"
    level = logging.INFO if success else logging.WARNING
    
    logger.log(
        level,
        f"Authentication {status} for user '{username}' from IP {ip_address}"
    )

# Initialize default logger
default_logger = setup_logging()