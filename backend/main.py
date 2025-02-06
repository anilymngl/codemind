# backend/main.py
import os
import sys
# Add project root to sys.path to allow imports from other modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import logging
from logger import log_info, log_error, log_debug, log_warning, log_performance
from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv
from typing import Dict, Any, Optional
import traceback
import time
import gradio as gr

from mvp_orchestrator.enhanced_orchestrator import UnifiedOrchestrator, OrchestratorConfig
from components.ui_components import UIComponents, UITheme
from components.error_display import (
    ErrorDisplay,
    ErrorCategory,
    ErrorSeverity,
    create_error_details
)

# Load environment variables
load_dotenv()

# Initialize logging
logger = logging.getLogger('codemind.backend')

# Initialize FastAPI app
app = FastAPI(title="CodeMind API")

# Initialize UI components globally
ui = None

def setup_logging():
    """Configure logging settings"""
    # Create logs directory if it doesn't exist
    logs_dir = os.path.join(os.getcwd(), 'logs')
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)
        
    # Log initial setup
    log_info("Logging system initialized", extra={
        'log_directory': logs_dir,
        'log_files': {
            'app': f'app_{time.strftime("%Y%m%d")}.log',
            'error': f'error_{time.strftime("%Y%m%d")}.log',
            'api': f'api_{time.strftime("%Y%m%d")}.log',
            'performance': f'performance_{time.strftime("%Y%m%d")}.log'
        }
    })

def create_orchestrator() -> UnifiedOrchestrator:
    """Create and configure the orchestrator"""
    log_info("Creating orchestrator...")
    
    # Check environment variables
    gemini_key = os.environ.get("GEMINI_API_KEY")
    claude_key = os.environ.get("CLAUDE_API_KEY")
    e2b_key = os.environ.get("E2B_API_KEY")

    # Log environment variable status
    log_info("Checking environment variables...")
    log_debug("Environment variables status", extra={
        'gemini_key_present': bool(gemini_key),
        'claude_key_present': bool(claude_key),
        'e2b_key_present': bool(e2b_key)
    })

    if not all([gemini_key, claude_key, e2b_key]):
        missing_vars = [
            var for var, val in {
                "GEMINI_API_KEY": gemini_key,
                "CLAUDE_API_KEY": claude_key,
                "E2B_API_KEY": e2b_key
            }.items() if not val
        ]
        error_msg = f"Missing environment variables: {', '.join(missing_vars)}"
        log_error("Missing required environment variables", extra={
            'missing_vars': missing_vars
        })
        raise ValueError(error_msg)

    log_info("All required environment variables are present")

    try:
        # Create orchestrator config
        log_debug("Creating orchestrator configuration...")
        config = OrchestratorConfig(
            gemini_key=gemini_key,
            claude_key=claude_key,
            e2b_key=e2b_key,
            use_streaming=True,
            use_thinking_model=True,
            sandbox_config={
                'template': 'python3',
                'timeout_ms': 30000,  # 30 seconds
                'memory_mb': 512
            }
        )
        log_debug("Orchestrator configuration created", extra={
            'use_streaming': config.use_streaming,
            'use_thinking_model': config.use_thinking_model,
            'sandbox_template': config.sandbox_config.template,
            'sandbox_timeout_ms': config.sandbox_config.timeout_ms
        })
        
        # Create orchestrator
        log_info("Initializing orchestrator...")
        orchestrator = UnifiedOrchestrator(config)
        log_info("Successfully created orchestrator")
        return orchestrator
        
    except Exception as e:
        log_error("Failed to create orchestrator", exc_info=True, extra={
            'error_type': type(e).__name__,
            'error_message': str(e)
        })
        raise

# Initialize orchestrator
orchestrator = create_orchestrator()

