# claude_integration/claude_client.py
import asyncio
import os
import logging
import time
from typing import Dict, List, Optional, Any
from logger import log_info, log_error, log_debug, log_warning, log_performance  # Added log_performance
from mvp_orchestrator.reasoning_parser import StructuredReasoning
from anthropic import AsyncAnthropic
from anthropic.types import Message
from dataclasses import dataclass
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)
from mvp_orchestrator.error_types import (
    ClaudeAPIError,
    RateLimitError,
    ValidationError
)
from langchain.output_parsers import StructuredOutputParser
from models.pydantic_schemas import ClaudeSynthesisResult
import aiohttp
from langchain_core.utils.json import parse_json_markdown  # Add this import

# Configure basic logger - adjust level as needed
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(module)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class ClaudeConfig:
    """Configuration for Claude client"""
    api_key: str
    model: str = "claude-3-5-sonnet-20241022"
    temperature: float = 0.7
    top_p: float = 0.8
    max_tokens: int = 4096
    rate_limit_per_minute: int = 50
    rate_limit_burst: int = 10
    stream_response: bool = False

class RateLimiter:
    """Token bucket rate limiter"""
    
    def __init__(self, rate_per_minute: int, burst_limit: int):
        self.rate = rate_per_minute / 60.0  # Convert to per second
        self.burst_limit = burst_limit
        self.tokens = burst_limit
        self.last_update = time.monotonic()
        self.lock = asyncio.Lock()
        
    async def acquire(self):
        """Acquire a token, waiting if necessary"""
        async with self.lock:
            while True:
                now = time.monotonic()
                time_passed = now - self.last_update
                self.tokens = min(
                    self.burst_limit,
                    self.tokens + time_passed * self.rate
                )
                self.last_update = now
                
                if self.tokens >= 1:
                    self.tokens -= 1
                    return True
                    
                # Calculate wait time
                wait_time = (1 - self.tokens) / self.rate
                logger.warning(f"Rate limit reached, waiting {wait_time:.2f}s")
                await asyncio.sleep(wait_time)
            return False

    async def get_retry_after(self):
        """Get the retry-after time in seconds"""
        async with self.lock:
            now = time.monotonic()
            time_passed = now - self.last_update
            wait_time = (1 - self.tokens) / self.rate
            return wait_time

