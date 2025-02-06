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
from .xml_processor import GeminiXMLProcessor
from mvp_orchestrator.error_types import (
    GeminiAPIError,
    RateLimitError,
    ValidationError
)
from logger import log_info, log_error, log_debug, log_api_request, log_api_response, log_performance  # Assuming you have a logger.py

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
            genai.configure(api_key=self.config.api_key)
            
            # Initialize model for generation
            logger.info("Initializing Gemini model...")
            self.model = genai.GenerativeModel(
                model_name=self.config.model,
                generation_config={'temperature': 0.7}  # Add some configuration
            )
            
            # Initialize XML processor
            logger.info("Initializing XML processor...")
            self.xml_processor = GeminiXMLProcessor()
            
            logger.info(f"Successfully initialized Gemini client with model: {self.config.model}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Gemini client: {str(e)}", exc_info=True)
            raise GeminiAPIError("Failed to initialize Gemini", details={'error': str(e)})
            
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
            
            # Configure thinking model settings
            generation_config = {}
            if self.config.use_thinking_model:
                logger.debug("Configuring thinking model settings...")
                generation_config = {
                    'temperature': 0.7,
                    'candidate_count': 1,
                    'stop_sequences': [],
                    'max_output_tokens': 2048,
                }
                logger.debug("Thinking model configured", extra={
                    'generation_config': generation_config
                })
            
            # Generate response
            logger.info("Generating response from Gemini...")
            log_api_request(
                method="POST",
                url="https://generativelanguage.googleapis.com/v1/models/gemini-pro:generateContent",
                headers={"x-goog-api-key": "[REDACTED]"},
                body={'prompt': prompt, 'generation_config': generation_config}
            )
            
            response = await self.model.generate_content_async(
                prompt,
                generation_config=generation_config
            )
            
            duration_ms = (time.time() - start_time) * 1000
            log_api_response(
                status_code=200,  # Assuming success, we should handle actual status codes
                response_body={'text': response.text[:200] + "..." if response.text else None},
                duration_ms=duration_ms
            )
            log_performance("gemini_generate", duration_ms)
            
            # Process response
            if not response or not response.text:
                logger.error("Empty response received from Gemini")
                raise GeminiAPIError("Empty response from Gemini")
            
            logger.debug(f"Raw response received: {response.text[:200]}...")
            
            # Extract thoughts if using thinking model
            thoughts = []
            if self.config.use_thinking_model:
                log_info("Processing thinking model output", extra={
                    'model': self.config.model,
                    'response_length': len(response.text) if response.text else 0
                })
                try:
                    thought_count = 0
                    for part in response.candidates[0].content.parts:
                        log_debug(f"Processing response part {thought_count + 1}", extra={
                            'part_type': type(part).__name__,
                            'has_thought_attr': hasattr(part, 'thought'),
                            'part_length': len(part.text) if hasattr(part, 'text') else 0
                        })
                        if getattr(part, 'thought', False):
                            thought_text = part.text.strip()
                            thoughts.append(thought_text)
                            thought_count += 1
                            log_debug(f"Extracted thought {thought_count}", extra={
                                'thought_length': len(thought_text),
                                'thought_preview': thought_text[:100] + '...' if len(thought_text) > 100 else thought_text
                            })
                    
                    log_info(f"Thought extraction completed", extra={
                        'total_thoughts': len(thoughts),
                        'total_parts': thought_count,
                        'average_thought_length': sum(len(t) for t in thoughts) / len(thoughts) if thoughts else 0
                    })
                except Exception as e:
                    log_error("Failed to extract thoughts", exc_info=True, extra={
                        'error_type': type(e).__name__,
                        'candidates_length': len(response.candidates) if hasattr(response, 'candidates') else 0,
                        'has_content': hasattr(response.candidates[0], 'content') if hasattr(response, 'candidates') and response.candidates else False
                    })
            else:
                log_debug("Thinking model disabled, skipping thought extraction")
            
            # Parse XML response
            logger.info("Parsing XML response...")
            result = self.xml_processor.validate_and_process(response.text)
            
            # Add thoughts to result
            if thoughts:
                result['thoughts'] = thoughts
                logger.debug(f"Added {len(thoughts)} thoughts to result")
            
            # Add metadata
            result['metadata'] = {
                'model': self.config.model,
                'timestamp': datetime.utcnow().isoformat(),
                'query': query,
                'thinking_model_used': self.config.use_thinking_model,
                'generation_config': generation_config,
                'processing_time_ms': duration_ms
            }
            
            logger.info("Successfully generated reasoning", extra={
                'processing_time_ms': duration_ms,
                'response_size': len(response.text) if response.text else 0,
                'num_thoughts': len(thoughts)
            })
            return result
            
        except RateLimitError:
            logger.warning("Rate limit error encountered")
            raise
            
        except Exception as e:
            logger.error(f"Error getting reasoning from Gemini: {str(e)}", exc_info=True, extra={
                'query': query,
                'error_type': type(e).__name__,
                'processing_time_ms': (time.time() - start_time) * 1000
            })
            raise GeminiAPIError(
                "Failed to get reasoning",
                details={'error': str(e), 'query': query}
            )
            
    def _prepare_prompt(self, query: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Prepare prompt for Gemini with context"""
        logger.debug("Preparing prompt with context...")
        
        # Base prompt template
        prompt = f"""
        You are a code reasoning assistant. Analyze the following request and provide structured reasoning about implementation.
        
        REQUEST: {query}
        
        Respond in XML format with the following structure:
        <?xml version="1.0" encoding="UTF-8"?>
        <reasoning version="2.0.0">
            <technical_requirements>
                <item>List key technical requirements</item>
                ...
            </technical_requirements>
            <implementation_strategy>
                <item>Outline implementation steps</item>
                ...
            </implementation_strategy>
            <guidance_for_claude>
                <item>Provide guidance for code synthesis</item>
                ...
            </guidance_for_claude>
            <sandbox_requirements>
                <template>python3</template>
                <dependencies>
                    <package>any required packages</package>
                </dependencies>
            </sandbox_requirements>
        </reasoning>
        """
        
        # Add context if provided
        if context:
            logger.debug(f"Adding context: {list(context.keys())}")
            context_str = "\nCONTEXT:\n"
            for key, value in context.items():
                context_str += f"{key}: {value}\n"
            prompt += context_str
            
        logger.debug(f"Final prompt length: {len(prompt)}")
        return prompt
