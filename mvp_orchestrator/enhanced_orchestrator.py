from gemini_integration.gemini_client import GeminiReasoner, GeminiConfig
from claude_integration.claude_client import ClaudeSynthesizer, ClaudeConfig
from typing import Dict, Any, Optional
from logger import log_info, log_error, log_warning, log_debug, log_performance
from mvp_orchestrator.mvp_orchestrator import SimpleMVPOrchestrator # Import SimpleMVPOrchestrator for potential renaming
import asyncio
import time
from dataclasses import dataclass
from typing import List
import logging
from datetime import datetime
from .retry_handler import RetryHandler, RetryConfig, RetryExhaustedError
from mvp_orchestrator.error_types import (
    CodeMindError, OrchestrationError, ReasoningError,
    SynthesisError, ValidationError,
    RateLimitError, ConfigurationError, SandboxError
)
from .response_types import (
    OrchestrationResult, ReasoningOutput,
    SynthesisOutput, HistoryEntry
)
from .secure_sandbox import SandboxConfig

logger = logging.getLogger(__name__)

@dataclass
class OrchestratorConfig:
    """Configuration for the UnifiedOrchestrator"""
    def __init__(
        self,
        gemini_key: str,
        claude_key: str,
        e2b_key: str,  # Add E2B key
        max_retries: int = 3,
        retry_delay: float = 1.0,
        max_history_size: int = 100,
        use_streaming: bool = False,
        use_thinking_model: bool = False,
        rate_limit_config: Optional[Dict[str, Any]] = None,
        retry_config: Optional[RetryConfig] = None,
        sandbox_config: Optional[Dict[str, Any]] = None  # Add sandbox config
    ):
        self.gemini_key = gemini_key
        self.claude_key = claude_key
        self.e2b_key = e2b_key
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.max_history_size = max_history_size
        self.use_streaming = use_streaming
        self.use_thinking_model = use_thinking_model
        self.rate_limit_config = rate_limit_config or {
            'max_tokens_per_minute': 90000,
            'max_requests_per_minute': 60
        }
        
        # Initialize RetryConfig if not provided
        self.retry_config = retry_config or RetryConfig(
            max_retries=max_retries,
            base_delay=retry_delay,
            max_delay=retry_delay * 10.0,  # Set reasonable max delay
            jitter_factor=0.1,
            exponential_base=2.0
        )

        # Initialize SandboxConfig
        sandbox_defaults = {
            'template': 'base',
            'timeout_ms': 10 * 60 * 1000,  # 10 minutes
            'memory_mb': 512,
            'dependencies': None
        }
        sandbox_settings = {**sandbox_defaults, **(sandbox_config or {})}
        self.sandbox_config = SandboxConfig(
            api_key=e2b_key,
            **sandbox_settings
        )
        
        self.validate()
        
    def validate(self):
        """Validate the configuration"""
        if not self.gemini_key or not isinstance(self.gemini_key, str):
            raise ValidationError("Invalid Gemini API key")
        if not self.claude_key or not isinstance(self.claude_key, str):
            raise ValidationError("Invalid Claude API key")
        if not self.e2b_key or not isinstance(self.e2b_key, str):
            raise ValidationError("Invalid E2B API key")
        if self.max_retries < 0:
            raise ValidationError("max_retries must be non-negative")
        if self.retry_delay < 0:
            raise ValidationError("retry_delay must be non-negative")
        if self.max_history_size < 0:
            raise ValidationError("max_history_size must be non-negative")
        # Validate sandbox config
        self.sandbox_config.validate()

class OrchestrationError(Exception):
    """Base exception class for orchestration errors"""
    pass

class ReasoningError(OrchestrationError):
    """Raised when there's an error getting reasoning from Gemini"""
    pass

class SynthesisError(OrchestrationError):
    """Raised when there's an error getting code synthesis from Claude"""
    pass

