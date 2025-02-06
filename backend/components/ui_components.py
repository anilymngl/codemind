"""Enhanced UI components for CodeMind"""
import gradio as gr
from typing import Dict, Any, Optional, Tuple, List
import logging
from dataclasses import dataclass
from datetime import datetime
from .error_display import ErrorDisplay, ErrorCategory, ErrorSeverity, create_error_details
from logger import log_info, log_error, log_debug, log_warning, log_performance
import time

logger = logging.getLogger(__name__)

@dataclass
class UITheme:
    """Theme configuration for UI components"""
    primary_hue: str = "indigo"
    secondary_hue: str = "slate"
    neutral_hue: str = "slate"
    
    @property
    def theme(self) -> gr.Theme:
        """Get the Gradio theme"""
        return gr.themes.Base(
            primary_hue=self.primary_hue,
            secondary_hue=self.secondary_hue,
            neutral_hue=self.neutral_hue,
            font=["Inter", "system-ui", "sans-serif"]
        ).set(
            background_fill_primary="*neutral_950",
            background_fill_secondary="*neutral_900",
            border_color_primary="*neutral_700",
            block_background_fill="*neutral_900",
            block_label_background_fill="*neutral_800",
            input_background_fill="*neutral_800",
            button_primary_background_fill="*primary_600",
            button_primary_background_fill_hover="*primary_700",
            button_secondary_background_fill="*neutral_700",
            button_secondary_background_fill_hover="*neutral_600",
            body_text_color="*neutral_200"
        )

