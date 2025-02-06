import asyncio
import random
import logging
from typing import TypeVar, Callable, Any, Optional, Union
from dataclasses import dataclass
import aiohttp  # For network-related exceptions
import asyncio.exceptions  # For timeout exceptions
import time
from logger import log_info, log_debug, log_warning, log_error, log_performance

# Import our business exceptions
from .error_types import RateLimitError, ReasoningError, SynthesisError

logger = logging.getLogger(__name__)

T = TypeVar('T')  # Generic type for the return value

@dataclass
class RetryConfig:
    """Configuration for retry behavior
    
    Attributes:
        max_retries: Maximum number of retry attempts before giving up
        base_delay: Initial delay between retries in seconds
        max_delay: Maximum delay between retries in seconds
        jitter_factor: Random jitter as a fraction of delay to avoid thundering herd
        exponential_base: Base for exponential backoff calculation
    """
    max_retries: int = 3  #: Maximum number of retry attempts
    base_delay: float = 1.0  #: Base delay in seconds
    max_delay: float = 10.0  #: Maximum delay in seconds
    jitter_factor: float = 0.1  #: Jitter as a fraction of delay
    exponential_base: float = 2.0  #: Base for exponential backoff
    
    def validate(self):
        """Validate retry configuration"""
        log_debug("Validating retry configuration...")
        if self.max_retries < 0:
            log_error("Invalid max_retries value", extra={'max_retries': self.max_retries})
            raise ValueError("max_retries must be non-negative")
        if self.base_delay <= 0:
            log_error("Invalid base_delay value", extra={'base_delay': self.base_delay})
            raise ValueError("base_delay must be positive")
        if self.max_delay < self.base_delay:
            log_error("Invalid max_delay value", extra={
                'max_delay': self.max_delay,
                'base_delay': self.base_delay
            })
            raise ValueError("max_delay must be greater than or equal to base_delay")
        if not 0 <= self.jitter_factor <= 1:
            log_error("Invalid jitter_factor value", extra={'jitter_factor': self.jitter_factor})
            raise ValueError("jitter_factor must be between 0 and 1")
        if self.exponential_base <= 1:
            log_error("Invalid exponential_base value", extra={'exponential_base': self.exponential_base})
            raise ValueError("exponential_base must be greater than 1")
        log_debug("Retry configuration validated successfully")

class RetryExhaustedError(Exception):
    """Raised when all retry attempts have been exhausted
    
    Attributes:
        message: Description of the error
        last_error: The last exception that caused the retry to fail
        attempt_count: Number of attempts made before giving up
    """
    def __init__(
        self,
        message: str,
        last_error: Optional[Exception] = None,
        attempt_count: Optional[int] = None
    ):
        self.last_error = last_error
        self.attempt_count = attempt_count
        self.details = {
            'last_error': str(last_error) if last_error else None,
            'attempt_count': attempt_count
        }
        super().__init__(message)

# Define retryable exceptions
RetryableError = Union[
    aiohttp.ClientError,  # Network-related errors
    asyncio.TimeoutError,  # Timeout errors
    ConnectionError,  # General connection errors
    TimeoutError,  # Another form of timeout
    OSError,  # System-level I/O errors
    RateLimitError,  # Rate limit errors (retryable)
    ReasoningError,  # Reasoning errors (retryable)
    SynthesisError  # Synthesis errors (retryable)
]