class UnifiedOrchestrator:
    """Enhanced orchestrator that handles code generation, reasoning,
    rate limiting, and error handling for code generation.
    """
    
    def __init__(self, config: OrchestratorConfig):
        """
        Initialize the orchestrator with configuration
        
        Args:
            config: OrchestratorConfig instance with API keys and settings
        """
        self.config = config
        self.history: List[HistoryEntry] = []
        
        # Initialize retry handler with RetryConfig
        self.retry_handler = RetryHandler(config.retry_config)
        
        try:
            # Initialize Gemini client
            gemini_config = GeminiConfig(
                api_key=config.gemini_key,
                use_thinking_model=config.use_thinking_model,
                rate_limit_per_minute=config.rate_limit_config['max_requests_per_minute'],
                rate_limit_burst=10  # Default burst limit
            )
            self.reasoner = GeminiReasoner(
                gemini_key=config.gemini_key,
                config=gemini_config
            )
            
            # Initialize Claude client
            self.synthesizer = ClaudeSynthesizer(
                claude_key=config.claude_key,
                config=ClaudeConfig(
                    api_key=config.claude_key,
                    stream_response=config.use_streaming,
                    rate_limit_per_minute=config.rate_limit_config['max_requests_per_minute'],
                    rate_limit_burst=10  # Default burst limit
                )
            )
            
        except Exception as e:
            logger.error(f"Failed to initialize clients: {str(e)}")
            raise ConfigurationError(f"Failed to initialize clients: {str(e)}")
            
        logger.info("UnifiedOrchestrator initialized successfully")
        
    async def execute_code_in_sandbox(self, code: str) -> Dict[str, Any]:
        """Execute code in the secure sandbox environment"""
        from .secure_sandbox import SecureSandbox
        try:
            result = await SecureSandbox.quick_execute(code, self.config.sandbox_config)
            return result
        except Exception as e:
            logger.error(f"Error executing code in sandbox: {str(e)}")
            raise SandboxError(f"Error executing code in sandbox: {str(e)}")

    async def run_sandbox(self, code: str) -> Dict[str, Any]:
        """
        Execute code in the sandbox environment independently of the main query processing flow.
        This method is exposed for UI-triggered sandbox execution.

        Args:
            code: The code to execute in the sandbox

        Returns:
            Dictionary containing:
                - success: bool indicating if execution was successful
                - output: stdout from the code execution
                - error: error message if execution failed
                - execution_time_ms: execution time in milliseconds
        """
        if not code or not code.strip():
            log_warning("Empty code received for sandbox execution")
            return {
                'success': False,
                'output': None,
                'error': "Code cannot be empty",
                'execution_time_ms': 0
            }

        try:
            log_info("Starting sandbox execution...", extra={
                'code_length': len(code)
            })
            
            sandbox_start = time.time()
            execution_result = await self.execute_code_in_sandbox(code)
            sandbox_duration = (time.time() - sandbox_start) * 1000
            
            log_performance("sandbox_execution", sandbox_duration, {
                'success': execution_result.get('success', False),
                'error': execution_result.get('error')
            })

            if not execution_result.get('success', False):
                log_warning("Sandbox execution failed", extra={
                    'error': execution_result.get('error')
                })
            else:
                log_info("Sandbox execution completed successfully")

            return {
                'success': execution_result.get('success', False),
                'output': execution_result.get('output'),
                'error': execution_result.get('error'),
                'execution_time_ms': sandbox_duration
            }

        except Exception as e:
            log_error("Error during sandbox execution", exc_info=True)
            return {
                'success': False,
                'output': None,
                'error': f"Sandbox execution failed: {str(e)}",
                'execution_time_ms': (time.time() - sandbox_start) * 1000
            }
        
    async def process_query(self, query: str, context: Optional[Dict] = None) -> OrchestrationResult:
        """Process a query through the orchestration pipeline"""
        start_time = time.time()
        log_info("Starting query processing", extra={
            'query_length': len(query),
            'has_context': bool(context)
        })
        
        if not query or not query.strip():
            log_warning("Empty query received")
            return OrchestrationResult.error_result(
                "ValidationError",
                "Query cannot be empty",
                {'query': query}
            )
            
        try:
            # 1. Get reasoning from Gemini with retry
            log_info("Getting reasoning from Gemini...")
            reasoning_start = time.time()
            reasoning_output = await self.retry_handler.execute(
                self.reasoner.get_reasoning,
                query,
                context=context
            )
            reasoning_duration = (time.time() - reasoning_start) * 1000
            log_performance("reasoning_phase", reasoning_duration, {
                'success': bool(reasoning_output),
                'num_requirements': len(reasoning_output.get('technical_requirements', [])),
                'num_strategy': len(reasoning_output.get('implementation_strategy', []))
            })

            # 2. Get code synthesis from Claude with retry
            log_info("Getting synthesis from Claude...")
            synthesis_start = time.time()
            synthesis_output = await self.retry_handler.execute(
                self.synthesizer.generate_code,
                query,
                reasoning_data=reasoning_output,
                context=context
            )
            synthesis_duration = (time.time() - synthesis_start) * 1000
            log_performance("synthesis_phase", synthesis_duration, {
                'success': bool(synthesis_output),
                'code_length': len(synthesis_output.get('code_completion', '')),
            })

            # 3. Create success result (without sandbox execution)
            total_duration = (time.time() - start_time) * 1000
            result = OrchestrationResult.success_result(
                code=synthesis_output['code_completion'],
                reasoning=ReasoningOutput(
                    thoughts=reasoning_output.get('thoughts', []),
                    reasoning=reasoning_output.get('reasoning', ''),
                    metadata=reasoning_output.get('metadata', {})
                ),
                synthesis=SynthesisOutput(
                    code=synthesis_output['code_completion'],
                    explanation=synthesis_output.get('explanation'),
                    metadata=synthesis_output.get('metadata', {})
                ),
                metadata={
                    'processing_time': total_duration,
                    'context': context,
                    'use_streaming': self.config.use_streaming,
                    'use_thinking_model': self.config.use_thinking_model,
                    'execution_result': None,  # No sandbox execution in this flow
                    'phase_durations': {
                        'reasoning_ms': reasoning_duration,
                        'synthesis_ms': synthesis_duration,
                        'sandbox_ms': 0  # No sandbox execution in this flow
                    }
                }
            )

            log_info("Query processing completed successfully", extra={
                'total_duration_ms': total_duration,
                'phases': {
                    'reasoning_ms': reasoning_duration,
                    'synthesis_ms': synthesis_duration,
                    'sandbox_ms': 0  # No sandbox execution in this flow
                }
            })
            return result
            
        except RetryExhaustedError as e:
            # Extract the original error from RetryExhaustedError
            original_error = e.last_error
            log_error("Retry exhausted", extra={
                'original_error_type': type(original_error).__name__,
                'retries': self.config.max_retries,
                'duration_ms': (time.time() - start_time) * 1000
            })
            # Create error result with the original error type
            return OrchestrationResult.error_result(
                type(original_error).__name__,  # Use the original error type
                str(original_error),
                getattr(original_error, 'details', None)
            )
                
        except (RateLimitError, ReasoningError, SynthesisError, ValidationError, SandboxError) as e:
            # Handle known business exceptions directly
            log_error(f"Business exception caught", extra={
                'error_type': type(e).__name__,
                'error_message': str(e),
                'duration_ms': (time.time() - start_time) * 1000
            })
            return OrchestrationResult.error_result(
                type(e).__name__,  # Use the exact error type name
                str(e),
                getattr(e, 'details', None)
            )
            
        except Exception as e:
            # Handle unexpected errors
            log_error("Unexpected error during processing", exc_info=True, extra={
                'error_type': type(e).__name__,
                'duration_ms': (time.time() - start_time) * 1000
            })
            return OrchestrationResult.error_result(
                "UnexpectedError",
                f"An unexpected error occurred: {str(e)}"
            )
    
    def _handle_error(self, error: Exception) -> OrchestrationResult:
        """Handle different types of errors and create appropriate error results"""
        logger.error(f"Entering _handle_error with error type: {type(error)}")
        if isinstance(error, RateLimitError):
            result = OrchestrationResult.error_result(
                "RateLimitError",
                str(error),
                {'retry_after': getattr(error, 'retry_after', None)}
            )
        elif isinstance(error, ReasoningError):
            result = OrchestrationResult.error_result(
                "ReasoningError",
                str(error),
                getattr(error, 'details', None)
            )
        elif isinstance(error, SynthesisError):
            result = OrchestrationResult.error_result(
                "SynthesisError",
                str(error),
                getattr(error, 'details', None)
            )
        elif isinstance(error, ValidationError):
            result = OrchestrationResult.error_result(
                "ValidationError",
                str(error),
                getattr(error, 'details', None)
            )
        else:
            logger.exception("Unexpected error during processing")
            result = OrchestrationResult.error_result(
                "UnexpectedError",
                f"An unexpected error occurred: {str(error)}"
            )
        logger.debug(f"_handle_error returning result with result_type: {result.error.type}")
        return result
    
    def _update_history(self, query: str, result: OrchestrationResult):
        """Update history with new entry and maintain history size"""
        self.history.append(HistoryEntry(
            query=query,
            result=result,
            metadata={
                'timestamp': datetime.now(),
                'use_streaming': self.config.use_streaming,
                'use_thinking_model': self.config.use_thinking_model
            }
        ))
        
        # Maintain history size limit
        if len(self.history) > self.config.max_history_size:
            self.history = self.history[-self.config.max_history_size:]
            
    def get_history(
        self,
        limit: Optional[int] = None,
        success_only: bool = False
    ) -> List[HistoryEntry]:
        """Get history entries with optional filtering"""
        entries = self.history
        if success_only:
            entries = [e for e in entries if e.result.success]
        if limit:
            entries = entries[-limit:]
        return entries