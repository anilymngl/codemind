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
        log_debug(f"SimpleMVPOrchestrator.process_query() - Gemini Output: {gemini_output.dict()}")  # DETAILED LOG - Log Gemini output
        log_info("   [Orchestrator] Gemini reasoning COMPLETED.") # HIGH-LEVEL LOG - End Gemini reasoning

        log_info("   [Orchestrator] Calling Claude for synthesis...") # HIGH-LEVEL LOG - Start Claude synthesis
        try:
            log_debug("--- SimpleMVPOrchestrator.process_query() START (Detailed) ---")  # DETAILED LOG - Function entry
            log_debug(f"SimpleMVPOrchestrator.process_query() - Calling ClaudeSynthesizer.synthesize()...")  # DETAILED LOG - Before Claude call
            log_debug(f"SimpleMVPOrchestrator.process_query() - Gemini Reasoning: {gemini_output.dict()}")  # DETAILED LOG - print Gemini reasoning

            claude_output = await self.synthesizer.synthesize(
                user_query=user_query, 
                structured_reasoning=gemini_output.dict()
            )
            log_debug("SimpleMVPOrchestrator.process_query() - ClaudeSynthesizer.synthesize() call completed.")  # DETAILED LOG - After Claude call
            log_debug(f"SimpleMVPOrchestrator.process_query() - Claude Output: {claude_output.dict()}")  # DETAILED LOG - print output
            log_debug("--- SimpleMVPOrchestrator.process_query() END (Detailed) ---")  # DETAILED LOG - Function exit
        except Exception as e:
            log_error(f"SimpleMVPOrchestrator.process_query() - Claude synthesis FAILED: {e}")
            claude_output = None

        log_info("   [Orchestrator] Claude synthesis COMPLETED.") # HIGH-LEVEL LOG - End Claude synthesis

        log_info("--- MVP Orchestrator: Processing Query END ---") # HIGH-LEVEL LOG - End of query processing
        return { # Return dictionary
            "gemini_output": gemini_output.dict() if gemini_output else None,
            "claude_output": claude_output.dict() if claude_output else None,
            "final_output_text": claude_output.code_completion if claude_output else "Error during code generation"
        }