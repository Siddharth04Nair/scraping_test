"""
Logger Helper - Centralized logging configuration
"""

import logging
import sys
from typing import Optional


def setup_logger(
    name: str,
    level: Optional[int] = None,
    log_file: Optional[str] = None,
) -> logging.Logger:
    """
    Set up a logger with consistent formatting.
    
    Args:
        name: Logger name (usually __name__)
        level: Logging level (default: INFO)
        log_file: Optional file path to write logs to
        
    Returns:
        Configured logger instance
    """
    if level is None:
        level = logging.INFO
    
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger
    
    # Create formatter
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler with UTF-8 encoding
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    
    # Handle encoding issues on Windows
    if sys.platform == 'win32':
        try:
            console_handler.stream.reconfigure(encoding='utf-8')
        except AttributeError:
            # Fallback for older Python versions
            pass
    
    logger.addHandler(console_handler)
    
    # Optional file handler
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get or create a logger instance.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Logger instance
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        return setup_logger(name)
    return logger