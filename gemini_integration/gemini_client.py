# gemini_integration/gemini_client.py
import google.generativeai as genai
import logging
from typing import Dict, Any, Optional, List
import time
import asyncio
from dataclasses import dataclass
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)
from datetime import datetime
from .rate_limiter import RateLimiter
from langchain.output_parsers import StructuredOutputParser
from models.pydantic_schemas import GeminiReasoningResult
from mvp_orchestrator.error_types import (
    GeminiAPIError,
    RateLimitError,
    ValidationError,
    ReasoningError
)
from logger import log_info, log_error, log_debug, log_api_request, log_api_response, log_performance  # Assuming you have a logger.py
from langchain_core.utils.json import parse_json_markdown  # Add this import

logger = logging.getLogger(__name__)

class GeminiConfig:
    """Configuration for Gemini client"""
    def __init__(
        self,
        api_key: str,
        model: str = "gemini-2.0-flash-thinking-exp-01-21",
        use_thinking_model: bool = False,
        rate_limit_per_minute: int = 60,
        rate_limit_burst: int = 10,
        api_version: str = "v1alpha"
    ):
        self.api_key = api_key
        self.model = model
        self.use_thinking_model = use_thinking_model
        self.rate_limit_per_minute = rate_limit_per_minute
        self.rate_limit_burst = rate_limit_burst
        self.api_version = api_version

