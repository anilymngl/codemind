# claude_integration/claude_client.py
import anthropic
import os
import logging
from typing import Dict, List
from logger import log_info, log_error, log_debug, log_warning  # Import simplified logger functions

# Configure basic logger - adjust level as needed
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(module)s - %(message)s')
logger = logging.getLogger(__name__)

class ClaudeSynthesizer:
    def __init__(self, claude_key: str):
        self.client = anthropic.Anthropic(api_key=claude_key)
        self.current_model = "claude-3-5-sonnet-20241022" # Set default model
        self.max_output_tokens = 8192 # Set default max tokens

    async def synthesize(self, user_query: str, gemini_reasoning_list: List[str], gemini_full_response: str) -> Dict[str, str]:
        log_info("--- ClaudeSynthesizer.synthesize() START ---")
        log_debug(f"ClaudeSynthesizer.synthesize() - User query received: {user_query}")
        log_debug(f"ClaudeSynthesizer.synthesize() - Gemini Reasoning List (count): {len(gemini_reasoning_list)}")
        if gemini_reasoning_list:
            log_debug(f"ClaudeSynthesizer.synthesize() - Gemini Reasoning (first thought snippet):\n{gemini_reasoning_list[0][:200]}...")
        log_debug(f"ClaudeSynthesizer.synthesize() - Gemini Full Response (first 200 chars) received:\n{gemini_full_response[:200]}...")

        thinking_content = "<thinking>\n" + "\n".join(gemini_reasoning_list) + "\n</thinking>"
        # Refined Prompt for Claude - Explicitly request code and tags
        claude_prompt = f"""
<user_query>
{user_query}
</user_query>

<thinking_process>
{thinking_content}
</thinking_process>

Based on the user query and the provided thinking process, please generate the code to create the interactive correlation tool.
**Enclose the complete code output within `<code_completion>` and `</code_completion>` XML tags.**
Return your response in XML format.
"""

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": claude_prompt} # Use the refined prompt
                ]
            },
            {
                "role": "assistant",
                "content": [
                    {"type": "text", "text": thinking_content} # Keep assistant_prefill as thinking content
                ]
            }
        ]

        response = await self.client.messages.create(
            model=self.current_model,
            messages=messages,
            max_tokens=self.max_output_tokens,
        )
        log_info("Claude model messages.create() call completed (with ASSISTANT PREFILL - LIST OF THOUGHTS).")
        log_debug(f"ClaudeSynthesizer.synthesize() - **Raw Claude Full Response Object:**\n{response}") # Log the raw response object
        if not response.content:
            log_warning("ClaudeSynthesizer.synthesize() - Claude response content is empty!")
            return {
                'claude_output_xml': "<error>Claude API returned empty content. Check logs for full response object.</error>",
                'claude_full_response': "<error>Empty Claude response content</error>"
            }

        # Only access response.content[0] if response.content is not empty
        if response.content: # ADD THIS CHECK: Ensure response.content is not empty
            log_debug(f"ClaudeSynthesizer.synthesize() - Claude Response Content (first 200 chars):\n{response.content[0].text[:200]}...")
            claude_output_xml = response.content[0].text
            log_debug(f"ClaudeSynthesizer.synthesize() - claude_output_xml (first 200 chars):\n{claude_output_xml[:200]}...")
        else: # Handle the case where response.content is empty
            claude_output_xml = "<error>Claude API returned empty content. Check logs for full response object.</error>" # Or a more informative message
            log_warning("ClaudeSynthesizer.synthesize() - Claude response content is empty, cannot extract text.") # Log warning

        return {
            'claude_output_xml': claude_output_xml,
            'claude_full_response': str(response)
        }