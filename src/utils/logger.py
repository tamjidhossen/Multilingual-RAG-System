"""
Logging configuration for the Multilingual RAG System
Provides structured logging with color output and file logging
"""

import logging
import sys
from pathlib import Path
from typing import Optional
import colorlog

# Global logger cache
_loggers = {}


def setup_logger(
    name: str,
    level: str = "INFO",
    log_file: Optional[Path] = None,
    format_string: Optional[str] = None,
) -> logging.Logger:
    """
    Set up a logger with both console and file output
    
    Args:
        name: Logger name
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file (optional)
        format_string: Custom format string (optional)
    
    Returns:
        Configured logger instance
    """
    if name in _loggers:
        return _loggers[name]
    
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # Remove existing handlers to avoid duplication
    logger.handlers.clear()
    
    # Default format
    if format_string is None:
        format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Console handler with colors
    console_handler = colorlog.StreamHandler(sys.stdout)
    console_formatter = colorlog.ColoredFormatter(
        fmt="%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'red,bg_white',
        }
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler (if log file specified)
    if log_file:
        # Create log directory if it doesn't exist
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_formatter = logging.Formatter(
            fmt=format_string,
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    # Cache the logger
    _loggers[name] = logger
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get an existing logger or create a new one with default settings
    
    Args:
        name: Logger name
    
    Returns:
        Logger instance
    """
    if name in _loggers:
        return _loggers[name]
    
    # Import settings here to avoid circular imports
    from ..config.settings import Settings
    settings = Settings()
    
    return setup_logger(
        name=name,
        level=settings.LOG_LEVEL,
        log_file=settings.LOG_FILE
    )


class LoggerMixin:
    """
    Mixin class to add logging capability to any class
    """
    
    @property
    def logger(self) -> logging.Logger:
        """Get logger for this class"""
        return get_logger(self.__class__.__name__)


def log_function_call(func):
    """
    Decorator to log function calls with parameters and execution time
    """
    import functools
    import time
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        start_time = time.time()
        
        # Log function entry
        logger.debug(f"Calling {func.__name__} with args={args}, kwargs={kwargs}")
        
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.debug(f"{func.__name__} completed in {execution_time:.3f}s")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"{func.__name__} failed after {execution_time:.3f}s: {e}")
            raise
    
    return wrapper


def log_performance(operation_name: str):
    """
    Context manager to log performance of code blocks
    
    Usage:
        with log_performance("PDF Processing"):
            # Your code here
            pass
    """
    import time
    from contextlib import contextmanager
    
    @contextmanager
    def _log_performance():
        logger = get_logger("performance")
        start_time = time.time()
        logger.info(f"Starting {operation_name}")
        
        try:
            yield
            execution_time = time.time() - start_time
            logger.info(f"Completed {operation_name} in {execution_time:.3f}s")
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Failed {operation_name} after {execution_time:.3f}s: {e}")
            raise
    
    return _log_performance()