@app.post("/query")
async def process_query_api(user_query: str) -> Dict[str, Any]:
    """
    API endpoint to process user queries.
    """
    start_time = time.time()
    log_info("API query received", extra={
        'query_length': len(user_query)
    })
    
    try:
        result = await orchestrator.process_query(user_query)
        duration_ms = (time.time() - start_time) * 1000
        
        log_performance("api_query_processing", duration_ms, {
            'success': result.success,
            'has_code': bool(result.code),
            'has_reasoning': bool(result.reasoning)
        })
        
        return {
            "success": result.success,
            "code": result.code,
            "reasoning": result.reasoning,
            "metadata": result.metadata
        }
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        log_error("Error processing query via API", exc_info=True, extra={
            'error_type': type(e).__name__,
            'duration_ms': duration_ms,
            'query_length': len(user_query)
        })
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/run_sandbox")
async def run_sandbox_api(code: str) -> Dict[str, Any]:
    """
    API endpoint to execute code in the sandbox environment.
    
    Args:
        code: The code to execute in the sandbox
        
    Returns:
        Dictionary containing execution results:
            - success: bool indicating if execution was successful
            - output: stdout from the code execution
            - error: error message if execution failed
            - execution_time_ms: execution time in milliseconds
    """
    start_time = time.time()
    log_info("API sandbox execution request received", extra={
        'code_length': len(code)
    })
    
    try:
        result = await orchestrator.run_sandbox(code)
        duration_ms = (time.time() - start_time) * 1000
        
        log_performance("api_sandbox_execution", duration_ms, {
            'success': result['success'],
            'has_output': bool(result.get('output')),
            'has_error': bool(result.get('error'))
        })
        
        return result
        
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        log_error("Error executing code in sandbox via API", exc_info=True, extra={
            'error_type': type(e).__name__,
            'duration_ms': duration_ms,
            'code_length': len(code)
        })
        raise HTTPException(status_code=500, detail=str(e))

async def process_query_gradio(user_query: str) -> tuple[str, str, str, str]:
    """
    Process a query through the Gradio interface.
    
    Args:
        user_query: The user's query string
        
    Returns:
        Tuple of (thoughts, code, reasoning, error_display)
    """
    start_time = time.time()
    log_info("Processing Gradio query", extra={
        'query_length': len(user_query)
    })
    
    try:
        result = await orchestrator.process_query(user_query)
        
        if result.success:
            # Format thoughts
            thoughts = "\n".join([
                f"🤔 {thought}" for thought in result.reasoning.thoughts
            ]) if result.reasoning and result.reasoning.thoughts else "No explicit thoughts generated"
            
            # Get code and reasoning
            code = result.code or "No code generated"
            reasoning = result.reasoning.reasoning if result.reasoning else "No reasoning available"
            
            # Add success info to error display
            if ui and ui.error_display:
                error = create_error_details(
                    message="Query processed successfully",
                    category=ErrorCategory.SYSTEM,
                    severity=ErrorSeverity.INFO,
                    source="orchestrator",
                    details={
                        "query": user_query,
                        "processing_time": result.metadata.get("processing_time"),
                        "num_thoughts": len(result.reasoning.thoughts) if result.reasoning and result.reasoning.thoughts else 0
                    }
                )
                ui.error_display.tracker.add_error(error)
            
            duration_ms = (time.time() - start_time) * 1000
            log_performance("gradio_query_processing", duration_ms, {
                'success': True,
                'has_thoughts': bool(result.reasoning and result.reasoning.thoughts),
                'has_code': bool(result.code),
                'has_reasoning': bool(result.reasoning)
            })
            
            return thoughts, code, reasoning, ""  # Empty error display
            
        else:
            error_msg = f"Error: {result.error.message if result.error else 'Unknown error'}"
            
            # Track error if UI is available
            if ui and ui.error_display:
                error = create_error_details(
                    message=error_msg,
                    category=ErrorCategory.SYSTEM,
                    severity=ErrorSeverity.ERROR,
                    source="orchestrator",
                    details=result.error.details if result.error else None,
                    suggestion="Please try rephrasing your query or check the error details."
                )
                ui.error_display.tracker.add_error(error)
                error_display = ui.error_display.format_for_ui(error)
            else:
                error_display = error_msg
            
            duration_ms = (time.time() - start_time) * 1000
            log_performance("gradio_query_processing", duration_ms, {
                'success': False,
                'error_type': type(result.error).__name__ if result.error else 'Unknown'
            })
            
            return error_msg, error_msg, error_msg, error_display
            
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        log_error("Error in Gradio interface", exc_info=True, extra={
            'error_type': type(e).__name__,
            'duration_ms': duration_ms,
            'query_length': len(user_query)
        })
        error_msg = f"Error: {str(e)}"
        
        # Track unexpected error if UI is available
        if ui and ui.error_display:
            error = create_error_details(
                message=str(e),
                category=ErrorCategory.SYSTEM,
                severity=ErrorSeverity.CRITICAL,
                source="gradio_interface",
                stack_trace=traceback.format_exc(),
                suggestion="This is an unexpected error. Please report this issue."
            )
            ui.error_display.tracker.add_error(error)
            error_display = ui.error_display.format_for_ui(error)
        else:
            error_display = error_msg
        
        return error_msg, error_msg, error_msg, error_display

