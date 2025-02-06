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
from .xml_validator import ClaudeXMLValidator
import aiohttp

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
            
        # Initialize XML validator
        self.xml_validator = ClaudeXMLValidator()
        
    def _prepare_message_params(
        self,
        query: str,
        reasoning_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Prepare message parameters for Claude API request"""
        # Construct the system prompt
        system_prompt = """You are a senior software engineer tasked with implementing code based on requirements and reasoning.
        Your responses should be clear, efficient, and well-documented. Always provide complete, runnable code that includes all necessary imports and dependencies."""

        # Extract reasoning components
        requirements = "\n".join(f"- {req}" for req in reasoning_data.get('technical_requirements', []))
        strategy = "\n".join(f"- {step}" for step in reasoning_data.get('implementation_strategy', []))
        guidance = "\n".join(f"- {guide}" for guide in reasoning_data.get('guidance_for_claude', []))
        thoughts = "\n".join(f"- {thought}" for thought in reasoning_data.get('thoughts', []))

        # Build the user message
        user_message = f"""Query: {query}

Technical Requirements:
{requirements}

Implementation Strategy:
{strategy}

Specific Guidance:
{guidance}

Reasoning Thoughts:
{thoughts}

Please provide your response in XML format with the following structure:
<?xml version="1.0" encoding="UTF-8"?>
<synthesis version="2.0.0">
    <code_completion>
        [Your implementation here]
    </code_completion>
    <explanation>
        [Brief explanation of the implementation]
    </explanation>
    <sandbox_config>
        <template>python3</template>
        <dependencies>
            <package>any required packages</package>
        </dependencies>
    </sandbox_config>
    <metadata>
        <item key="language">python</item>
        <item key="complexity">medium</item>
    </metadata>
</synthesis>"""

        # Add context if provided
        if context:
            user_message += f"\n\nAdditional Context:\n{context}"

        return {
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_message}],
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
            
            # Validate and process XML response
            log_debug("Processing Claude response...")
            result = self.xml_validator.validate_and_process(response.content[0].text)
            
            return result
            
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
                            # Skip XML declaration if present at start
                            text = delta.text
                            if not current_block_text and text.lstrip().startswith('<?xml'):
                                log_debug("Found XML declaration in text delta", extra={
                                    'original_text': text[:100]
                                })
                                text = text[text.find('?>') + 2:].lstrip()
                                log_debug("Removed XML declaration", extra={
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
            
            # Combine all text and clean up XML declaration
            full_text = '\n'.join(accumulated_text)
            log_debug("Combined accumulated text", extra={
                'total_size': len(full_text),
                'num_blocks': len(accumulated_text),
                'starts_with_xml': full_text.lstrip().startswith('<?xml')
            })
            
            if not full_text:
                log_error("Empty streaming response from Claude")
                raise ClaudeAPIError("Empty streaming response from Claude")
            
            # Remove any XML declaration
            if full_text.lstrip().startswith('<?xml'):
                log_debug("Removing XML declaration from full text", extra={
                    'original_start': full_text[:200]
                })
                full_text = full_text[full_text.find('?>') + 2:].lstrip()
                log_debug("Removed XML declaration", extra={
                    'new_start': full_text[:200]
                })
            
            # Validate and process XML response
            log_debug("Processing streamed response...", extra={
                'text_length': len(full_text),
                'first_tag': full_text.split('>', 1)[0] + '>' if '>' in full_text else 'NO_TAG'
            })
            
            # Clean up any markdown code block markers
            if full_text.startswith("```xml"):
                full_text = full_text.replace("```xml", "", 1)
            if full_text.endswith("```"):
                full_text = full_text.rsplit("```", 1)[0]
            
            result = self.xml_validator.validate_and_process(full_text)
            
            log_debug("Successfully processed XML response", extra={
                'result_keys': list(result.keys()),
                'has_code': bool(result.get('code_completion')),
                'has_explanation': bool(result.get('explanation'))
            })
            
            return result
            
        except Exception as e:
            log_error("Streaming response handling failed", exc_info=True, extra={
                'error_type': type(e).__name__,
                'error_msg': str(e),
                'accumulated_blocks': len(accumulated_text) if 'accumulated_text' in locals() else 0
            })
            raise ClaudeAPIError(f"Failed to handle streaming response: {str(e)}")