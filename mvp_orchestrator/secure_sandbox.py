from typing import Dict, Optional, Any
from e2b import Sandbox
from dataclasses import dataclass
import asyncio
import logging
import time
from .error_types import SandboxError
from logger import log_info, log_debug, log_error, log_warning, log_performance

logger = logging.getLogger(__name__)

@dataclass
class SandboxConfig:
    """Configuration for the secure sandbox environment"""
    api_key: str
    template: str = "base"  # E2B template to use
    timeout_ms: int = 10 * 60 * 1000  # 10 minutes default
    memory_mb: int = 512  # Default memory limit
    dependencies: Optional[list[str]] = None  # Python packages to install

    def validate(self):
        """Validate the configuration"""
        log_debug("Validating sandbox configuration...")
        if not self.api_key:
            log_error("Missing E2B API key")
            raise ValueError("E2B API key is required")
        if self.timeout_ms <= 0:
            log_error("Invalid timeout value", extra={'timeout_ms': self.timeout_ms})
            raise ValueError("timeout_ms must be positive")
        if self.memory_mb <= 0:
            log_error("Invalid memory limit", extra={'memory_mb': self.memory_mb})
            raise ValueError("memory_mb must be positive")
        log_debug("Sandbox configuration validated", extra={
            'template': self.template,
            'timeout_ms': self.timeout_ms,
            'memory_mb': self.memory_mb,
            'has_dependencies': bool(self.dependencies)
        })

class SecureSandbox:
    """
    A secure sandbox environment for code execution using E2B.
    Provides isolation and resource limits.
    """
    
    def __init__(self, config: SandboxConfig):
        """
        Initialize the sandbox with configuration
        
        Args:
            config: SandboxConfig instance with API key and settings
        """
        self.config = config
        self.config.validate()
        self._sandbox: Optional[Sandbox] = None
        
        log_info("Initialized secure sandbox", extra={
            'template': config.template,
            'timeout_ms': config.timeout_ms,
            'memory_mb': config.memory_mb
        })
        
    async def __aenter__(self):
        """Async context manager entry"""
        start_time = time.time()
        try:
            log_info("Creating sandbox environment...")
            self._sandbox = await Sandbox.create(
                template=self.config.template,
                api_key=self.config.api_key,
                timeout_ms=self.config.timeout_ms,
            )
            
            # Install dependencies if specified
            if self.config.dependencies:
                log_info("Installing dependencies...", extra={
                    'num_packages': len(self.config.dependencies)
                })
                for package in self.config.dependencies:
                    log_debug(f"Installing package: {package}")
                    await self._sandbox.install_python_package(package)
                    
            duration_ms = (time.time() - start_time) * 1000
            log_performance("sandbox_creation", duration_ms, {
                'success': True,
                'dependencies_installed': bool(self.config.dependencies)
            })
            return self
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            log_error("Failed to create sandbox", exc_info=True, extra={
                'error_type': type(e).__name__,
                'duration_ms': duration_ms
            })
            raise SandboxError(f"Failed to create sandbox: {str(e)}")
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self._sandbox:
            try:
                log_debug("Destroying sandbox...")
                await self._sandbox.destroy()
                log_info("Sandbox destroyed successfully")
            except Exception as e:
                log_error("Error destroying sandbox", exc_info=True, extra={
                    'error_type': type(e).__name__
                })
    
    async def execute_code(self, code: str) -> Dict[str, Any]:
        """
        Execute code in the sandbox environment
        
        Args:
            code: Python code to execute
            
        Returns:
            Dictionary containing execution results:
                - success: bool indicating if execution was successful
                - output: stdout from the code execution
                - error: error message if execution failed
                - artifacts: any files or data produced by the code
        """
        if not self._sandbox:
            log_error("Sandbox not initialized")
            raise SandboxError("Sandbox not initialized. Use async context manager.")
            
        start_time = time.time()
        log_info("Executing code in sandbox", extra={
            'code_length': len(code)
        })
            
        try:
            # Execute the code
            log_debug("Running Python code...")
            process = await self._sandbox.run_python(code)
            
            duration_ms = (time.time() - start_time) * 1000
            result = {
                'success': process.exit_code == 0,
                'output': process.stdout,
                'error': process.stderr if process.exit_code != 0 else None,
                'exit_code': process.exit_code,
                'artifacts': [],  # TODO: Implement artifact collection if needed
                'execution_time_ms': duration_ms
            }
            
            log_performance("code_execution", duration_ms, {
                'success': result['success'],
                'exit_code': result['exit_code'],
                'output_length': len(result['output']) if result['output'] else 0,
                'error_length': len(result['error']) if result['error'] else 0
            })
            
            if not result['success']:
                log_warning("Code execution failed", extra={
                    'exit_code': result['exit_code'],
                    'error': result['error']
                })
            else:
                log_info("Code execution completed successfully")
                
            return result
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            log_error("Error executing code in sandbox", exc_info=True, extra={
                'error_type': type(e).__name__,
                'duration_ms': duration_ms
            })
            return {
                'success': False,
                'output': '',
                'error': str(e),
                'exit_code': 1,
                'artifacts': [],
                'execution_time_ms': duration_ms
            }

    @staticmethod
    async def quick_execute(code: str, config: SandboxConfig) -> Dict[str, Any]:
        """
        Static helper method for one-off code execution
        
        Args:
            code: Python code to execute
            config: SandboxConfig instance
            
        Returns:
            Execution results dictionary
        """
        log_info("Starting quick execute", extra={
            'code_length': len(code)
        })
        async with SecureSandbox(config) as sandbox:
            return await sandbox.execute_code(code) 