async def run_sandbox_code(code: str) -> tuple[str, str, str]:
    """
    Execute code in the sandbox environment for the Gradio UI.
    
    Args:
        code: The code to execute
        
    Returns:
        Tuple of (output_markdown, status_text, execution_time_text)
    """
    start_time = time.time()
    log_info("Running code in sandbox (UI)", extra={
        'code_length': len(code)
    })
    
    if not code or not code.strip():
        return (
            "⚠️ No code provided",
            "Error: Empty code",
            ""
        )
    
    try:
        # Execute code in sandbox
        result = await orchestrator.run_sandbox(code)
        duration_ms = (time.time() - start_time) * 1000
        
        log_performance("ui_sandbox_execution", duration_ms, {
            'success': result['success'],
            'has_output': bool(result.get('output')),
            'has_error': bool(result.get('error'))
        })
        
        # Format output for UI
        if result['success']:
            output_md = f"""
### 🎉 Execution Successful

**Output:**
```
{result.get('output', '(No output)')}
```
"""
            status = "✅ Success"
        else:
            output_md = f"""
### ❌ Execution Failed

**Error:**
```
{result.get('error', 'Unknown error')}
```
"""
            status = "❌ Failed"
            
        # Format execution time
        exec_time = f"⏱️ Execution time: {result.get('execution_time_ms', duration_ms):.2f}ms"
        
        return output_md, status, exec_time
        
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        log_error("Error in sandbox execution (UI)", exc_info=True, extra={
            'error_type': type(e).__name__,
            'duration_ms': duration_ms,
            'code_length': len(code)
        })
        
        error_md = f"""
### ❌ Execution Error

**Error:**
```
{str(e)}
```
"""
        return error_md, "❌ Error", f"⏱️ Time: {duration_ms:.2f}ms"

def create_ui() -> None:
    """Create and launch the Gradio UI"""
    log_info("Creating UI...")
    
    # Make ui accessible globally
    global ui
    
    # Initialize UI components
    ui = UIComponents()
    
    # Create async wrapper functions to handle tuple returns
    async def process_query_wrapper(query: str):
        result = await process_query_gradio(query)
        return result[0], result[1], result[2], result[3]
    
    async def run_sandbox_wrapper(code: str):
        result = await run_sandbox_code(code)
        return result[0], result[1], result[2]
    
    # Create the query API endpoint
    query_api = gr.Interface(
        fn=process_query_wrapper, 
        inputs=gr.Textbox(label="Query"),
        outputs=[
            gr.Textbox(label="Response"),
            gr.Textbox(label="Error"),
            gr.Textbox(label="Status"),
            gr.Textbox(label="Additional Info")
        ],
        title="Query API",
        description="Process a natural language query"
    )
    
    # Create the sandbox API endpoint
    sandbox_api = gr.Interface(
        fn=run_sandbox_wrapper,
        inputs=gr.Textbox(label="Code"),
        outputs=[
            gr.Textbox(label="Output"),
            gr.Textbox(label="Error"),
            gr.Textbox(label="Status")
        ],
        title="Sandbox API",
        description="Run code in a sandbox environment"
    )
    
    # Create the main interface
    main_interface = gr.Blocks()
    with main_interface:
        ui.create_interface(
            process_query_fn=process_query_gradio,
            run_sandbox_fn=run_sandbox_code,
            title="🧠 CodeMind - Creative Coding Assistant"
        )
    
    # Create a Blocks interface that combines all components
    demo = gr.TabbedInterface(
        [main_interface, query_api, sandbox_api],
        ["Main UI", "Query API", "Sandbox API"]
    )
    
    # Configure queue settings and launch
    demo.queue(
        max_size=20,                # Maximum queue size to prevent resource exhaustion
        default_concurrency_limit=3, # Default concurrency limit for all events
        status_update_rate="auto"   # Enable automatic status updates
    ).launch(
        server_name="127.0.0.1",  # Changed from 0.0.0.0 to 127.0.0.1
        server_port=7860,
        share=False,
        show_error=True,
        favicon_path="assets/favicon.ico",
        max_threads=40             # Use FastAPI default for thread pool
    )
    
    log_info("UI launched successfully", extra={
        'server': 'http://127.0.0.1:7860',  # Updated log message
        'max_threads': 40,
        'queue_size': 20,
        'concurrency_limit': 3
    })

def print_color(text: str, color: str = None) -> None:
    """Print colored text using ANSI escape codes"""
    colors = {
        'red': '\033[91m',
        'green': '\033[92m',
        'yellow': '\033[93m',
        'blue': '\033[94m',
        'magenta': '\033[95m',
        'cyan': '\033[96m',
        'white': '\033[97m',
        'bold': '\033[1m',
        'reset': '\033[0m'
    }
    if color and color in colors:
        print(f"{colors[color]}{text}{colors['reset']}")
    else:
        print(text)

