# backend/main.py
import os
import sys
import gradio as gr  # Import Gradio
import logging
from logger import log_info, log_error, log_debug, log_warning  # Import simplified logger functions
from fastapi import FastAPI, HTTPException

from gemini_integration.gemini_client import GeminiReasoner
from claude_integration.claude_client import ClaudeSynthesizer
from mvp_orchestrator.mvp_orchestrator import SimpleMVPOrchestrator  # You can use your existing orchestrator

from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

app = FastAPI()

gemini_key = os.environ.get("GEMINI_API_KEY")
claude_key = os.environ.get("CLAUDE_API_KEY")

if not gemini_key or not claude_key:
    raise ValueError("Please set GEMINI_API_KEY and CLAUDE_API_KEY in your .env file")

orchestrator = SimpleMVPOrchestrator(gemini_key=gemini_key, claude_key=claude_key)  # Initialize orchestrator


@app.post("/query")
async def process_query_api(user_query: str):
    """
    API endpoint to process user queries.
    """
    log_info(f"API query received: {user_query}")
    try:
        output_dict = await orchestrator.process_query(user_query)
        return {
            "reasoning": output_dict['gemini_output_xml'],  # Return Gemini reasoning as 'reasoning'
            "execution": output_dict['final_output_text']   # Return final output as 'execution'
        }
    except Exception as e:
        log_error(f"Error processing query via API: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# --- GRADIO UI (Optional - Keep if you want a basic web UI, remove if focusing on CLI for now) ---
async def process_query_gradio(user_query):  # NEW FUNCTION FOR GRADIO
    output_dict = await orchestrator.process_query(user_query)
    return (output_dict['gemini_output_xml'],
            output_dict['claude_output_xml'],
            output_dict['final_output_text'])


iface = gr.Interface(  # GRADIO INTERFACE DEFINITION
    fn=process_query_gradio,  # Function to call when input is submitted
    inputs=gr.Textbox(lines=4, placeholder="Enter your code completion query here..."),  # Input: Textbox
    outputs=[  # Outputs: 3 Textboxes
        gr.Textbox(label="Gemini Reasoning"),  # Changed label back to "Gemini Reasoning" - now displays list of thoughts
        gr.Textbox(label="Claude Thinking XML"),
        gr.Textbox(label="Final Output (Code Completion)")
    ],
    title="CodeMind MVP - Gradio UI",
    description="Enter a query and get code completion powered by Gemini and Claude."
)
# --- END GRADIO UI ---


if __name__ == "__main__":
    log_info("Starting backend application...")  # ADD LOG - Application start
    log_info(f"Current working directory: {os.getcwd()}")  # ADD LOG - Working directory
    log_info(f"Python executable path: {sys.executable}")  # ADD LOG - Python executable
    iface.launch(debug=True)  # Launch the Gradio interface (or remove if focusing only on API/CLI)