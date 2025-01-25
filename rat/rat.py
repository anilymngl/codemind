import os
from dotenv import load_dotenv
from rich import print as rprint
from rich.panel import Panel
from prompt_toolkit import PromptSession
from prompt_toolkit.styles import Style
import time
import asyncio  # Import asyncio
from logger import log_info, log_error, log_debug, log_warning
from mvp_orchestrator.mvp_orchestrator import SimpleMVPOrchestrator

# Load environment variables
load_dotenv()

class CLICodeMind:
    def __init__(self, orchestrator):
        self.orchestrator = orchestrator
        self.current_model = "Claude"
        self.show_reasoning = True

    def set_model(self, model_name):
        self.current_model = model_name
        rprint(f"\n[green]Model set to {self.current_model}[/]")

    async def process_query(self, user_input):
        log_info(f"CLI processing query: {user_input}")
        return await self.orchestrator.process_query(user_input)

async def main():
    gemini_key = os.getenv("GEMINI_API_KEY")
    claude_key = os.getenv("CLAUDE_API_KEY")

    if not gemini_key or not claude_key:
        rprint("[red]Error:[/] Please set GEMINI_API_KEY and CLAUDE_API_KEY in your .env file.")
        return

    orchestrator = SimpleMVPOrchestrator(gemini_key=gemini_key, claude_key=claude_key)
    cli_app = CLICodeMind(orchestrator)
    session = PromptSession()

    rprint(Panel.fit("[bold cyan]CodeMind MVP - CLI Demo (Reasoned Execution)[/]", title="CodeMind 🧠", border_style="cyan"))
    rprint("[yellow]Commands:[/]")
    rprint(" • [bold red]quit[/] to exit")
    rprint(" • [bold magenta]model <name>[/] to change model (Claude models - optional)")
    rprint(" • [bold magenta]reasoning[/] to toggle reasoning visibility\n")

    while True:
        try:
            # Corrected line: Await prompt_async, then strip the *result*
            user_input_coroutine = session.prompt_async("\nYou: ", style=Style.from_dict({'prompt': 'orange bold'}))
            user_input = await user_input_coroutine # Await the coroutine to get the string
            user_input = user_input.strip() # *Now* strip the string

            if user_input.lower() == "quit":
                rprint("\n[green]Goodbye![/]")
                break
            elif user_input.lower().startswith("model"):
                cli_app.set_model(user_input.split(" ", 1)[1])
                continue
            elif user_input.lower() == "reasoning":
                cli_app.show_reasoning = not cli_app.show_reasoning
                rprint(f"Reasoning visibility set to {cli_app.show_reasoning}")
                continue

            output_dict = await cli_app.process_query(user_input)

            if cli_app.show_reasoning:
                rprint(Panel(output_dict['gemini_output_reasoning'], title="Gemini Reasoning", border_style="blue")) # Use new key
            # Display FULL Claude XML Output - Replacing final_output_text
            rprint(Panel(output_dict['claude_output_xml'], title="Claude XML Output (Full)", border_style="green")) # Show Claude XML Output

        except KeyboardInterrupt:
            continue
        except EOFError:
            break

if __name__ == "__main__":
    loop = asyncio.get_event_loop() # Get current event loop
    loop.run_until_complete(main()) # Run main within the event loop