class RetryHandler:
    """Handles retrying operations with exponential backoff and jitter
    
    This class provides a robust retry mechanism for async operations that may fail
    transiently. It implements exponential backoff with jitter to help distribute
    retry attempts and avoid thundering herd problems.
    
    Attributes:
        config: Configuration parameters for retry behavior
    """
    
    def __init__(self, config: RetryConfig):
        """Initialize the retry handler
        
        Args:
            config: Configuration parameters for retry behavior
        """
        self.config = config
        self.config.validate()
        log_info("Initialized retry handler", extra={
            'max_retries': config.max_retries,
            'base_delay': config.base_delay,
            'max_delay': config.max_delay
        })
        
    def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay with exponential backoff and jitter
        
        Args:
            attempt: The current attempt number (0-based)
            
        Returns:
            The calculated delay in seconds
        """
        # Calculate base exponential delay
        delay = min(
            self.config.base_delay * (self.config.exponential_base ** attempt),
            self.config.max_delay
        )
        
        # Add jitter
        jitter = random.uniform(
            -delay * self.config.jitter_factor,
            delay * self.config.jitter_factor
        )
        
        delay = max(0, delay + jitter)
        
        log_debug("Calculated retry delay", extra={
            'attempt': attempt,
            'base_delay': delay,
            'jitter': jitter,
            'final_delay': delay
        })
        return delay
    
    async def execute(
        self,
        operation: Callable[..., Any],
        *args,
        **kwargs
    ) -> Any:
        """Execute an operation with retry logic
        
        This method will attempt to execute the given operation, retrying on failure
        with exponential backoff and jitter. It handles both network-related errors
        and business exceptions like RateLimitError, ReasoningError, and SynthesisError.
        
        Args:
            operation: The async function to execute
            *args: Positional arguments for the operation
            **kwargs: Keyword arguments for the operation
            
        Returns:
            The result of the operation if successful
            
        Raises:
            The original exception after retries are exhausted
            Exception: Any unhandled exception from the operation
        """
        start_time = time.time()
        log_info("Starting execution with retry", extra={
            'operation': operation.__name__,
            'max_retries': self.config.max_retries
        })
        
        last_error = None
        operation_name = getattr(operation, '__name__', str(operation))
        
        logger.debug(
            f"Starting execution of {operation_name} with max {self.config.max_retries} retries"
        )
        
        # Try up to max_retries + 1 times (initial try + retries)
        for attempt in range(self.config.max_retries + 1):
            try:
                if attempt > 0:
                    delay = self._calculate_delay(attempt - 1)  # Adjust attempt for delay calculation
                    log_info(f"Retry attempt {attempt}", extra={
                        'delay': delay,
                        'operation': operation_name
                    })
                    await asyncio.sleep(delay)
                
                operation_start = time.time()
                result = await operation(*args, **kwargs)
                operation_duration = (time.time() - operation_start) * 1000
                
                log_performance(f"retry_operation_{operation_name}", operation_duration, {
                    'attempt': attempt,
                    'success': True
                })
                
                if attempt > 0:
                    log_info(
                        f"Successfully executed {operation_name} "
                        f"after {attempt + 1} attempts"
                    )
                total_duration = (time.time() - start_time) * 1000
                log_info("Operation completed successfully", extra={
                    'operation': operation_name,
                    'attempts': attempt + 1,
                    'total_duration_ms': total_duration
                })
                return result
                
            except (aiohttp.ClientError, asyncio.TimeoutError, ConnectionError,
                    TimeoutError, OSError, RateLimitError, ReasoningError,
                    SynthesisError) as e:
                last_error = e
                error_type = type(e).__name__
                log_warning(
                    f"{error_type} in {operation_name} "
                    f"(attempt {attempt + 1}/{self.config.max_retries + 1}): {str(e)}"
                )
                
                # If this was the last attempt, wrap the error in RetryExhaustedError
                if attempt == self.config.max_retries:
                    log_error(
                        f"Retry limit exceeded for {operation_name} with {error_type}: {str(e)}"
                    )
                    total_duration = (time.time() - start_time) * 1000
                    log_error("Retry attempts exhausted", exc_info=True, extra={
                        'operation': operation_name,
                        'total_attempts': attempt + 1,
                        'total_duration_ms': total_duration,
                        'final_error_type': error_type
                    })
                    raise RetryExhaustedError(
                        f"Operation {operation_name} failed after {attempt + 1} attempts",
                        last_error=e,
                        attempt_count=attempt + 1
                    ) from e
                    
            except Exception as e:
                # Log unexpected errors and re-raise immediately
                log_error(
                    f"Unexpected error in {operation_name}: {str(e)}",
                    exc_info=True
                )
                raise 