"""Error display and tracking component for CodeMind"""
import logging
from enum import Enum
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import uuid
from dataclasses import dataclass

logger = logging.getLogger(__name__)

class ErrorSeverity(str, Enum):
    """Severity levels for errors"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class ErrorCategory(str, Enum):
    """Categories of errors"""
    VALIDATION = "validation"
    SYSTEM = "system"
    NETWORK = "network"
    SANDBOX = "sandbox"
    UNKNOWN = "unknown"

@dataclass
class ErrorDetails:
    """Details of an error occurrence"""
    message: str
    category: ErrorCategory
    severity: ErrorSeverity
    timestamp: datetime
    error_id: str
    source: str
    details: Optional[Dict[str, Any]] = None
    stack_trace: Optional[str] = None
    suggestion: Optional[str] = None

class ErrorTracker:
    """Tracks and manages error history"""
    
    def __init__(self, max_history: int = 1000):
        """Initialize error tracker"""
        self.errors: List[ErrorDetails] = []
        self.max_history = max_history
        
    def add_error(self, error: ErrorDetails):
        """Add an error to the tracker"""
        self.errors.append(error)
        
        # Maintain history size limit
        if len(self.errors) > self.max_history:
            self.errors = self.errors[-self.max_history:]
            
    def get_errors_by_category(self, category: ErrorCategory) -> List[ErrorDetails]:
        """Get errors of a specific category"""
        return [e for e in self.errors if e.category == category]
        
    def get_errors_by_severity(self, severity: ErrorSeverity) -> List[ErrorDetails]:
        """Get errors of a specific severity"""
        return [e for e in self.errors if e.severity == severity]
        
    def get_recent_errors(self, hours: float = 1, limit: Optional[int] = None) -> List[ErrorDetails]:
        """Get errors from the last N hours"""
        cutoff = datetime.now() - timedelta(hours=hours)
        recent = [e for e in self.errors if e.timestamp > cutoff]
        
        if limit:
            recent = recent[-limit:]
            
        return recent
        
    def clear_history(self):
        """Clear error history"""
        self.errors = []

class ErrorDisplay:
    """Displays and formats errors for different outputs"""
    
    def __init__(self):
        """Initialize error display"""
        self.tracker = ErrorTracker()
        
    def format_error(self, error: ErrorDetails) -> Dict[str, Any]:
        """Format error for JSON output"""
        formatted = {
            "error_id": error.error_id,
            "message": error.message,
            "category": error.category.value,
            "severity": error.severity.value,
            "timestamp": error.timestamp.isoformat(),
            "source": error.source
        }
        
        if error.details:
            formatted["details"] = error.details
        if error.stack_trace:
            formatted["stack_trace"] = error.stack_trace
        if error.suggestion:
            formatted["suggestion"] = error.suggestion
            
        return formatted
        
    def format_for_ui(self, error: ErrorDetails) -> str:
        """Format error for UI display with markdown"""
        severity_emoji = {
            ErrorSeverity.INFO: "ℹ️",
            ErrorSeverity.WARNING: "⚠️",
            ErrorSeverity.ERROR: "❌",
            ErrorSeverity.CRITICAL: "🚨"
        }
        
        lines = [
            f"## {severity_emoji[error.severity]} Error Details",
            f"**Message:** {error.message}",
            f"**Category:** {error.category.value}",
            f"**Severity:** {error.severity.value}",
            f"**Source:** {error.source}",
            f"**Time:** {error.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
        ]
        
        if error.suggestion:
            lines.append(f"\n**Suggestion:** {error.suggestion}")
            
        if error.details:
            lines.append("\n**Details:**")
            for key, value in error.details.items():
                lines.append(f"- {key}: {value}")
                
        if error.stack_trace:
            lines.append("\n**Stack Trace:**")
            lines.append("```")
            lines.append(error.stack_trace)
            lines.append("```")
            
        return "\n".join(lines)
        
    def format_for_log(self, error: ErrorDetails) -> str:
        """Format error for log output"""
        severity_prefix = {
            ErrorSeverity.INFO: "INFO",
            ErrorSeverity.WARNING: "WARN",
            ErrorSeverity.ERROR: "ERROR",
            ErrorSeverity.CRITICAL: "CRITICAL"
        }
        
        lines = [
            f"[{severity_prefix[error.severity]}] {error.message}",
            f"Category: {error.category.value}",
            f"Source: {error.source}",
            f"Time: {error.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
        ]
        
        if error.details:
            lines.append("Details:")
            for key, value in error.details.items():
                lines.append(f"  {key}: {value}")
                
        if error.stack_trace:
            lines.append("Stack Trace:")
            lines.append(error.stack_trace)
            
        return "\n".join(lines)
        
    def get_error_metrics(self) -> Dict[str, Any]:
        """Get error metrics and statistics"""
        recent_errors = self.tracker.get_recent_errors(hours=1)
        
        metrics = {
            "total_errors": len(self.tracker.errors),
            "recent_errors": len(recent_errors),
            "by_severity": {
                severity.value: len(self.tracker.get_errors_by_severity(severity))
                for severity in ErrorSeverity
            },
            "by_category": {
                category.value: len(self.tracker.get_errors_by_category(category))
                for category in ErrorCategory
            }
        }
        
        return metrics

def create_error_details(
    message: str,
    category: ErrorCategory,
    severity: ErrorSeverity,
    source: str,
    details: Optional[Dict[str, Any]] = None,
    stack_trace: Optional[str] = None,
    suggestion: Optional[str] = None
) -> ErrorDetails:
    """Helper function to create error details"""
    return ErrorDetails(
        message=message,
        category=category,
        severity=severity,
        timestamp=datetime.now(),
        error_id=str(uuid.uuid4()),
        source=source,
        details=details,
        stack_trace=stack_trace,
        suggestion=suggestion
    ) 