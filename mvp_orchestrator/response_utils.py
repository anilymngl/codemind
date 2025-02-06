"""Utility functions for working with standardized response types"""

import json
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import asdict

from .response_types import (
    OrchestrationResult,
    ReasoningOutput,
    SynthesisOutput,
    ErrorDetails,
    HistoryEntry
)

def serialize_response(response: OrchestrationResult) -> Dict[str, Any]:
    """
    Serialize an OrchestrationResult to a JSON-compatible dictionary
    
    Args:
        response: The OrchestrationResult to serialize
        
    Returns:
        Dictionary representation of the response
    """
    def _serialize_datetime(obj: Any) -> Any:
        """Helper to serialize datetime objects"""
        if isinstance(obj, datetime):
            return obj.isoformat()
        return obj
    
    # Convert to dict and handle datetime serialization
    response_dict = asdict(response)
    return json.loads(
        json.dumps(response_dict, default=_serialize_datetime)
    )

def deserialize_response(data: Dict[str, Any]) -> OrchestrationResult:
    """
    Deserialize a dictionary into an OrchestrationResult
    
    Args:
        data: Dictionary containing response data
        
    Returns:
        Reconstructed OrchestrationResult object
    """
    # Parse timestamps
    if 'timestamp' in data:
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
    
    if data.get('error'):
        if 'timestamp' in data['error']:
            data['error']['timestamp'] = datetime.fromisoformat(
                data['error']['timestamp']
            )
    
    # Reconstruct nested objects
    if data.get('reasoning'):
        data['reasoning'] = ReasoningOutput(**data['reasoning'])
    if data.get('synthesis'):
        data['synthesis'] = SynthesisOutput(**data['synthesis'])
    if data.get('error'):
        data['error'] = ErrorDetails(**data['error'])
    
    return OrchestrationResult(**data)

def merge_responses(
    responses: List[OrchestrationResult],
    strategy: str = 'latest'
) -> OrchestrationResult:
    """
    Merge multiple responses into a single response
    
    Args:
        responses: List of responses to merge
        strategy: Merge strategy ('latest', 'first_success', or 'combine')
        
    Returns:
        Merged OrchestrationResult
    """
    if not responses:
        return OrchestrationResult.error_result(
            'MergeError',
            'No responses to merge'
        )
    
    if strategy == 'latest':
        return responses[-1]
    
    if strategy == 'first_success':
        for response in responses:
            if response.success:
                return response
        return responses[-1]
    
    if strategy == 'combine':
        # Combine successful responses
        successful = [r for r in responses if r.success]
        if not successful:
            return responses[-1]
        
        # Merge metadata
        combined_metadata = {}
        for response in successful:
            combined_metadata.update(response.metadata or {})
        
        # Use the latest successful response as base
        latest = successful[-1]
        latest.metadata = combined_metadata
        return latest
    
    raise ValueError(f"Unknown merge strategy: {strategy}")

def filter_sensitive_data(response: OrchestrationResult) -> OrchestrationResult:
    """
    Remove sensitive data from a response
    
    Args:
        response: Response to filter
        
    Returns:
        Filtered response
    """
    filtered = OrchestrationResult(
        success=response.success,
        code=response.code,
        error=response.error,
        metadata=_filter_metadata(response.metadata)
    )
    
    if response.reasoning:
        filtered.reasoning = ReasoningOutput(
            thoughts=response.reasoning.thoughts,
            reasoning=response.reasoning.reasoning,
            metadata=_filter_metadata(response.reasoning.metadata)
        )
    
    if response.synthesis:
        filtered.synthesis = SynthesisOutput(
            code=response.synthesis.code,
            explanation=response.synthesis.explanation,
            metadata=_filter_metadata(response.synthesis.metadata)
        )
    
    return filtered

def _filter_metadata(metadata: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Filter sensitive data from metadata"""
    if not metadata:
        return {}
    
    # List of keys that might contain sensitive data
    sensitive_keys = {
        'api_key', 'key', 'secret', 'password', 'token',
        'auth', 'credential', 'private'
    }
    
    filtered = {}
    for key, value in metadata.items():
        # Skip if key contains sensitive words
        if any(sensitive in key.lower() for sensitive in sensitive_keys):
            continue
        
        # Recursively filter nested dictionaries
        if isinstance(value, dict):
            filtered[key] = _filter_metadata(value)
        else:
            filtered[key] = value
    
    return filtered

def create_error_response(
    error_type: str,
    message: str,
    details: Optional[Dict[str, Any]] = None,
    code: Optional[str] = None
) -> OrchestrationResult:
    """
    Create a standardized error response
    
    Args:
        error_type: Type of error
        message: Error message
        details: Optional error details
        code: Optional code that caused the error
        
    Returns:
        Error response
    """
    return OrchestrationResult.error_result(
        error_type,
        message,
        {
            **(details or {}),
            'error_code': code,
            'timestamp': datetime.now()
        }
    ) 