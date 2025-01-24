# mvp_orchestrator/mvp_orchestrator.py
from logger import log_info, log_error, log_debug, log_warning # Import simplified logger functions
import logging
# Configure basic logger - adjust level as needed
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(module)s - %(message)s')
logger = logging.getLogger(__name__)

from gemini_integration.gemini_client import GeminiReasoner
from claude_integration.claude_client import ClaudeSynthesizer

class SimpleMVPOrchestrator:
    def __init__(self, gemini_key: str, claude_key: str):
        self.reasoner = GeminiReasoner(gemini_key=gemini_key)
        self.synthesizer = ClaudeSynthesizer(claude_key=claude_key)

    async def process_query(self, user_query: str) -> dict:
        log_info("--- MVP Orchestrator: Processing Query START ---") # HIGH-LEVEL LOG - Start of query processing
        log_info(f"   User Query: {user_query}") # HIGH-LEVEL LOG - User query - KEEP for simple overview

        log_info("   [Orchestrator] Calling Gemini for reasoning...") # HIGH-LEVEL LOG - Start Gemini reasoning
        log_debug("--- SimpleMVPOrchestrator.process_query() START (Detailed) ---")  # DETAILED LOG - Function entry
        log_debug(f"SimpleMVPOrchestrator.process_query() - User query received: {user_query}")  # DETAILED LOG - Log input
        log_debug("SimpleMVPOrchestrator.process_query() - Calling GeminiReasoner.get_reasoning()...")  # DETAILED LOG - Before Gemini call
        gemini_output = await self.reasoner.get_reasoning(user_query=user_query)
        log_debug("SimpleMVPOrchestrator.process_query() - GeminiReasoner.get_reasoning() call completed.")  # DETAILED LOG - After Gemini call
        log_debug(f"SimpleMVPOrchestrator.process_query() - Gemini Output Keys: {gemini_output.keys()}") # DETAILED LOG - Log keys of Gemini output
        log_debug(f"SimpleMVPOrchestrator.process_query() - Gemini Thoughts (first thought snippet): {gemini_output.get('thoughts', [''])[0][:200]}...") # DETAILED LOG - Log snippet of first thought
        log_debug(f"SimpleMVPOrchestrator.process_query() - Gemini Response (first 200 chars): {gemini_output.get('response', '')[:200]}...")  # DETAILED LOG - Log snippet of Gemini response
        log_debug("--- SimpleMVPOrchestrator.process_query() END (Detailed) ---")  # DETAILED LOG - Function exit
        log_info("   [Orchestrator] Gemini reasoning COMPLETED.") # HIGH-LEVEL LOG - End Gemini reasoning

        log_info("   [Orchestrator] Calling Claude for synthesis...") # HIGH-LEVEL LOG - Start Claude synthesis
        log_debug("--- SimpleMVPOrchestrator.process_query() START (Detailed) ---")  # DETAILED LOG - Function entry
        log_debug(f"SimpleMVPOrchestrator.process_query() - Calling ClaudeSynthesizer.synthesize()...")  # DETAILED LOG - Before Claude call
        log_debug(f"SimpleMVPOrchestrator.process_query() - Gemini Thoughts (first thought snippet for Claude): {gemini_output.get('thoughts', [''])[0][:200]}...")  # DETAILED LOG - print snippet of Gemini thoughts for Claude
        log_debug(f"SimpleMVPOrchestrator.process_query() - Gemini Full Response (first 200 chars for Claude): {gemini_output.get('response', '')[:200]}...")  # DETAILED LOG - print snippet of Gemini full response for Claude

        claude_output_xml = await self.synthesizer.synthesize(user_query=user_query, gemini_reasoning_list=gemini_output['thoughts'], gemini_full_response=gemini_output['response']) # Pass Gemini THOUGHTS LIST and FULL RESPONSE to Claude
        log_debug("SimpleMVPOrchestrator.process_query() - ClaudeSynthesizer.synthesize() call completed.")  # DETAILED LOG - After Claude call
        log_debug(f"SimpleMVPOrchestrator.process_query() - Claude Output XML (first 200 chars): {claude_output_xml[:200]}...")  # DETAILED LOG - print snippet
        log_debug("--- SimpleMVPOrchestrator.process_query() END (Detailed) ---")  # DETAILED LOG - Function exit
        log_info("   [Orchestrator] Claude synthesis COMPLETED.") # HIGH-LEVEL LOG - End Claude synthesis

        # VERY BASIC XML PARSING - JUST GET code_completion text
        log_debug("SimpleMVPOrchestrator.process_query() - Starting string-based extraction of code_completion...") # DETAILED LOG - Before extraction - KEEP
        import xml.etree.ElementTree as ET
        final_output_text = "Error during XML parsing" # Default in case of parsing error
        try:
            log_debug("SimpleMVPOrchestrator.process_query() - Attempting XML parsing...") # Debug log before XML parsing
            # ... (rest of your XML parsing code - no logging changes needed here if you removed XML parsing)
            pass # Placeholder - assuming you removed XML parsing
            log_debug("SimpleMVPOrchestrator.process_query() - XML parsing completed (if code is still active).") # Debug log after XML parsing
        except Exception as e:
            log_error(f"XML Parse Error in Claude output (if XML parsing is still active): {e}", extra={
                "exception": str(e),
                "claude_output_xml_snippet": claude_output_xml[:500] # Log a snippet of Claude XML for context
            }) # More detailed error log with Claude XML snippet

        log_debug("SimpleMVPOrchestrator.process_query() - String-based extraction completed.") # DETAILED LOG - After extraction - KEEP
        # ROBUST STRING-BASED EXTRACTION of <code_completion> - REPLACING XML PARSING
        final_output_text = "Error during code completion extraction" # Default in case of extraction error
        start_tag = "<code_completion>"
        end_tag = "</code_completion>"

        log_debug("SimpleMVPOrchestrator.process_query() - Starting string-based <code_completion> extraction...") # More specific debug log - KEEP
        start_index = claude_output_xml.find(start_tag)
        end_index = claude_output_xml.find(end_tag)

        if start_index != -1 and end_index != -1 and start_index < end_index:
            start_pos = start_index + len(start_tag)
            final_output_text = claude_output_xml[start_pos:end_index].strip()
            log_info("Successfully extracted code_completion text using string manipulation.") # INFO log for success - KEEP
        else:
            final_output_text = "Warning: <code_completion> tag not found or malformed in Claude output"
            log_warning("Warning: <code_completion> tag not found or malformed in Claude output.") # Warning log - KEEP

        log_info("--- MVP Orchestrator: Processing Query END ---") # HIGH-LEVEL LOG - End of query processing
        return { # Return dictionary
            "gemini_output_xml": gemini_output['response'], # Keep passing full Gemini response for now (might be useful for debugging)
            "claude_output_xml": claude_output_xml,
            "final_output_text": final_output_text
        }