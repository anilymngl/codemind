"""Error types for CodeMind"""
from typing import Optional, Any, Dict

class CodeMindError(Exception):
    """Base exception class for all CodeMind errors"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(message)

class OrchestrationError(CodeMindError):
    """Base class for orchestration-related errors"""
    pass

class ReasoningError(OrchestrationError):
    """Raised when there's an error getting reasoning from Gemini"""
    pass

class SynthesisError(OrchestrationError):
    """Raised when there's an error getting code synthesis from Claude"""
    pass

class ValidationError(CodeMindError):
    """Raised when there's an error validating input or output"""
    pass

class ConfigurationError(CodeMindError):
    """Raised when there's an error in configuration"""
    pass

class APIError(CodeMindError):
    """Base class for API-related errors"""
    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response: Optional[Dict[str, Any]] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, details=details)
        self.status_code = status_code
        self.response = response

class GeminiAPIError(APIError):
    """Raised when there's an error calling the Gemini API"""
    pass

class ClaudeAPIError(APIError):
    """Raised when there's an error calling the Claude API"""
    pass

class RateLimitError(APIError):
    """Raised when API rate limits are exceeded"""
    def __init__(
        self,
        message: str,
        retry_after: Optional[float] = None,
        status_code: Optional[int] = None,
        response: Optional[Dict[str, Any]] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, status_code, response, details)
        self.retry_after = retry_after

class SandboxError(CodeMindError):
    """Raised when there's an error in sandbox code execution"""
    pass 