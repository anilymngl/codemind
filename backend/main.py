# backend/main.py
import os
import sys
import gradio as gr  # Import Gradio
import logging
from logger import log_info, log_error, log_debug, log_warning # Import simplified logger functions

from gemini_integration.gemini_client import GeminiReasoner
from claude_integration.claude_client import ClaudeSynthesizer 
from mvp_orchestrator.mvp_orchestrator import SimpleMVPOrchestrator

from dotenv import load_dotenv
load_dotenv() # Load environment variables from .env file

gemini_api_key = os.environ.get("GEMINI_API_KEY")
claude_api_key = os.environ.get("CLAUDE_API_KEY")

orchestrator = SimpleMVPOrchestrator(gemini_key=gemini_api_key, claude_key=claude_api_key) # Initialize your orchestrator

class SimpleMVPOrchestrator: # Keep your orchestrator class definition - NO CHANGES NEEDED
    def __init__(self, gemini_key: str, claude_key: str):
        self.reasoner = GeminiReasoner(gemini_key=gemini_key)
        self.synthesizer = ClaudeSynthesizer(claude_key=claude_key)

    async def process_query(self, user_query: str) -> dict:
        log_info("--- SimpleMVPOrchestrator.process_query() START ---") # ADD LOG
        log_debug(f"Processing user query: {user_query}") # ADD LOG

        log_info("Calling self.reasoner.get_reasoning()...") # ADD LOG
        gemini_output = await self.reasoner.get_reasoning(user_query=user_query)
        log_info("self.reasoner.get_reasoning() call completed.") # ADD LOG
        log_debug(f"Gemini Output (first 200 chars of response): {gemini_output['response'][:200]}...") # ADD LOG - print snippet

        log_info("Calling self.synthesizer.synthesize()...") # ADD LOG
        claude_output_xml = await self.synthesizer.synthesize(user_query=user_query, gemini_reasoning_list=gemini_output['thoughts'], gemini_full_response=gemini_output['response'])
        log_info("self.synthesizer.synthesize() call completed.") # ADD LOG
        log_debug(f"Claude Output XML (first 200 chars): {claude_output_xml[:200]}...")

        # WRITE FULL CLAUDE XML TO FILE - REPLACING TERMINAL PRINT
        try:
            with open("claude_xml_log.txt", "w", encoding="utf-8") as log_file: # Open claude_xml_log.txt in write mode ('w') and UTF-8 encoding
                log_file.write("--- FULL Claude Output XML: ---\n") # Write start marker
                log_file.write(claude_output_xml) # Write the Claude XML to the file
                log_file.write("\n--- END FULL Claude Output XML ---\n") # Write end marker
            print("Full Claude XML output written to claude_xml_log.txt") # Confirmation message to terminal - KEEP PRINT FOR USER INFO
        except Exception as e: # ADD LOGGING FOR FILE WRITING ERROR
            log_error(f"Error writing Claude XML to claude_xml_log.txt: {e}") # Error handling in case file writing fails

        log_info("Starting string-based extraction of code_completion...") # ADD LOG
        # ROBUST STRING-BASED EXTRACTION of <code_completion> - REPLACING XML PARSING
        final_output_text = "Error during code completion extraction" # Default in case of extraction error
        start_tag = "<code_completion>"
        end_tag = "</code_completion>"

        start_index = claude_output_xml.find(start_tag)
        end_index = claude_output_xml.find(end_tag)

        if start_index != -1 and end_index != -1 and start_index < end_index:
            start_pos = start_index + len(start_tag)
            final_output_text = claude_output_xml[start_pos:end_index].strip()
            log_info("Successfully extracted code_completion text using string manipulation.") # ADD LOG
        else:
            final_output_text = "Warning: <code_completion> tag not found or malformed in Claude output"
            log_warning("Warning: <code_completion> tag not found or malformed in Claude output.") # ADD LOG

        log_info("String-based extraction completed.") # ADD LOG

        log_info("--- SimpleMVPOrchestrator.process_query() END ---") # ADD LOG
        return {
            "gemini_output_xml": gemini_output['thoughts'], # Changed to return list of thoughts
            "claude_output_xml": claude_output_xml,
            "final_output_text": final_output_text
        }


async def process_query_gradio(user_query): # NEW FUNCTION FOR GRADIO
    output_dict = await orchestrator.process_query(user_query)
    return (output_dict['gemini_output_xml'],
            output_dict['claude_output_xml'],
            output_dict['final_output_text'])


iface = gr.Interface( # GRADIO INTERFACE DEFINITION
    fn=process_query_gradio, # Function to call when input is submitted
    inputs=gr.Textbox(lines=4, placeholder="Enter your code completion query here..."), # Input: Textbox
    outputs=[ # Outputs: 3 Textboxes
        gr.Textbox(label="Gemini Reasoning"), # Changed label back to "Gemini Reasoning" - now displays list of thoughts
        gr.Textbox(label="Claude Thinking XML"),
        gr.Textbox(label="Final Output (Code Completion)")
    ],
    title="CodeMind MVP - Gradio UI",
    description="Enter a query and get code completion powered by Gemini and Claude."
)

if __name__ == "__main__":
    log_info("Starting backend application...") # ADD LOG - Application start
    log_info(f"Current working directory: {os.getcwd()}") # ADD LOG - Working directory
    log_info(f"Python executable path: {sys.executable}") # ADD LOG - Python executable
    iface.launch(debug=True) # Launch the Gradio interface