class GeminiReasoner:
    """Enhanced Gemini client for code reasoning"""
    
    def __init__(self, gemini_key: str, config: Optional[GeminiConfig] = None):
        """Initialize Gemini client with configuration"""
        logger.info("Initializing GeminiReasoner...")
        
        if not gemini_key:
            logger.error("No API key provided")
            raise ValidationError("Gemini API key is required")
            
        self.config = config or GeminiConfig(api_key=gemini_key)
        logger.debug(f"Using model: {self.config.model}, thinking_model: {self.config.use_thinking_model}")
        
        self.rate_limiter = RateLimiter(
            self.config.rate_limit_per_minute,
            self.config.rate_limit_burst
        )
        logger.debug(f"Rate limiter configured: {self.config.rate_limit_per_minute}/min, burst: {self.config.rate_limit_burst}")
        
        try:
            # Configure API key and version
            logger.info("Configuring Gemini API...")
            logger.debug(f"API version: {self.config.api_version}")
            genai.configure(api_key=self.config.api_key)
            logger.debug("Gemini API configured successfully")
            
            # Initialize model for generation
            logger.info("Initializing Gemini model...")
            logger.debug(f"Model name: {self.config.model}")
            self.model = genai.GenerativeModel(
                model_name=self.config.model,
                generation_config={'temperature': 0.7}
            )
            logger.debug("Gemini model initialized successfully")
            
            # Initialize output parser
            logger.info("Initializing output parser...")
            response_schemas = [
                {
                    "name": "reasoning_steps",
                    "type": "array",
                    "description": "List of reasoning steps",
                    "items": {"type": "string"}
                },
                {
                    "name": "conclusion",
                    "type": "string",
                    "description": "Final conclusion of reasoning"
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
                    "description": "Reasoning version"
                }
            ]
            logger.debug(f"Response schemas defined: {[schema['name'] for schema in response_schemas]}")
            try:
                self.output_parser = StructuredOutputParser(response_schemas=response_schemas)
                logger.debug("Output parser initialized successfully")
            except Exception as parser_error:
                logger.error(f"Failed to initialize output parser: {str(parser_error)}", exc_info=True)
                logger.error(f"Parser error type: {type(parser_error)}")
                raise
            
            logger.info(f"Successfully initialized Gemini client with model: {self.config.model}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Gemini client: {str(e)}", exc_info=True)
            logger.error(f"Error type: {type(e)}")
            logger.error(f"Error details: {str(e)}")
            if hasattr(e, '__dict__'):
                logger.error(f"Error attributes: {e.__dict__}")
            raise GeminiAPIError("Failed to initialize Gemini", details={'error': str(e), 'error_type': str(type(e))})
            
    def _clean_response_text(self, text: Any) -> str:
        """Clean response text by handling markdown code blocks and JSON formatting"""
        logger.debug("Cleaning response text...")
        
        # If we already have a dictionary, convert it to JSON string
        if isinstance(text, dict):
            logger.debug("Converting dictionary response to JSON string")
            try:
                import json
                return json.dumps(text)
            except Exception as e:
                logger.error(f"Failed to convert dictionary to JSON: {e}")
                raise ReasoningError(
                    "Failed to convert Gemini dictionary response to JSON",
                    details={
                        'received_type': str(type(text)),
                        'received_value': repr(text),
                        'error': str(e)
                    }
                )
        
        # If we have a Gemini response object, extract the text
        if hasattr(text, 'text'):
            logger.debug("Extracting text from Gemini response object")
            text = text.text
        
        # Ensure we have a string
        if not isinstance(text, str):
            logger.warning(f"Received non-string response: {type(text)}")
            try:
                text = str(text)
            except Exception as e:
                logger.error(f"Failed to convert response to string: {e}")
                raise ReasoningError(
                    "Invalid response type from Gemini",
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
                    raise ReasoningError(
                        "Invalid response type from Gemini",
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
                raise ReasoningError(
                    f"Invalid JSON in Gemini response: {str(e)}",
                    details={
                        'raw_output': response_text,
                        'cleaned_output': cleaned_text,
                        'error_location': f"line {e.lineno}, column {e.colno}"
                    }
                )
            
            # Check for required fields
            required_fields = ['reasoning_steps', 'conclusion']
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                raise ReasoningError(
                    f"Missing required fields in Gemini response: {', '.join(missing_fields)}",
                    details={
                        'raw_output': response_text,
                        'cleaned_output': cleaned_text,
                        'missing_fields': missing_fields,
                        'found_fields': list(data.keys())
                    }
                )
                
            # Validate field types and content
            if not isinstance(data['reasoning_steps'], list):
                raise ReasoningError(
                    "reasoning_steps must be a list",
                    details={
                        'raw_output': response_text,
                        'cleaned_output': cleaned_text,
                        'actual_type': type(data['reasoning_steps']).__name__
                    }
                )
                
            if not data['reasoning_steps']:
                raise ReasoningError(
                    "reasoning_steps cannot be empty",
                    details={'raw_output': response_text}
                )
                
            if not isinstance(data['conclusion'], str) or not data['conclusion'].strip():
                raise ReasoningError(
                    "conclusion must be a non-empty string",
                    details={
                        'raw_output': response_text,
                        'cleaned_output': cleaned_text,
                        'actual_type': type(data['conclusion']).__name__ if 'conclusion' in data else 'missing'
                    }
                )
                
            # Validate metadata if present
            if 'metadata' in data:
                if not isinstance(data['metadata'], list):
                    raise ReasoningError(
                        "metadata must be a list",
                        details={'actual_type': type(data['metadata']).__name__}
                    )
                for item in data['metadata']:
                    if not isinstance(item, dict) or 'key' not in item or 'value' not in item:
                        raise ReasoningError(
                            "metadata items must be objects with 'key' and 'value' fields",
                            details={'invalid_item': item}
                        )
                        
        except json.JSONDecodeError as e:
            raise ReasoningError(
                f"Invalid JSON in Gemini response: {str(e)}",
                details={
                    'raw_output': response_text,
                    'error_location': f"line {e.lineno}, column {e.colno}"
                }
            )
        except KeyError as e:
            raise ReasoningError(
                f"Missing key in Gemini response: {str(e)}",
                details={'raw_output': response_text}
            )

    async def get_reasoning(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """
        Get reasoning about code implementation from Gemini
        """
        start_time = time.time()
        logger.info(f"Getting reasoning for query: {query[:100]}...", extra={
            'query_length': len(query),
            'has_context': bool(context)
        })
        
        if not query:
            logger.error("Empty query provided")
            raise ValidationError("Query cannot be empty")
            
        # Check rate limit
        logger.debug("Checking rate limit...")
        if not await self.rate_limiter.acquire():
            logger.warning("Rate limit exceeded", extra={
                'retry_after': self.rate_limiter.get_retry_after()
            })
            retry_after = self.rate_limiter.get_retry_after()
            raise RateLimitError(
                "Rate limit exceeded for Gemini API",
                retry_after=retry_after
            )
            
        try:
            # Prepare prompt with context
            logger.debug("Preparing prompt...")
            prompt = self._prepare_prompt(query, context)
            logger.debug("Prompt prepared", extra={
                'prompt_length': len(prompt)
            })
            
            # Generate response
            logger.info("Generating response from Gemini...")
            response = await self.model.generate_content_async(prompt)
            
            if not response:
                logger.error("Empty response received from Gemini")
                raise GeminiAPIError("Empty response from Gemini")
            
            # Handle different response types
            response_content = None
            if hasattr(response, 'text'):
                response_content = response.text
            elif isinstance(response, dict):
                response_content = response
            else:
                logger.error(f"Unexpected response type from Gemini: {type(response)}")
                raise GeminiAPIError(
                    "Unexpected response type from Gemini",
                    details={'response_type': str(type(response))}
                )
            
            # Clean and validate response structure
            cleaned_text = self._clean_response_text(response_content)
            self._validate_response(cleaned_text)
            
            # Parse JSON response
            logger.info("Parsing JSON response...")
            try:
                parsed_output = self.output_parser.parse(cleaned_text)
                return parsed_output
            except Exception as e:
                raise ReasoningError(
                    f"Failed to parse JSON output from Gemini Reasoning: {e}",
                    details={
                        'raw_output': str(response_content),
                        'cleaned_output': cleaned_text
                    }
                ) from e
            
        except RateLimitError:
            logger.warning("Rate limit error encountered")
            raise
            
        except Exception as e:
            logger.error(f"Error getting reasoning from Gemini: {str(e)}", exc_info=True, extra={
                'query': query,
                'error_type': type(e).__name__,
                'processing_time_ms': (time.time() - start_time) * 1000
            })
            raise
            
    def _prepare_prompt(self, query: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Prepare prompt for Gemini with context"""
        logger.debug("Preparing prompt with context...")
        
        # Base prompt template
        base_prompt = f"""You are a helpful AI reasoning assistant. Please provide a step-by-step reasoning to answer the user's question.

QUESTION: {query}

RESPONSE FORMAT:
You must respond with valid JSON enclosed in a markdown code block. Do not include any text outside the code block.

Example format:
```json
{{
  "reasoning_steps": ["step 1", "step 2"],
  "conclusion": "final conclusion",
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
3. "reasoning_steps" must be a non-empty array of strings
4. "conclusion" must be a non-empty string summarizing your final recommendation
5. "metadata" must be an array of objects with "key" and "value" fields
6. Do not include any explanation or text outside the JSON block

EXAMPLE CONCLUSIONS:
- "Based on the analysis, I recommend implementing X using Y approach because Z"
- "The optimal solution would be X because of reasons Y and Z"
- "Given the requirements, the best approach is X as it addresses Y while maintaining Z"
"""

        if context:
            logger.debug(f"Adding context: {list(context.keys())}")
            context_str = "\nCONTEXT:\n"
            for key, value in context.items():
                context_str += f"{key}: {value}\n"
            base_prompt += context_str

        logger.debug(f"Final prompt length: {len(base_prompt)}")
        return base_prompt
