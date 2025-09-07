"""
Centralized logging configuration for s3tester.

This module provides standardized logging setup with JSON format support
and consistent logger naming conventions.
"""

import json
import logging
import logging.config
import sys
from typing import Dict, Any
from pathlib import Path


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_entry = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
            
        # Add extra fields from record
        for key, value in record.__dict__.items():
            if key not in ["name", "msg", "args", "levelname", "levelno", "pathname", 
                          "filename", "module", "lineno", "funcName", "created", 
                          "msecs", "relativeCreated", "thread", "threadName", 
                          "processName", "process", "getMessage", "exc_info", "exc_text", "stack_info"]:
                log_entry[key] = value
                
        return json.dumps(log_entry)


def setup_logging(
    log_level: str = "INFO",
    json_format: bool = False,
    log_file: str = None
) -> None:
    """
    Setup standardized logging configuration.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_format: If True, use JSON formatter for structured logging
        log_file: Optional log file path for file output
    """
    handlers = {}
    formatters = {}
    
    # Console formatter
    if json_format:
        formatters["json"] = {
            "()": "s3tester.core.logging_config.JSONFormatter"
        }
        console_formatter = "json"
    else:
        formatters["standard"] = {
            "format": "%(asctime)s [%(levelname)8s] %(name)s: %(message)s (%(filename)s:%(lineno)s)"
        }
        console_formatter = "standard"
    
    # Console handler
    handlers["console"] = {
        "class": "logging.StreamHandler",
        "level": log_level,
        "formatter": console_formatter,
        "stream": "ext://sys.stdout"
    }
    
    # File handler (if specified)
    if log_file:
        handlers["file"] = {
            "class": "logging.FileHandler",
            "level": log_level,
            "formatter": "json" if json_format else "standard",
            "filename": log_file,
            "mode": "a"
        }
    
    # Root logger configuration
    root_config = {
        "level": log_level,
        "handlers": list(handlers.keys())
    }
    
    # Logger configuration
    loggers = {
        "s3tester": {
            "level": log_level,
            "handlers": list(handlers.keys()),
            "propagate": False
        },
        "boto3": {
            "level": "WARNING",
            "handlers": list(handlers.keys()),
            "propagate": False
        },
        "botocore": {
            "level": "WARNING", 
            "handlers": list(handlers.keys()),
            "propagate": False
        },
        "urllib3": {
            "level": "WARNING",
            "handlers": list(handlers.keys()),
            "propagate": False
        }
    }
    
    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": formatters,
        "handlers": handlers,
        "root": root_config,
        "loggers": loggers
    }
    
    logging.config.dictConfig(config)


def get_logger(name: str) -> logging.Logger:
    """
    Get a standardized logger instance.
    
    Args:
        name: Logger name, should start with 's3tester.'
        
    Returns:
        Configured logger instance
        
    Example:
        >>> logger = get_logger("s3tester.operations.bucket")
        >>> logger.info("Bucket operation started")
    """
    if not name.startswith("s3tester."):
        name = f"s3tester.{name}"
    return logging.getLogger(name)


def log_operation_start(logger: logging.Logger, operation: str, **kwargs) -> None:
    """
    Log operation start with structured data.
    
    Args:
        logger: Logger instance
        operation: Operation name
        **kwargs: Additional context data
    """
    logger.info(f"Starting {operation}", extra={"operation": operation, "context": kwargs})


def log_operation_success(logger: logging.Logger, operation: str, duration: float, **kwargs) -> None:
    """
    Log operation success with structured data.
    
    Args:
        logger: Logger instance  
        operation: Operation name
        duration: Operation duration in seconds
        **kwargs: Additional context data
    """
    logger.info(
        f"{operation} completed successfully in {duration:.2f}s", 
        extra={"operation": operation, "duration": duration, "status": "success", "context": kwargs}
    )


def log_operation_error(logger: logging.Logger, operation: str, error: Exception, duration: float = None, **kwargs) -> None:
    """
    Log operation error with structured data.
    
    Args:
        logger: Logger instance
        operation: Operation name  
        error: Exception that occurred
        duration: Operation duration in seconds (if available)
        **kwargs: Additional context data
    """
    extra_data = {
        "operation": operation, 
        "error_type": type(error).__name__,
        "error_message": str(error),
        "status": "error",
        "context": kwargs
    }
    if duration is not None:
        extra_data["duration"] = duration
        
    logger.error(f"{operation} failed: {error}", extra=extra_data, exc_info=True)