class UIComponents:
    """Enhanced UI components with loading states and responsive design"""
    
    def __init__(self, theme: Optional[UITheme] = None):
        """Initialize UI components with theme"""
        log_debug("Initializing UI components...", extra={
            'theme': {
                'primary_hue': theme.primary_hue if theme else 'blue',
                'secondary_hue': theme.secondary_hue if theme else 'indigo',
                'neutral_hue': theme.neutral_hue if theme else 'gray'
            }
        })
        self.theme = theme or UITheme()
        self.error_display = ErrorDisplay()
        log_debug("UI components initialized", extra={
            'theme': {
                'primary_hue': self.theme.primary_hue,
                'secondary_hue': self.theme.secondary_hue,
                'neutral_hue': self.theme.neutral_hue
            }
        })
        
    def create_interface(
        self,
        process_query_fn,
        run_sandbox_fn,
        title: str = "🧠 CodeMind - Creative Coding Assistant"
    ) -> gr.Blocks:
        """Create the main interface with all components"""
        start_time = time.time()
        log_info("Creating Gradio interface...", extra={'title': title})
        
        css = self._get_css()
        
        with gr.Blocks(title=title, theme=self.theme.theme, css=css) as iface:
            self._create_header()
            
            # Add queue status display
            with gr.Row(elem_classes="queue-status-row"):
                queue_status = gr.Markdown(
                    value="Queue Status: Ready",
                    elem_classes="queue-status"
                )
            
            with gr.Tabs() as tabs:
                # Main Code Generation Tab
                with gr.Tab("💡 Code Generation", id="code_gen"):
                    log_debug("Creating code generation tab...")
                    query_components = self._create_query_section()
                    output_components = self._create_output_section()
                    
                    # Connect components with queue status updates
                    query_components.submit_btn.click(
                        fn=process_query_fn,
                        inputs=[query_components.input_box],
                        outputs=[
                            output_components.thoughts,
                            output_components.code,
                            output_components.reasoning,
                            output_components.error_output
                        ],
                        api_name="generate"
                    ).then(
                        fn=lambda: (
                            gr.Button(
                                value="🚀 Generate Code",
                                variant="primary",
                                interactive=True
                            ),
                            gr.Markdown("Queue Status: Ready")
                        ),
                        inputs=None,
                        outputs=[
                            query_components.submit_btn,
                            queue_status
                        ]
                    )
                    
                # Sandbox Tab
                with gr.Tab("🔬 Sandbox", id="sandbox"):
                    log_debug("Creating sandbox tab...")
                    sandbox_components = self._create_sandbox_section()
                    
                    # Connect sandbox components with queue status
                    sandbox_components.run_btn.click(
                        fn=run_sandbox_fn,
                        inputs=[sandbox_components.code_input],
                        outputs=[
                            sandbox_components.output,
                            sandbox_components.status,
                            sandbox_components.execution_time
                        ],
                        api_name="execute"
                    ).then(
                        fn=lambda: (
                            gr.Button(
                                value="▶️ Run Code",
                                variant="primary",
                                interactive=True
                            ),
                            gr.Markdown("Ready"),
                            gr.Markdown(visible=True),  # Show execution time
                            gr.Markdown("Queue Status: Ready")
                        ),
                        inputs=None,
                        outputs=[
                            sandbox_components.run_btn,
                            sandbox_components.status,
                            sandbox_components.execution_time,
                            queue_status
                        ]
                    )
                    
                # History Tab
                with gr.Tab("📜 History", id="history"):
                    log_debug("Creating history tab...")
                    self._create_history_section()
            
            # Add event handlers for loading states and queue updates
            self._add_loading_handlers(
                query_components,
                sandbox_components,
                queue_status
            )
            
        duration_ms = (time.time() - start_time) * 1000
        log_performance("ui_creation", duration_ms, {
            'num_tabs': 3,
            'has_error_display': bool(self.error_display)
        })
        
        return iface
    
    def _create_header(self):
        """Create the header section"""
        gr.Markdown("""
        # 🧠 CodeMind - Creative Coding Assistant
        
        ### Intelligent Code Generation & Execution
        
        Enter your coding idea or problem, and let CodeMind help you implement it!
        """)
    
    def _create_query_section(self) -> 'QueryComponents':
        """Create the query input section"""
        with gr.Row():
            with gr.Column(scale=2):
                input_box = gr.Textbox(
                    lines=4,
                    placeholder="Describe what you want to create or solve...",
                    label="Your Request",
                    elem_classes=["input-box", "main-input"]
                )
            with gr.Column(scale=1):
                submit_btn = gr.Button(
                    "🚀 Generate Code",
                    variant="primary",
                    size="lg"
                )
                
        return QueryComponents(input_box, submit_btn)
    
    def _create_output_section(self) -> 'OutputComponents':
        """Create the output display section"""
        start_time = time.time()
        log_debug("Creating output section components")
        
        # Thought Process Section
        with gr.Row():
            log_debug("Creating thought process section...")
            with gr.Accordion("💭 Thought Process", open=False, elem_classes="thought-process-section") as thought_accordion:
                gr.Markdown("""
                    **AI's Step-by-Step Thinking**
                    Below are the intermediate thoughts and considerations the AI had while processing your request.
                    These represent the model's "stream of consciousness" before formulating the final structured response.
                """, elem_classes="section-description")
                thoughts = gr.Markdown(elem_classes=["markdown-output", "thought-content"])
                
        # Reasoning Section
        with gr.Row():
            log_debug("Creating reasoning section...")
            with gr.Column(scale=4):
                gr.Markdown("### 🔍 Structured Reasoning", elem_classes="section-header")
                gr.Markdown("""
                    This section contains the AI's formal analysis, including:
                    - Technical requirements identified
                    - Implementation strategy
                    - Key considerations and constraints
                """, elem_classes="section-description")
                reasoning = gr.Markdown(elem_classes=["markdown-output", "reasoning-content"])
            
            with gr.Column(scale=6):
                log_debug("Creating code output section...")
                gr.Markdown("### 🎨 Generated Code", elem_classes="section-header")
                code = gr.Code(
                    language="python",
                    lines=25,
                    elem_classes="code-output"
                )
                
        # Error Display Section
        with gr.Row():
            log_debug("Creating error display section...")
            with gr.Accordion("⚠️ Errors & Warnings", open=False) as error_accordion:
                error_output = gr.Markdown(elem_classes="error-output")
                
        duration_ms = (time.time() - start_time) * 1000
        log_performance("output_section_creation", duration_ms, {
            'components': ['thoughts', 'reasoning', 'code', 'error_output']
        })
        
        return OutputComponents(thoughts, code, reasoning, error_output)
    
    def _create_sandbox_section(self) -> 'SandboxComponents':
        """Create the sandbox section for code execution"""
        with gr.Row():
            with gr.Column(scale=2):
                code_input = gr.Code(
                    label="Python Code",
                    language="python",
                    lines=15,
                    elem_classes="input-box sandbox-code"
                )
                gr.Markdown("""
                    Enter Python code to execute in the sandbox environment.
                    The code will be executed in an isolated environment with basic Python packages.
                    Execution time is limited to 30 seconds.
                """, elem_classes="section-description")
            
            with gr.Column(scale=1):
                run_btn = gr.Button(
                    "▶️ Run Code",
                    variant="primary",
                    size="lg",
                    elem_classes="sandbox-run-btn"
                )
                status = gr.Markdown("Ready", elem_classes="status-text")
                
        with gr.Row():
            with gr.Accordion("📝 Execution Results", open=True):
                output = gr.Markdown(
                    value="No execution results yet. Click 'Run Code' to execute.",
                    elem_classes=["markdown-output", "sandbox-output"]
                )
                
        # Add execution time display
        with gr.Row():
            execution_time = gr.Markdown(
                value="",
                elem_classes="execution-time",
                visible=False
            )
            
        return SandboxComponents(
            code_input=code_input,
            run_btn=run_btn,
            output=output,
            status=status,
            execution_time=execution_time
        )
    
    def _create_history_section(self):
        """Create the history section"""
        with gr.Row():
            gr.Markdown("### 📜 Recent Activity", elem_classes="section-header")
            
        with gr.Tabs():
            with gr.Tab("Queries"):
                history_list = gr.Dataframe(
                    headers=["Timestamp", "Query", "Status"],
                    elem_classes="history-list"
                )
                
            with gr.Tab("Errors"):
                with gr.Row():
                    with gr.Column(scale=2):
                        error_list = gr.Dataframe(
                            headers=["Time", "Severity", "Category", "Message"],
                            elem_classes="error-list"
                        )
                    with gr.Column(scale=1):
                        error_metrics = gr.JSON(label="Error Metrics")
                        
                with gr.Row():
                    refresh_btn = gr.Button("🔄 Refresh", size="sm")
                    clear_btn = gr.Button("🗑️ Clear History", size="sm", variant="stop")
                    
                    refresh_btn.click(
                        fn=lambda: (
                            self._get_error_list(),
                            self.error_display.get_error_metrics()
                        ),
                        outputs=[error_list, error_metrics]
                    )
                    
                    clear_btn.click(
                        fn=lambda: (
                            self.error_display.tracker.clear_history(),
                            [], # Empty error list
                            {} # Empty metrics
                        ),
                        outputs=[error_list, error_metrics]
                    )
    
    def _get_error_list(self) -> List[List[str]]:
        """Get formatted error list for display"""
        errors = self.error_display.tracker.get_recent_errors(limit=100)
        return [
            [
                e.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                e.severity.value,
                e.category.value,
                e.message
            ]
            for e in errors
        ]
    
    def _add_loading_handlers(
        self,
        query_components: 'QueryComponents',
        sandbox_components: 'SandboxComponents',
        queue_status: gr.Markdown
    ):
        """Add loading state handlers to components"""
        # Query loading state
        query_components.submit_btn.click(
            fn=lambda: (
                gr.Button(
                    value="⏳ Generating...",
                    variant="secondary",
                    interactive=False
                ),
                gr.Markdown("Queue Status: Processing...")
            ),
            inputs=None,
            outputs=[
                query_components.submit_btn,
                queue_status
            ],
            api_name=None,
            queue=False
        )
        
        # Sandbox loading state
        sandbox_components.run_btn.click(
            fn=lambda: (
                gr.Button(
                    value="⚙️ Running...",
                    variant="secondary",
                    interactive=False
                ),
                gr.Markdown("Executing..."),
                gr.Markdown("Queue Status: Processing...")
            ),
            inputs=None,
            outputs=[
                sandbox_components.run_btn,
                sandbox_components.status,
                queue_status
            ],
            api_name=None,
            queue=False
        )
    
    def _get_css(self) -> str:
        """Get the CSS styles for the UI"""
        base_css = """
        /* Container styling */
        .gradio-container { 
            max-width: 1400px !important;
            margin: auto !important;
            padding: 20px !important;
            background-color: #0f172a !important;  /* slate-950 */
        }

        /* Body styling */
        body {
            background-color: #0f172a !important;  /* slate-950 */
            color: #f1f5f9 !important;  /* slate-100 */
            font-family: 'Inter', system-ui, -apple-system, sans-serif !important;
        }
        
        /* Input/Output box styling */
        .input-box {
            border-radius: 8px !important;
            border: 1px solid #334155 !important;  /* slate-700 */
            background: #1e293b !important;  /* slate-800 */
            margin: 10px 0 !important;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1) !important;
        }
        
        .main-input {
            font-size: 1.1em !important;
            color: #f1f5f9 !important;  /* slate-100 */
            line-height: 1.6 !important;
            background: #1e293b !important;  /* slate-800 */
        }
        
        /* Section descriptions */
        .section-description {
            font-size: 1em !important;
            color: #cbd5e1 !important;  /* slate-300 */
            margin-bottom: 1em !important;
            padding: 12px !important;
            background: #1e293b !important;  /* slate-800 */
            border-radius: 6px !important;
            border: 1px solid #334155 !important;  /* slate-700 */
        }
        
        /* Thought Process styling */
        .thought-process-section {
            border-left: 4px solid #6366f1 !important;  /* indigo-500 */
            margin: 1em 0 !important;
            background: #1e293b !important;  /* slate-800 */
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1) !important;
        }
        
        .thought-content {
            background: #1e293b !important;  /* slate-800 */
            padding: 20px !important;
            border-radius: 8px !important;
            min-height: 100px !important;
            max-height: 400px !important;
            overflow-y: auto !important;
            font-size: 1.1em !important;
            line-height: 1.7 !important;
            color: #f1f5f9 !important;  /* slate-100 */
            border: 1px solid #334155 !important;  /* slate-700 */
        }
        
        .thought-content p {
            margin-bottom: 1em !important;
            padding-left: 20px !important;
            border-left: 3px solid #6366f1 !important;  /* indigo-500 */
            color: #f1f5f9 !important;  /* slate-100 */
        }
        
        /* Reasoning content styling */
        .reasoning-content {
            background: #1e293b !important;  /* slate-800 */
            padding: 20px !important;
            border-radius: 8px !important;
            min-height: 200px !important;
            max-height: 600px !important;
            overflow-y: auto !important;
            font-size: 1.1em !important;
            line-height: 1.7 !important;
            border: 1px solid #334155 !important;  /* slate-700 */
            border-left: 4px solid #6366f1 !important;  /* indigo-500 */
            color: #f1f5f9 !important;  /* slate-100 */
        }
        
        /* Code output styling */
        .code-output {
            font-family: 'JetBrains Mono', 'Fira Code', monospace !important;
            background: #0f172a !important;  /* slate-950 */
            color: #e2e8f0 !important;  /* slate-200 */
            padding: 20px !important;
            border-radius: 8px !important;
            min-height: 200px !important;
            max-height: 600px !important;
            overflow-y: auto !important;
            border: 1px solid #334155 !important;  /* slate-700 */
            font-size: 0.95em !important;
            line-height: 1.5 !important;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1) !important;
        }

        /* Code block styling */
        .code-block {
            background: #0f172a !important;  /* slate-950 */
            color: #e2e8f0 !important;  /* slate-200 */
            font-family: 'JetBrains Mono', 'Fira Code', monospace !important;
            padding: 1em !important;
            border-radius: 6px !important;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1) !important;
        }

        /* Section headers */
        .section-header {
            font-size: 1.4em !important;
            font-weight: 600 !important;
            margin: 1.2em 0 0.8em 0 !important;
            color: #6366f1 !important;  /* indigo-500 */
            padding-left: 12px !important;
            border-left: 4px solid #6366f1 !important;  /* indigo-500 */
        }

        /* Button styling */
        button.primary {
            background: #4f46e5 !important;  /* indigo-600 */
            color: white !important;
            border: none !important;
            padding: 12px 24px !important;
            border-radius: 6px !important;
            font-weight: 600 !important;
            transition: all 0.2s ease !important;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1) !important;
        }

        button.primary:hover {
            background: #4338ca !important;  /* indigo-700 */
            transform: translateY(-1px) !important;
            box-shadow: 0 6px 8px rgba(0, 0, 0, 0.15) !important;
        }

        button.secondary {
            background: #334155 !important;  /* slate-700 */
            color: #f1f5f9 !important;  /* slate-100 */
            border: none !important;
            padding: 12px 24px !important;
            border-radius: 6px !important;
            font-weight: 600 !important;
            transition: all 0.2s ease !important;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1) !important;
        }

        button.secondary:hover {
            background: #1e293b !important;  /* slate-800 */
            transform: translateY(-1px) !important;
            box-shadow: 0 6px 8px rgba(0, 0, 0, 0.15) !important;
        }

        /* Scrollbar styling */
        ::-webkit-scrollbar {
            width: 8px !important;
            height: 8px !important;
        }

        ::-webkit-scrollbar-track {
            background: #1e293b !important;  /* slate-800 */
            border-radius: 4px !important;
        }

        ::-webkit-scrollbar-thumb {
            background: #334155 !important;  /* slate-700 */
            border-radius: 4px !important;
        }

        ::-webkit-scrollbar-thumb:hover {
            background: #475569 !important;  /* slate-600 */
        }
        """ + self._get_additional_css()
        
        return base_css
        
    def _get_additional_css(self) -> str:
        """Get additional CSS styles"""
        return """
        /* Status text */
        .status-text {
            font-size: 0.95em !important;
            color: #cbd5e1 !important;  /* slate-300 */
            margin-top: 10px !important;
            font-weight: 500 !important;
        }
        
        /* Warning text */
        .warning-text {
            background: #451a03 !important;  /* amber-950 */
            color: #fbbf24 !important;  /* amber-400 */
            padding: 16px !important;
            border-radius: 8px !important;
            margin: 16px 0 !important;
            border-left: 4px solid #f59e0b !important;  /* amber-500 */
            font-weight: 500 !important;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1) !important;
        }
        
        /* History list */
        .history-list {
            height: 300px !important;
            overflow-y: auto !important;
            background: #1e293b !important;  /* slate-800 */
            border: 1px solid #334155 !important;  /* slate-700 */
            border-radius: 8px !important;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1) !important;
        }
        
        /* Error output styling */
        .error-output {
            background: #450a0a !important;  /* red-950 */
            border-left: 4px solid #dc2626 !important;  /* red-600 */
            padding: 16px !important;
            margin: 16px 0 !important;
            border-radius: 8px !important;
            color: #fca5a5 !important;  /* red-300 */
            font-weight: 500 !important;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1) !important;
        }
        
        .error-list {
            height: 400px !important;
            overflow-y: auto !important;
            background: #1e293b !important;  /* slate-800 */
            border: 1px solid #334155 !important;  /* slate-700 */
            border-radius: 8px !important;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1) !important;
        }
        
        /* Error severity colors */
        .severity-info {
            color: #60a5fa !important;  /* blue-400 */
            font-weight: 500 !important;
        }
        
        .severity-warning {
            color: #fbbf24 !important;  /* amber-400 */
            font-weight: 500 !important;
        }
        
        .severity-error {
            color: #f87171 !important;  /* red-400 */
            font-weight: 500 !important;
        }
        
        .severity-critical {
            color: #ef4444 !important;  /* red-500 */
            font-weight: 700 !important;
        }
        
        /* Responsive design */
        @media (max-width: 768px) {
            .gradio-container {
                padding: 12px !important;
            }
            
            .markdown-output,
            .code-output {
                min-height: 150px !important;
                max-height: 400px !important;
            }
        }
        
        /* Markdown styling */
        .markdown-output {
            color: #f1f5f9 !important;  /* slate-100 */
            background: #1e293b !important;  /* slate-800 */
            padding: 20px !important;
            border-radius: 8px !important;
            border: 1px solid #334155 !important;  /* slate-700 */
            line-height: 1.7 !important;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1) !important;
        }
        
        .markdown-output code {
            background: #0f172a !important;  /* slate-950 */
            color: #e2e8f0 !important;  /* slate-200 */
            padding: 3px 6px !important;
            border-radius: 4px !important;
            font-family: 'JetBrains Mono', 'Fira Code', monospace !important;
            font-size: 0.9em !important;
        }
        
        .markdown-output pre {
            background: #0f172a !important;  /* slate-950 */
            color: #e2e8f0 !important;  /* slate-200 */
            padding: 20px !important;
            border-radius: 8px !important;
            overflow-x: auto !important;
            font-family: 'JetBrains Mono', 'Fira Code', monospace !important;
            font-size: 0.9em !important;
            line-height: 1.5 !important;
            margin: 1em 0 !important;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1) !important;
        }
        
        /* Sandbox Styles */
        .sandbox-code {
            font-family: 'JetBrains Mono', monospace;
            border-radius: 8px;
            margin-bottom: 1rem;
        }
        
        .sandbox-output {
            padding: 1rem;
            border-radius: 8px;
            background-color: var(--neutral-800);
            margin-top: 1rem;
        }
        
        .sandbox-output pre {
            background-color: var(--neutral-900);
            padding: 1rem;
            border-radius: 4px;
            margin: 0.5rem 0;
        }
        
        .execution-time {
            font-family: 'JetBrains Mono', monospace;
            color: var(--neutral-400);
            font-size: 0.9rem;
            text-align: right;
            padding: 0.5rem;
            margin-top: 0.5rem;
        }
        
        .status-text {
            font-weight: bold;
            text-align: center;
            margin-top: 0.5rem;
        }
        
        .sandbox-run-btn {
            width: 100%;
            margin-top: 1rem;
        }
        
        /* Queue Status Styles */
        .queue-status-row {
            margin: 0.5rem 0;
            padding: 0.5rem;
            background: var(--neutral-900);
            border-radius: 8px;
            border: 1px solid var(--neutral-700);
        }
        
        .queue-status {
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.9rem;
            color: var(--neutral-400);
            text-align: center;
            padding: 0.25rem;
        }
        """

@dataclass
class QueryComponents:
    """Components for the query section"""
    input_box: gr.Textbox
    submit_btn: gr.Button

@dataclass
class OutputComponents:
    """Components for the output section"""
    thoughts: gr.Markdown
    code: gr.Code
    reasoning: gr.Markdown
    error_output: gr.Markdown

@dataclass
class SandboxComponents:
    """Components for the sandbox section"""
    code_input: gr.Code
    run_btn: gr.Button
    output: gr.Markdown
    status: gr.Markdown
    execution_time: gr.Markdown 