class ClaudeSynthesizer:
    """Enhanced Claude client for code synthesis"""
    
    def __init__(self, claude_key: str, config: Optional[ClaudeConfig] = None):
        """Initialize Claude client with configuration"""
        if not claude_key:
            raise ValidationError("Claude API key is required")
            
        self.config = config or ClaudeConfig(api_key=claude_key)
        self.rate_limiter = RateLimiter(
            self.config.rate_limit_per_minute,
            self.config.rate_limit_burst
        )
        
        # Initialize Claude
        try:
            self.client = AsyncAnthropic(api_key=self.config.api_key)
        except Exception as e:
            raise ClaudeAPIError("Failed to initialize Claude", details={'error': str(e)})
            
        # Initialize StructuredOutputParser
        response_schemas = [
            {
                "name": "code_completion",
                "type": "string",
                "description": "Generated code snippet"
            },
            {
                "name": "explanation",
                "type": "string",
                "description": "Explanation of the code"
            },
            {
                "name": "sandbox_config",
                "type": "object",
                "description": "Sandbox configuration",
                "properties": {
                    "template": {"type": "string"},
                    "timeout_ms": {"type": "integer"},
                    "memory_mb": {"type": "integer"},
                    "dependencies": {
                        "type": "array",
                        "items": {"type": "string"}
                    }
                }
            },
            {
                "name": "metadata",
                "type": "array",
                "description": "Optional metadata items",
                "items": {
                    "type": "object",
                    "properties": {
                        "key": {"type": "string"},
                        "value": {"type": "string"}
                    }
                }
            },
            {
                "name": "version",
                "type": "string",
                "description": "Synthesis version"
            }
        ]
        logger.debug(f"Response schemas defined: {[schema['name'] for schema in response_schemas]}")
        self.output_parser = StructuredOutputParser(response_schemas=response_schemas)
        
    def _prepare_message_params(
        self,
        query: str,
        reasoning_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Prepare message parameters for Claude API request"""
        # Construct the system prompt
        system_prompt = f"""You are a helpful AI code synthesis assistant. Please generate Python code based on the user request.

REQUEST: {query}

RESPONSE FORMAT:
You must respond with valid JSON enclosed in a markdown code block. Do not include any text outside the code block.

Example format:
```json
{{
  "code_completion": "<generated code>",
  "explanation": "<explanation of code>",
  "sandbox_config": {{
    "template": "python3",
    "timeout_ms": 1000,
    "memory_mb": 256,
    "dependencies": ["dep1", "dep2"]
  }},
  "metadata": [
    {{
      "key": "example_key",
      "value": "example_value"
    }}
  ],
  "version": "2.0.0"
}}
```

REQUIREMENTS:
1. Response MUST be valid JSON inside a markdown code block (```json)
2. ALL fields are required and must match the exact names shown
3. "code_completion" must be a non-empty string containing the generated code
4. "explanation" must be a non-empty string explaining the code
5. "sandbox_config" is optional but must follow the structure shown if present
6. "metadata" must be an array of objects with "key" and "value" fields
7. Do not include any explanation or text outside the JSON block

REASONING DATA:
{reasoning_data}
"""

        # Add context if provided
        if context:
            system_prompt += f"\n\nAdditional Context:\n{context}"

        return {
            "system": system_prompt,
            "messages": [{"role": "user", "content": system_prompt}],
            "model": self.config.model,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
            "stream": self.config.stream_response
        }
        
    @retry(
        retry=retry_if_exception_type((RateLimitError, ConnectionError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def generate_code(
        self,
        query: str,
        reasoning_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate code based on reasoning data"""
        start_time = time.time()
        log_info("Starting code generation", extra={
            'query_length': len(query),
            'has_context': bool(context),
            'reasoning_sections': list(reasoning_data.keys())
        })
        
        try:
            # Check rate limit first
            if not await self.rate_limiter.acquire():
                retry_after = await self.rate_limiter.get_retry_after()
                raise RateLimitError(
                    "Rate limit exceeded for Claude API",
                    retry_after=retry_after
                )

            # Prepare message parameters
            log_debug("Preparing message parameters...")
            message_params = self._prepare_message_params(query, reasoning_data, context)
            log_debug("Message parameters prepared", extra={
                'system_prompt_length': len(message_params.get('system', '')),
                'user_message_length': len(message_params.get('messages', [{}])[0].get('content', ''))
            })
            
            # Handle streaming vs non-streaming
            if self.config.stream_response:
                log_debug("Using streaming response mode")
                try:
                    result = await self._handle_streaming_response(message_params)
                except Exception as e:
                    log_error("Streaming response failed", extra={'error': str(e)})
                    # Fallback to non-streaming
                    log_info("Falling back to non-streaming mode")
                    result = await self._handle_regular_response(message_params)
            else:
                log_debug("Using regular response mode")
                result = await self._handle_regular_response(message_params)
            
            # Validate result structure
            if not self._validate_result_structure(result):
                raise ClaudeAPIError("Invalid response structure from Claude")
            
            duration_ms = (time.time() - start_time) * 1000
            log_performance("claude_generate", duration_ms, {
                'response_size': len(result.get('code_completion', '')),
                'streaming_used': self.config.stream_response
            })
            
            return result
            
        except RateLimitError as e:
            log_warning("Rate limit exceeded", extra={'retry_after': e.retry_after})
            raise  # Re-raise for retry handler
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            log_error("Failed to generate code", exc_info=True, extra={
                'error_type': type(e).__name__,
                'duration_ms': duration_ms,
                'query': query
            })
            raise ClaudeAPIError(f"Failed to generate code: {str(e)}")

    def _validate_result_structure(self, result: Dict[str, Any]) -> bool:
        """Validate the structure of Claude's response"""
        required_fields = ['code_completion', 'explanation']
        return all(field in result for field in required_fields) and bool(result['code_completion'])

    async def _handle_regular_response(self, message_params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle regular (non-streaming) response from Claude"""
        try:
            # Make API request
            log_debug("Making regular API request...")
            response = await self.client.messages.create(
                model=message_params['model'],
                system=message_params['system'],
                messages=message_params['messages'],
                temperature=message_params['temperature'],
                max_tokens=message_params['max_tokens']
            )
            
            if not response or not response.content:
                log_error("Empty response from Claude")
                raise ClaudeAPIError("Empty response from Claude")
            
            # Combine all text and clean up JSON parsing
            full_text = ''.join(chunk.text for chunk in response.content)
            log_debug("Combined accumulated text", extra={
                'total_size': len(full_text),
                'starts_with_json': full_text.lstrip().startswith('{')
            })
            
            if not full_text:
                log_error("Empty regular response from Claude")
                raise ClaudeAPIError("Empty regular response from Claude")
            
            # Clean and validate response
            cleaned_text = self._clean_response_text(full_text)
            self._validate_response(cleaned_text)
            
            try:
                parsed_output = self.output_parser.parse(cleaned_text)
                return parsed_output
            except Exception as e:
                raise ClaudeAPIError(
                    f"Failed to parse JSON output from Claude: {e}",
                    details={
                        'raw_output': full_text,
                        'cleaned_output': cleaned_text
                    }
                ) from e
            
        except Exception as e:
            log_error("Regular response handling failed", exc_info=True)
            raise ClaudeAPIError(f"Failed to handle regular response: {str(e)}")

    async def _handle_streaming_response(self, message_params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle streaming response from Claude"""
        try:
            # Make streaming API request
            log_debug("Making streaming API request...", extra={
                'model': message_params['model'],
                'max_tokens': message_params['max_tokens']
            })
            
            stream = await self.client.messages.create(
                model=message_params['model'],
                system=message_params['system'],
                messages=message_params['messages'],
                temperature=message_params['temperature'],
                max_tokens=message_params['max_tokens'],
                stream=True
            )
            
            # Initialize accumulators for different content blocks
            accumulated_text = []
            current_block_text = []
            block_count = 0
            
            # Process stream events
            async for chunk in stream:
                event_type = getattr(chunk, 'type', None)
                log_debug(f"Processing stream chunk", extra={
                    'event_type': event_type,
                    'chunk_attrs': dir(chunk),
                    'block_count': block_count
                })
                
                if event_type == 'message_start':
                    log_debug("Received message_start event", extra={
                        'message_id': getattr(getattr(chunk, 'message', None), 'id', None)
                    })
                    continue
                    
                elif event_type == 'content_block_start':
                    block_count += 1
                    log_debug("Received content_block_start event", extra={
                        'block_number': block_count,
                        'block_type': getattr(getattr(chunk, 'content_block', None), 'type', None)
                    })
                    current_block_text = []
                    
                elif event_type == 'content_block_delta':
                    if hasattr(chunk, 'delta'):
                        delta = chunk.delta
                        log_debug("Processing content block delta", extra={
                            'delta_type': delta.type,
                            'block_number': block_count
                        })
                        
                        if delta.type == 'text_delta' and hasattr(delta, 'text'):
                            # Skip JSON declaration if present at start
                            text = delta.text
                            if not current_block_text and text.lstrip().startswith('{'):
                                log_debug("Found JSON declaration in text delta", extra={
                                    'original_text': text[:100]
                                })
                                text = text[text.find('{') + 1:].lstrip()
                                log_debug("Removed JSON declaration", extra={
                                    'cleaned_text': text[:100]
                                })
                            current_block_text.append(text)
                            log_debug("Added text to current block", extra={
                                'text_length': len(text),
                                'current_block_size': len(''.join(current_block_text))
                            })
                        elif delta.type == 'input_json_delta' and hasattr(delta, 'partial_json'):
                            current_block_text.append(delta.partial_json)
                            log_debug("Added JSON delta to current block", extra={
                                'json_length': len(delta.partial_json)
                            })
                            
                elif event_type == 'content_block_stop':
                    log_debug("Received content_block_stop event", extra={
                        'block_number': block_count,
                        'block_text_size': len(''.join(current_block_text))
                    })
                    if current_block_text:
                        block_content = ''.join(current_block_text)
                        accumulated_text.append(block_content)
                        log_debug("Added block to accumulated text", extra={
                            'block_size': len(block_content),
                            'total_blocks': len(accumulated_text),
                            'total_size': len('\n'.join(accumulated_text))
                        })
                    current_block_text = []
                    
                elif event_type == 'message_stop':
                    log_debug("Received message_stop event", extra={
                        'total_blocks': block_count
                    })
                    break
                    
                elif event_type == 'error':
                    error_data = getattr(chunk, 'error', {})
                    error_msg = getattr(error_data, 'message', 'Unknown streaming error')
                    log_error(f"Received error event: {error_msg}", extra={
                        'error_data': error_data
                    })
                    raise ClaudeAPIError(f"Streaming error: {error_msg}")
            
            # Combine all text and clean up JSON parsing
            full_text = '\n'.join(accumulated_text)
            log_debug("Combined accumulated text", extra={
                'total_size': len(full_text),
                'num_blocks': len(accumulated_text)
            })
            
            if not full_text:
                log_error("Empty streaming response from Claude")
                raise ClaudeAPIError("Empty streaming response from Claude")
            
            # Clean and validate response
            cleaned_text = self._clean_response_text(full_text)
            self._validate_response(cleaned_text)
            
            try:
                parsed_output = self.output_parser.parse(cleaned_text)
                return parsed_output
            except Exception as e:
                raise ClaudeAPIError(
                    f"Failed to parse JSON output from Claude (streaming): {e}",
                    details={
                        'raw_output': full_text,
                        'cleaned_output': cleaned_text
                    }
                ) from e
            
        except Exception as e:
            log_error("Streaming response handling failed", exc_info=True)
            raise ClaudeAPIError(f"Failed to handle streaming response: {str(e)}")

    def _clean_response_text(self, text: str) -> str:
        """Clean response text by handling markdown code blocks and JSON formatting"""
        logger.debug("Cleaning response text...")
        
        # Ensure we have a string
        if not isinstance(text, str):
            logger.warning(f"Received non-string response: {type(text)}")
            try:
                text = str(text)
            except Exception as e:
                logger.error(f"Failed to convert response to string: {e}")
                raise ClaudeAPIError(
                    "Invalid response type from Claude",
                    details={
                        'received_type': str(type(text)),
                        'received_value': repr(text)
                    }
                )
        
        # Try to extract JSON from markdown code block if present
        try:
            return parse_json_markdown(text)
        except Exception as e:
            logger.debug(f"Failed to parse markdown JSON: {e}")
            
        # If no markdown block or parsing failed, try to find JSON content
        import re
        json_pattern = r'\{[\s\S]*\}'
        match = re.search(json_pattern, text)
        if match:
            return match.group(0)
            
        return text

    def _validate_response(self, response_text: str) -> None:
        """Validate response structure before parsing"""
        try:
            import json
            
            # Ensure we have a string
            if not isinstance(response_text, str):
                logger.warning(f"Received non-string response for validation: {type(response_text)}")
                try:
                    response_text = str(response_text)
                except Exception as e:
                    logger.error(f"Failed to convert response to string for validation: {e}")
                    raise ClaudeAPIError(
                        "Invalid response type from Claude",
                        details={
                            'received_type': str(type(response_text)),
                            'received_value': repr(response_text)
                        }
                    )
            
            # Clean and prepare the response text
            cleaned_text = self._clean_response_text(response_text)
            logger.debug("Attempting to parse cleaned response text")
            
            try:
                data = json.loads(cleaned_text)
            except json.JSONDecodeError as e:
                raise ClaudeAPIError(
                    f"Invalid JSON in Claude response: {str(e)}",
                    details={
                        'raw_output': response_text,
                        'cleaned_output': cleaned_text,
                        'error_location': f"line {e.lineno}, column {e.colno}"
                    }
                )
            
            # Check for required fields
            required_fields = ['code_completion', 'explanation']
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                raise ClaudeAPIError(
                    f"Missing required fields in Claude response: {', '.join(missing_fields)}",
                    details={
                        'raw_output': response_text,
                        'cleaned_output': cleaned_text,
                        'missing_fields': missing_fields,
                        'found_fields': list(data.keys())
                    }
                )
                
            # Validate field types and content
            if not isinstance(data['code_completion'], str) or not data['code_completion'].strip():
                raise ClaudeAPIError(
                    "code_completion must be a non-empty string",
                    details={
                        'raw_output': response_text,
                        'cleaned_output': cleaned_text,
                        'actual_type': type(data['code_completion']).__name__ if 'code_completion' in data else 'missing'
                    }
                )
                
            if not isinstance(data['explanation'], str) or not data['explanation'].strip():
                raise ClaudeAPIError(
                    "explanation must be a non-empty string",
                    details={
                        'raw_output': response_text,
                        'cleaned_output': cleaned_text,
                        'actual_type': type(data['explanation']).__name__ if 'explanation' in data else 'missing'
                    }
                )
                
            # Validate sandbox_config if present
            if 'sandbox_config' in data:
                if not isinstance(data['sandbox_config'], dict):
                    raise ClaudeAPIError(
                        "sandbox_config must be an object",
                        details={'actual_type': type(data['sandbox_config']).__name__}
                    )
                # Validate sandbox_config fields
                for field in ['template', 'timeout_ms', 'memory_mb']:
                    if field in data['sandbox_config']:
                        if field == 'template' and not isinstance(data['sandbox_config'][field], str):
                            raise ClaudeAPIError(f"sandbox_config.{field} must be a string")
                        elif field in ['timeout_ms', 'memory_mb'] and not isinstance(data['sandbox_config'][field], int):
                            raise ClaudeAPIError(f"sandbox_config.{field} must be an integer")
                
            # Validate metadata if present
            if 'metadata' in data:
                if not isinstance(data['metadata'], list):
                    raise ClaudeAPIError(
                        "metadata must be a list",
                        details={'actual_type': type(data['metadata']).__name__}
                    )
                for item in data['metadata']:
                    if not isinstance(item, dict) or 'key' not in item or 'value' not in item:
                        raise ClaudeAPIError(
                            "metadata items must be objects with 'key' and 'value' fields",
                            details={'invalid_item': item}
                        )
                        
        except json.JSONDecodeError as e:
            raise ClaudeAPIError(
                f"Invalid JSON in Claude response: {str(e)}",
                details={
                    'raw_output': response_text,
                    'error_location': f"line {e.lineno}, column {e.colno}"
                }
            )
        except KeyError as e:
            raise ClaudeAPIError(
                f"Missing key in Claude response: {str(e)}",
                details={'raw_output': response_text}
            )