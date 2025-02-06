# logger.py
import logging
import json
from typing import Dict, Any, Optional
import os
from datetime import datetime
import traceback
import inspect
import threading

# Ensure logs directory exists
LOGS_DIR = "logs"
if not os.path.exists(LOGS_DIR):
    os.makedirs(LOGS_DIR)

# Create separate log files for different purposes
current_date = datetime.now().strftime('%Y%m%d')
LOG_FILE = os.path.join(LOGS_DIR, f"app_{current_date}.log")
API_LOG_FILE = os.path.join(LOGS_DIR, f"api_{current_date}.log")
ERROR_LOG_FILE = os.path.join(LOGS_DIR, f"error_{current_date}.log")
PERF_LOG_FILE = os.path.join(LOGS_DIR, f"performance_{current_date}.log")

class DetailedFormatter(logging.Formatter):
    """Custom formatter that handles missing fields gracefully"""
    def format(self, record):
        # Only process records from our loggers
        if not any(record.name.startswith(prefix) for prefix in ['codemind', 'backend', 'api', 'performance']):
            return super().format(record)
            
        # Add extra_data if not present
        if not hasattr(record, 'extra_data'):
            record.extra_data = {}

        # Format extra data
        try:
            if record.extra_data:
                record.extra_data = json.dumps(record.extra_data, indent=2)
            else:
                record.extra_data = ""
        except:
            record.extra_data = str(getattr(record, 'extra_data', ""))

        # Add function name if not present
        if not hasattr(record, 'function_name'):
            try:
                record.function_name = inspect.currentframe().f_back.f_code.co_name
            except:
                record.function_name = '<unknown>'

        # Add stack trace for errors
        if record.levelno >= logging.ERROR:
            if not hasattr(record, 'stack_info') or not record.stack_info:
                record.stack_info = ''.join(traceback.format_stack()[:-1])
        else:
            record.stack_info = ""

        return super().format(record)

# Configure formatters
console_formatter = logging.Formatter(
    '%(levelname)s - %(message)s'  # Simplified console output
)

file_formatter = DetailedFormatter(
    '%(asctime)s - %(levelname)s - [%(name)s:%(function_name)s] - %(message)s%(extra_data)s%(stack_info)s'
)

# Configure handlers
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(console_formatter)
console_handler.addFilter(lambda record: record.levelno >= logging.WARNING)  # Only show warnings and above in console

file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(file_formatter)

error_handler = logging.FileHandler(ERROR_LOG_FILE, encoding='utf-8')
error_handler.setLevel(logging.ERROR)
error_handler.setFormatter(file_formatter)

api_handler = logging.FileHandler(API_LOG_FILE, encoding='utf-8')
api_handler.setLevel(logging.DEBUG)
api_handler.setFormatter(file_formatter)

perf_handler = logging.FileHandler(PERF_LOG_FILE, encoding='utf-8')
perf_handler.setLevel(logging.INFO)
perf_handler.setFormatter(file_formatter)

# Configure root logger with minimal setup
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
root_logger.handlers = []
root_logger.addHandler(console_handler)

# Create our main logger
codemind_logger = logging.getLogger('codemind')
codemind_logger.setLevel(logging.DEBUG)
codemind_logger.propagate = False  # Don't propagate to root
codemind_logger.addHandler(file_handler)
codemind_logger.addHandler(error_handler)

# Configure specific loggers
api_logger = logging.getLogger('api')
api_logger.setLevel(logging.DEBUG)
api_logger.propagate = False
api_logger.addHandler(api_handler)

perf_logger = logging.getLogger('performance')
perf_logger.setLevel(logging.INFO)
perf_logger.propagate = False
perf_logger.addHandler(perf_handler)

# Disable noisy third-party loggers
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('httpcore').setLevel(logging.WARNING)
logging.getLogger('gradio').setLevel(logging.WARNING)

def format_extra(extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Format extra data with common fields"""
    formatted = {
        'timestamp': datetime.now().isoformat(),
        'process_id': os.getpid(),
        'thread_id': threading.get_ident()
    }
    if extra:
        formatted.update(extra)
    return formatted

def log_api_request(method: str, url: str, headers: Dict, body: Any = None) -> None:
    """Log API request details"""
    api_logger.debug(
        f"API Request: {method} {url}",
        extra={'extra_data': {
            'method': method,
            'url': url,
            'headers': {k: v for k, v in headers.items() if k.lower() != 'authorization'},
            'body': body
        }}
    )

def log_api_response(status_code: int, response_body: Any, duration_ms: float) -> None:
    """Log API response details"""
    api_logger.debug(
        f"API Response: {status_code}",
        extra={'extra_data': {
            'status_code': status_code,
            'duration_ms': duration_ms,
            'body': response_body
        }}
    )

def log_performance(operation: str, duration_ms: float, extra: Dict[str, Any] = None) -> None:
    """Log performance metrics"""
    perf_logger.info(
        f"Performance: {operation} took {duration_ms:.2f}ms",
        extra={'extra_data': format_extra({
            'operation': operation,
            'duration_ms': duration_ms,
            **(extra or {})
        })}
    )

def log_info(message: str, extra: Dict[str, Any] = None) -> None:
    """Enhanced info logging"""
    codemind_logger.info(message, extra={'extra_data': format_extra(extra)})

def log_error(message: str, extra: Dict[str, Any] = None, exc_info: bool = True) -> None:
    """Enhanced error logging"""
    codemind_logger.error(message, exc_info=exc_info, extra={'extra_data': format_extra(extra)})

def log_debug(message: str, extra: Dict[str, Any] = None) -> None:
    """Enhanced debug logging"""
    codemind_logger.debug(message, extra={'extra_data': format_extra(extra)})

def log_warning(message: str, extra: Dict[str, Any] = None) -> None:
    """Enhanced warning logging"""
    codemind_logger.warning(message, extra={'extra_data': format_extra(extra)})

def log_critical(message: str, extra: Dict[str, Any] = None, exc_info: bool = True) -> None:
    """Enhanced critical logging"""
    codemind_logger.critical(message, exc_info=exc_info, extra={'extra_data': format_extra(extra)})