import logging
import os
import sys
from datetime import datetime
from typing import Optional

class Logger:
    """Production-grade logging utility for standardized log management with AWS Lambda support."""
    
    # Log levels as class attributes for easy access
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL
    
    def __init__(
        self,
        name: str,
        level: int = logging.INFO,
        log_file: Optional[str] = None,
        console: bool = True,
        format_str: str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ):
        """
        Initialize the logger with configurable output destinations and format.
        
        Args:
            name: Logger name (typically module or class name)
            level: Minimum log level to record
            log_file: Optional file path for logs
            console: Whether to output logs to console
            format_str: Log format string
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        self.logger.propagate = False  # Avoid duplicate logs
        
        # Create formatter
        formatter = logging.Formatter(format_str)
        
        # Clear any existing handlers to prevent duplicates
        self.logger.handlers.clear()
        
        # Add console handler if requested
        if console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
        
        # Add file handler if log file specified
        if log_file:
            # Check if running in AWS Lambda environment
            if 'AWS_LAMBDA_FUNCTION_NAME' in os.environ:
                # Use /tmp directory in Lambda (the only writable directory)
                if log_file.startswith('/'):
                    # Absolute path provided - extract just the filename
                    log_filename = os.path.basename(log_file)
                else:
                    # Relative path - extract just the filename to be safe
                    log_filename = os.path.basename(log_file)
                
                log_file_path = f"/tmp/{log_filename}"
            else:
                # Local environment - use the specified path
                log_file_path = log_file
                # Ensure directory exists (not needed for /tmp in Lambda)
                log_dir = os.path.dirname(os.path.abspath(log_file_path))
                os.makedirs(log_dir, exist_ok=True)
            
            try:
                file_handler = logging.FileHandler(log_file_path)
                file_handler.setFormatter(formatter)
                self.logger.addHandler(file_handler)
            except (OSError, IOError) as e:
                # Fall back to console-only logging if file logging fails
                console_handler = logging.StreamHandler(sys.stderr)
                console_handler.setFormatter(formatter)
                self.logger.addHandler(console_handler)
                self.logger.warning(f"File logging failed, falling back to console: {str(e)}")
    
    def debug(self, message: str, *args, **kwargs):
        """Log debug message."""
        self.logger.debug(message, *args, **kwargs)
    
    def info(self, message: str, *args, **kwargs):
        """Log info message."""
        self.logger.info(message, *args, **kwargs)
    
    def warning(self, message: str, *args, **kwargs):
        """Log warning message."""
        self.logger.warning(message, *args, **kwargs)
    
    def error(self, message: str, *args, **kwargs):
        """Log error message."""
        self.logger.error(message, *args, **kwargs)
    
    def exception(self, message: str, *args, **kwargs):
        """Log exception with traceback."""
        self.logger.exception(message, *args, **kwargs)


# Determine if we're in AWS Lambda environment
in_lambda = 'AWS_LAMBDA_FUNCTION_NAME' in os.environ

# Create default application logger with environment-appropriate settings
app_logger = Logger(
    name="pdf_llm_backend",
    level=logging.INFO,
    # Use simple filename in Lambda, normal path otherwise
    log_file="app.log" if in_lambda else "logs/app.log"
)

# Log environment information
app_logger.info(f"Logger initialized in {'AWS Lambda' if in_lambda else 'local'} environment")
