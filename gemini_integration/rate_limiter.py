"""Rate limiter for API requests"""
import asyncio
import time
import logging
from typing import Optional
from logger import log_info, log_debug, log_warning, log_performance

logger = logging.getLogger(__name__)

class RateLimiter:
    """Token bucket rate limiter with retry support"""
    
    def __init__(self, rate_per_minute: int, burst_limit: int):
        """
        Initialize rate limiter
        
        Args:
            rate_per_minute: Number of requests allowed per minute
            burst_limit: Maximum burst size (token bucket capacity)
        """
        self.rate = rate_per_minute / 60.0  # Convert to per second
        self.burst_limit = burst_limit
        self.tokens = burst_limit
        self.last_update = time.monotonic()
        self.lock = asyncio.Lock()
        
        log_info("Initialized rate limiter", extra={
            'rate_per_minute': rate_per_minute,
            'burst_limit': burst_limit,
            'tokens_per_second': self.rate
        })

    async def _update_tokens(self) -> float:
        """
        Update token count based on elapsed time
        
        Returns:
            float: Current token count
        """
        now = time.monotonic()
        time_passed = now - self.last_update
        
        # Update token count
        old_tokens = self.tokens
        self.tokens = min(
            self.burst_limit,
            self.tokens + time_passed * self.rate
        )
        self.last_update = now
        
        log_debug("Rate limiter state updated", extra={
            'time_passed': time_passed,
            'old_tokens': old_tokens,
            'new_tokens': self.tokens,
            'tokens_added': self.tokens - old_tokens
        })
        
        return self.tokens
        
    async def acquire(self) -> bool:
        """
        Acquire a token if available
        
        Returns:
            bool: True if token acquired, False if rate limit exceeded
        """
        start_time = time.time()
        async with self.lock:
            tokens = await self._update_tokens()
            
            if tokens >= 1:
                self.tokens -= 1
                duration_ms = (time.time() - start_time) * 1000
                log_performance("rate_limiter_acquire", duration_ms, {
                    'success': True,
                    'remaining_tokens': self.tokens
                })
                return True
            
            log_warning("Rate limit exceeded", extra={
                'current_tokens': self.tokens,
                'retry_after': await self.get_retry_after()
            })
            return False
            
    async def get_retry_after(self) -> float:
        """
        Get suggested retry after duration in seconds
        
        Returns:
            float: Suggested wait time in seconds
        """
        async with self.lock:
            tokens = await self._update_tokens()
            
            if tokens >= 1:
                return 0.0
                
            retry_after = (1 - tokens) / self.rate
            log_debug("Calculated retry after", extra={
                'retry_after': retry_after,
                'current_tokens': tokens
            })
            return retry_after

    async def check_rate_limit(self) -> None:
        """
        Check rate limit and raise RateLimitError if exceeded
        
        Raises:
            RateLimitError: If rate limit is exceeded
        """
        if not await self.acquire():
            retry_after = await self.get_retry_after()
            log_warning("Rate limit check failed", extra={
                'retry_after': retry_after
            })
            from mvp_orchestrator.error_types import RateLimitError
            raise RateLimitError(
                "Rate limit exceeded",
                retry_after=retry_after
            ) 