def print_step(step: str, status: str = "...", color: str = "cyan") -> None:
    """Print a step in the startup sequence"""
    print_color(f"  {step:<50} {status}", color)

def print_startup_sequence():
    """Print the startup sequence with status updates"""
    # Clear screen
    print("\033[2J\033[H", end="")
    
    # Print initial banner
    print_color("""
 ██████╗ ██████╗ ██████╗ ███████╗███╗   ███╗██╗███╗   ██╗██████╗ 
██╔════╝██╔═══██╗██╔══██╗██╔════╝████╗ ████║██║████╗  ██║██╔══██╗
██║     ██║   ██║██║  ██║█████╗  ██╔████╔██║██║██╔██╗ ██║██║  ██║
██║     ██║   ██║██║  ██║██╔══╝  ██║╚██╔╝██║██║██║╚██╗██║██║  ██║
╚██████╗╚██████╔╝██████╔╝███████╗██║ ╚═╝ ██║██║██║ ╚████║██████╔╝
 ╚═════╝ ╚═════╝ ╚═════╝ ╚══════╝╚═╝     ╚═╝╚═╝╚═╝  ╚═══╝╚═════╝ 
""", "cyan")
    print_color("                  Creative Coding Assistant", "yellow")
    print_color("                     Version 1.0.0\n", "magenta")
    
    # Print initialization steps
    print_color("\n🚀 Initializing CodeMind...\n", "white")
    
    # Print system information
    print_color("System Information:", "blue")
    print_color(f"  • Python Version:    {sys.version.split()[0]}", "white")
    print_color(f"  • Working Directory: {os.path.basename(os.getcwd())}", "white")
    print_color(f"  • Platform:          {sys.platform}", "white")
    
    # Print configuration
    print_color("\nConfiguration:", "blue")
    print_color("  • Queue Size:        20", "white")
    print_color("  • Concurrency:       3", "white")
    print_color("  • Max Threads:       40", "white")
    
    # Print API information
    print_color("\nAPI Information:", "blue")
    print_color("  • Main UI:           http://127.0.0.1:7860", "green")
    print_color("  • API Endpoint:      http://127.0.0.1:7860/api", "green")
    print_color("  • Documentation:     http://127.0.0.1:7860/docs", "green")
    
    # Print model information
    print_color("\nAI Models:", "blue")
    print_color("  • Reasoning:         gemini-2.0-flash-thinking-exp-01-21", "white")
    print_color("  • Code Generation:   claude-3-5-sonnet-20241022", "white")
    
    # Print startup message
    print_color("\n🔧 Starting services...\n", "white")

if __name__ == "__main__":
    try:
        # Setup logging first
        setup_logging()
        
        # Print startup sequence
        print_startup_sequence()
        
        # Print progress steps
        print_step("Initializing logging system", "✓", "green")
        
        log_info("Starting CodeMind backend...")
        log_info("Environment information", extra={
            'cwd': os.getcwd(),
            'python_executable': sys.executable
        })
        
        # Initialize orchestrator
        print_step("Creating orchestrator", "...")
        orchestrator = create_orchestrator()
        print_step("Creating orchestrator", "✓", "green")
        
        # Create and launch UI
        print_step("Launching user interface", "...")
        create_ui()
        print_step("Launching user interface", "✓", "green")
        
        # Print final success message
        print_color("\n✨ CodeMind is ready!", "green")
        print_color("\nAccess points:", "blue")
        print_color("  📱 UI Interface:      http://127.0.0.1:7860", "green")
        print_color("  📚 API Documentation: http://127.0.0.1:7860/docs", "green")
        print_color("  🔍 API Explorer:      http://127.0.0.1:7860/api", "green")
        print_color("\nServer controls:", "blue")
        print_color("  🛑 Press Ctrl+C to stop the server", "yellow")
        print_color("  💡 Check logs in ./logs directory for detailed information", "white")
        print_color("\nHappy coding! 🚀\n", "magenta")
        
    except Exception as e:
        log_error("Failed to start application", exc_info=True, extra={
            'error_type': type(e).__name__,
            'error_message': str(e)
        })
        print_color("\n❌ Error starting CodeMind:", "red")
        print_color(f"  {str(e)}", "red")
        print_color("\nCheck the logs for more details.", "yellow")
        sys.exit(1)  # Exit with error code