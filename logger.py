# logger.py
import logging
from typing import Dict, Any
import os  # Import the os module

# Ensure logs directory exists
LOGS_DIR = "logs"  # Define directory for logs
if not os.path.exists(LOGS_DIR):
    os.makedirs(LOGS_DIR)

LOG_FILE = os.path.join(LOGS_DIR, "app.log") # Define log file path

# Configure root logger
logging.basicConfig(level=logging.INFO,  # Default level INFO for console output
                    format='%(asctime)s - %(levelname)s - %(module)s - %(message)s')

# Create a FileHandler to write logs to a file
file_handler = logging.FileHandler(LOG_FILE)
file_handler.setLevel(logging.DEBUG) # Log DEBUG level and above to file
file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(module)s - %(message)s') # Optional: Create formatter for file logs (same as console for now)
file_handler.setFormatter(file_formatter) # Apply formatter to file handler

# Get the root logger
_logger = logging.getLogger() # Get root logger (no name specified)
_logger.addHandler(file_handler) # Add the file handler to the root logger


def log_info(message: str, extra: Dict[str, Any] = None) -> None:
    """For general information."""
    if extra:
        message += f" - Extra: {extra}" # Simple string-based extra data for MVP
    _logger.info(message)

def log_error(message: str, extra: Dict[str, Any] = None) -> None:
    """For error conditions."""
    if extra:
        message += f" - Extra: {extra}"
    _logger.error(message)

def log_debug(message: str, extra: Dict[str, Any] = None) -> None:
    """For detailed debugging information."""
    if extra:
        message += f" - Extra: {extra}"
    _logger.debug(message)

def log_warning(message: str, extra: Dict[str, Any] = None) -> None:
    """For potential issues."""
    if extra:
        message += f" - Extra: {extra}"
    _logger.warning(message)