import time
import functools
import asyncio
from datetime import datetime
from typing import Callable, Optional

# Import the logger
from src.utils.logger import app_logger

def timing_decorator(func: Optional[Callable] = None, *, log_level="info", description: str = None):
    """
    Decorator to measure and log function execution time.
    
    Supports both synchronous and asynchronous functions.
    
    Args:
        func: The function to be decorated
        log_level: Log level to use ('debug', 'info', 'warning', 'error')
        description: Custom description for the log message
    
    Usage:
        @timing_decorator
        def function_name():
            ...
            
        @timing_decorator(log_level='debug', description='Custom operation name')
        async def async_function():
            ...
    """
    def decorator(fn):
        @functools.wraps(fn)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            func_name = fn.__qualname__
            prefix = description or func_name
            
            getattr(app_logger, log_level.lower())(f"Starting {prefix}")
            
            try:
                result = await fn(*args, **kwargs)
                
                elapsed = time.time() - start_time
                getattr(app_logger, log_level.lower())(f"{prefix} completed in {elapsed:.3f}s")
                
                return result
            except Exception as e:
                elapsed = time.time() - start_time
                app_logger.error(f"{prefix} failed after {elapsed:.3f}s: {str(e)}")
                raise
        
        @functools.wraps(fn)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            func_name = fn.__qualname__
            prefix = description or func_name
            
            getattr(app_logger, log_level.lower())(f"Starting {prefix}")
            
            try:
                result = fn(*args, **kwargs)
                
                elapsed = time.time() - start_time
                getattr(app_logger, log_level.lower())(f"{prefix} completed in {elapsed:.3f}s")
                
                return result
            except Exception as e:
                elapsed = time.time() - start_time
                app_logger.error(f"{prefix} failed after {elapsed:.3f}s: {str(e)}")
                raise
        
        # Select appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(fn):
            return async_wrapper
        return sync_wrapper
    
    # Handle both @timing_decorator and @timing_decorator(...)
    return decorator(func) if func else decorator
