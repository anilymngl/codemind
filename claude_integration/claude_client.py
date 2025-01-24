# claude_integration/claude_client.py
import anthropic
import os
import logging
from logger import log_info, log_error, log_debug, log_warning # Import simplified logger functions
import logging
# Configure basic logger - adjust level as needed
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(module)s - %(message)s')
logger = logging.getLogger(__name__)

class ClaudeSynthesizer:
    def __init__(self, claude_key: str):
        self.client = anthropic.Anthropic(api_key=claude_key)

    async def synthesize(self, user_query: str, gemini_reasoning_list: list, gemini_full_response: str) -> str:
        log_info("--- ClaudeSynthesizer.synthesize() START ---")  # ADD LOG
        log_debug(f"ClaudeSynthesizer.synthesize() - User query received: {user_query}")  # ADD LOG - Log input query
        log_debug(f"ClaudeSynthesizer.synthesize() - Gemini Reasoning List (count): {len(gemini_reasoning_list)}")  # ADD LOG - Log count of Gemini Reasoning List
        if gemini_reasoning_list: # Log snippet of first thought if list is not empty
            log_debug(f"ClaudeSynthesizer.synthesize() - Gemini Reasoning (first thought snippet):\n{gemini_reasoning_list[0][:200]}...") # ADD LOG - print snippet of first Gemini thought
        log_debug(f"ClaudeSynthesizer.synthesize() - Gemini Full Response (first 200 chars) received:\n{gemini_full_response[:200]}...") # ADD LOG - print snippet of Gemini full response

        claude_prompt = f"""
<system>
- You are Claude-Coder, a leading AI code synthesis engine in a multi-model system.
- PRIMARY OBJECTIVE: Generate KILLER CODE COMPLETIONS. Functional, best practices, robust, clear.
- SYNTHESIZE and ENHANCE Gemini-Strategist's reasoning, which is PROVIDED AS ASSISTANT PREFILL.
- ALSO CONSIDER Gemini-Strategist's FULL RESPONSE provided in <gemini_full_response> for broader context.

**Your Role:**
- Code Synthesis Expert.
- Reasoning Amplifier. Translate Gemini's strategy (in ASSISTANT PREFILL) into code, add coding expertise.
- Best Practice Enforcer. Ensure high standards, error handling, documentation.

**Input - Gemini's Reasoning (Assistant Prefill) & Full Response:**
- Gemini-Strategist's reasoning is PROVIDED AS ASSISTANT PREFILL.  It is provided as a LIST OF THOUGHTS, separate from this user prompt.
- Gemini-Strategist's FULL RESPONSE is provided in <gemini_full_response> for additional context and insights.
- Your task is to FOLLOW and AMPLIFY the ASSISTANT PREFILL reasoning (LIST OF THOUGHTS) AND CONSIDER the full response to generate the code.

**Gemini Reasoning (Assistant Prefill) -  PROVIDED SEPARATELY AS A LIST OF THOUGHTS, DO NOT EXPECT IT IN THIS PROMPT TEXT.**

<gemini_full_response>
{gemini_full_response}  **(Gemini-Strategist's FULL RESPONSE for context)**
</gemini_full_response >

**Phase 1: Blueprint Analysis (ASSISTANT PREFILL - LIST OF THOUGHTS) & Full Response Context:**
- Gemini-Strategist has provided reasoning as ASSISTANT PREFILL - as a LIST OF THOUGHTS.
- REVIEW the ASSISTANT PREFILL reasoning carefully (it's provided as a SEPARATE LIST, not in this prompt).
- ALSO, REVIEW Gemini's FULL RESPONSE in <gemini_full_response> for additional context and insights.
- User Code Completion Request: {user_query}

**Phase 2: Strategy Formulation (Guided by ASSISTANT PREFILL - LIST OF THOUGHTS & Full Response):**
- Based on Gemini's ASSISTANT PREFILL reasoning (LIST OF THOUGHTS) AND considering Gemini's FULL RESPONSE, formulate a concrete code completion strategy.  This involves:
    - Coding patterns, algorithms (as suggested by Gemini - in prefill reasoning and/or full response).
    - Code structure, components (as suggested by Gemini - in prefill reasoning and/or full response).
    - Error handling, validation (amplify Gemini's suggestions - from prefill reasoning and/or full response).
    - Best practices from Gemini's reasoning (ENSURE adherence - potentially reinforced in full response).

**Phase 3: Code Generation (KILLER Completion - Guided by ASSISTANT PREFILL Reasoning - LIST OF THOUGHTS & Full Response):**
- Generate the KILLER code completion. Follow Phase 2 strategy, Gemini's ASSISTANT PREFILL reasoning (LIST OF THOUGHTS), AND consider Gemini's FULL RESPONSE.
    - Functionality: Address user request flawlessly.
    - Robustness: Error handling, validation, edge cases (amplify Gemini's suggestions - from prefill reasoning and/or full response).
    - Best Practices: Checklist + your expertise (ENSURE and AMPLIFY - potentially reinforced in full response).
    - Clarity & Readability: Clean, formatted, understandable code.
    - Documentation: Comments, docstrings.

**Phase 4: Output Structure & Explanation:**
- Structure output in `<structured_output>` XML:
    - `<code_completion>`: KILLER code snippet.
    - `<explanation>`: DETAILED explanation:
        - How it addresses request.
        - How it IMPLEMENTS Gemini's ASSISTANT PREFILL reasoning (LIST OF THOUGHTS) AND considers Gemini's full response.
        - Best practices used and WHY.
        - Implementation notes.
    - `<best_practices_applied>`: Bulleted list of best practices.
    - `<implementation_notes>`: [Generate notes here!]
    </structured_output>

<request>
**User Request:** {user_query}
</request>

<structured_output>
    <code_completion>
    [KILLER code completion here!]
    </code_completion>
    <explanation>
    [DETAILED explanation here!]
    </explanation>
    <best_practices_applied>
    [Best practices list here!]
    </best_practices_applied>
    <implementation_notes>
    [Implementation notes here!]
    </implementation_notes>
</structured_output>
        """ # Sharpened Claude Prompt - more directive, structured, value-focused with ASSISTANT PREFILL - now expects LIST OF THOUGHTS

        log_debug(f"ClaudeSynthesizer.synthesize() - Claude Prompt:\n{claude_prompt}") # ADD LOG - Log Claude Prompt

        log_info("ClaudeSynthesizer.synthesize() - Calling Claude model messages.create() with ASSISTANT PREFILL (LIST OF THOUGHTS)...") # ADD LOG - Before Claude model call
        messages_list = [
            {"role": "user", "content": claude_prompt.format(user_query=user_query, gemini_full_response=gemini_full_response)}, # User prompt - NO Gemini reasoning here
        ]
        for thought in gemini_reasoning_list: # Add each Gemini thought as a separate assistant message for prefill
            messages_list.append({"role": "assistant", "content": thought})

        response = self.client.messages.create(
            model="claude-3-sonnet-20240229",  # Or your preferred Claude model
            max_tokens=2048, # Increased max_tokens to allow for detailed explanations and code
            messages=messages_list # Use dynamically created messages list with user prompt and assistant prefill thoughts
        )
        log_info("Claude model messages.create() call completed (with ASSISTANT PREFILL - LIST OF THOUGHTS).") # ADD LOG - REMOVE PRINT
        log_debug(f"ClaudeSynthesizer.synthesize() - Claude Response Content (first 200 chars):\n{response.content[0].text[:200]}...")  # ADD LOG - print snippet of Claude response
        log_info("--- ClaudeSynthesizer.synthesize() END ---") # ADD LOG
        return response.content[0].text # Assuming response.content is a list and you want the first item's text