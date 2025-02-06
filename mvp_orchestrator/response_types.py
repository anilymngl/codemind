from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional
from datetime import datetime
import json

@dataclass
class ReasoningOutput:
    """Output from the Gemini reasoning step"""
    thoughts: List[str]
    reasoning: str
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class SynthesisOutput:
    """Output from the Claude synthesis step"""
    code: str
    explanation: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ErrorDetails:
    """Detailed error information"""
    type: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class OrchestrationResult:
    """Final result from the orchestration process"""
    success: bool
    code: Optional[str] = None
    reasoning: Optional[ReasoningOutput] = None
    synthesis: Optional[SynthesisOutput] = None
    error: Optional[ErrorDetails] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    @classmethod
    def success_result(
        cls,
        code: str,
        reasoning: ReasoningOutput,
        synthesis: SynthesisOutput,
        metadata: Optional[Dict[str, Any]] = None
    ) -> 'OrchestrationResult':
        """Create a successful result"""
        return cls(
            success=True,
            code=code,
            reasoning=reasoning,
            synthesis=synthesis,
            metadata=metadata or {}
        )

    @classmethod
    def error_result(
        cls,
        error_type: str,
        error_message: str,
        error_details: Optional[Dict[str, Any]] = None
    ) -> 'OrchestrationResult':
        """Create an error result"""
        return cls(
            success=False,
            error=ErrorDetails(
                type=error_type,
                message=error_message,
                details=error_details
            )
        )

@dataclass
class HistoryEntry:
    """Entry in the orchestration history"""
    query: str
    result: OrchestrationResult
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

def serialize_response(response: OrchestrationResult) -> Dict[str, Any]:
    """
    Serialize an OrchestrationResult to a JSON-compatible dictionary
    
    Args:
        response: The OrchestrationResult to serialize
        
    Returns:
        Dictionary containing serialized response data
    """
    def _serialize_datetime(dt: datetime) -> str:
        """Serialize datetime to ISO format string"""
        return dt.isoformat()
    
    # Convert to dictionary
    response_dict = asdict(response)
    
    # Handle datetime serialization
    response_dict['timestamp'] = _serialize_datetime(response.timestamp)
    if response.error and response.error.timestamp:
        response_dict['error']['timestamp'] = _serialize_datetime(response.error.timestamp)
        
    return response_dict

def deserialize_response(data: Dict[str, Any]) -> OrchestrationResult:
    """
    Deserialize a dictionary into an OrchestrationResult
    
    Args:
        data: Dictionary containing serialized response data
        
    Returns:
        Deserialized OrchestrationResult
    """
    def _deserialize_datetime(dt_str: str) -> datetime:
        """Deserialize datetime from ISO format string"""
        return datetime.fromisoformat(dt_str)
    
    # Handle datetime deserialization
    if 'timestamp' in data:
        data['timestamp'] = _deserialize_datetime(data['timestamp'])
    if 'error' in data and data['error'] and 'timestamp' in data['error']:
        data['error']['timestamp'] = _deserialize_datetime(data['error']['timestamp'])
        
    # Reconstruct nested objects
    if 'reasoning' in data and data['reasoning']:
        data['reasoning'] = ReasoningOutput(**data['reasoning'])
    if 'synthesis' in data and data['synthesis']:
        data['synthesis'] = SynthesisOutput(**data['synthesis'])
    if 'error' in data and data['error']:
        data['error'] = ErrorDetails(**data['error'])
        
    return OrchestrationResult(**data)

def merge_responses(
    responses: List[OrchestrationResult],
    strategy: str = 'latest'
) -> OrchestrationResult:
    """
    Merge multiple OrchestrationResults based on a strategy
    
    Args:
        responses: List of OrchestrationResults to merge
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
        return max(responses, key=lambda r: r.timestamp)
    elif strategy == 'first_success':
        successes = [r for r in responses if r.success]
        return successes[0] if successes else responses[-1]
    elif strategy == 'combine':
        # Combine successful responses
        successes = [r for r in responses if r.success]
        if not successes:
            return responses[-1]
            
        combined_code = '\n\n'.join(r.code for r in successes if r.code)
        combined_reasoning = ReasoningOutput(
            thoughts=[t for r in successes if r.reasoning for t in r.reasoning.thoughts],
            reasoning='\n\n'.join(r.reasoning.reasoning for r in successes if r.reasoning),
            metadata={'combined': True}
        )
        combined_synthesis = SynthesisOutput(
            code=combined_code,
            explanation='\n\n'.join(r.synthesis.explanation for r in successes if r.synthesis and r.synthesis.explanation),
            metadata={'combined': True}
        )
        
        return OrchestrationResult.success_result(
            code=combined_code,
            reasoning=combined_reasoning,
            synthesis=combined_synthesis,
            metadata={'merge_strategy': 'combine'}
        )
    else:
        raise ValueError(f"Unknown merge strategy: {strategy}")

def filter_sensitive_data(response: OrchestrationResult) -> OrchestrationResult:
    """
    Remove sensitive data from an OrchestrationResult
    
    Args:
        response: The OrchestrationResult to filter
        
    Returns:
        Filtered OrchestrationResult
    """
    # Create a copy to avoid modifying the original
    filtered = deserialize_response(serialize_response(response))
    
    # Filter metadata
    if filtered.metadata:
        filtered.metadata = _filter_metadata(filtered.metadata)
    if filtered.reasoning and filtered.reasoning.metadata:
        filtered.reasoning.metadata = _filter_metadata(filtered.reasoning.metadata)
    if filtered.synthesis and filtered.synthesis.metadata:
        filtered.synthesis.metadata = _filter_metadata(filtered.synthesis.metadata)
    if filtered.error and filtered.error.details:
        filtered.error.details = _filter_metadata(filtered.error.details)
        
    return filtered

def _filter_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Filter sensitive data from metadata dictionary"""
    sensitive_keys = {
        'api_key', 'key', 'secret', 'password', 'token',
        'auth', 'credential', 'private'
    }
    
    return {
        k: '[FILTERED]' if any(s in k.lower() for s in sensitive_keys) else v
        for k, v in metadata.items()
    } 