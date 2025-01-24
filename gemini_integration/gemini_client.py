# gemini_integration/gemini_client.py
import google.generativeai as genai
import logging
from logger import log_info, log_error, log_debug, log_warning

from google.genai import types # Import the types module - needed for GenerateContentConfig and ThinkingConfig

class GeminiReasoner:
    def __init__(self, gemini_key: str):
        self.gemini_key = gemini_key
        # Initialize Gemini client using genai.Client and specify api_version='v1alpha' - NEW WAY based on docs
        self.client = genai.Client(api_key=gemini_key, http_options={'api_version':'v1alpha'}) # Initialize genai.Client with api_version - Client Instance is enough, no need to get model separately

    async def get_reasoning(self, user_query: str) -> dict:
        log_info("--- GeminiReasoner.get_reasoning() START ---")
        log_debug(f"GeminiReasoner.get_reasoning() - User query received: {user_query}")

        gemini_prompt = f"""
<system>
- You are a world-class AI that excels at Chain of Thought reasoning.
- Analyze the following user code completion request and generate a detailed, structured reasoning process.
- Think step-by-step and explicitly show your reasoning. Consider multiple angles and potential approaches.
- User Code Completion Request:
{user_query}

- Provide your reasoning in a well-structured format. Be thorough and provide sufficient detail in each section to guide Claude effectively.

**Objective:** Generate a detailed, structured reasoning to guide Claude in creating a code completion for the user's request.

**Reasoning Guidelines:**
- Think step-by-step to analyze the user's request.
- Explore different angles and potential approaches to the code completion.
- Focus on providing practical insights and a logical flow that Claude can follow.
- Structure your reasoning logically using clear sections and steps.

**User Code Completion Request:**
{user_query}

**Output Format:** Provide your reasoning in a clear and structured manner. Be detailed and aim to create a helpful blueprint for Claude.
 </system>
        """

        log_debug(f"GeminiReasoner.get_reasoning() - Gemini Prompt:\n{gemini_prompt}")

        log_info("GeminiReasoner.get_reasoning() - Calling Gemini model generate_content() with thinking_config...") # ADD LOG

        # Generate content using the model - using client.models.generate_content directly - NEW WAY based on docs
        config = types.GenerateContentConfig(  # config is still needed for thinking_config
            thinking_config=types.ThinkingConfig(include_thoughts=True)
        ) # Remove .to_dict() - GenerateContentConfig object should be passed directly

        response = self.client.models.generate_content( # Call generate_content on client.models, passing model name as argument
            contents=[types.Part.from_text(gemini_prompt.format(user_query=user_query))], # Wrap prompt in types.Part.from_text - as per some examples
            config=config, # Pass thinking_config to the generate_content call
            model='gemini-2.0-flash-thinking-exp' # Specify model name here - as per docs
        )


        log_info("GeminiReasoner.get_reasoning() - Gemini model generate_content() call completed.")
        if response.text is None:
            log_error("GeminiReasoner.get_reasoning() - Gemini response text is None!")
            log_debug(f"GeminiReasoner.get_reasoning() - Full Gemini response object: {response}") # Log full response for debugging
            model_response = "" # Or handle None response as needed, e.g., return empty string or raise exception
        else:
            log_debug(f"GeminiReasoner.get_reasoning() - Gemini Response (first 200 chars):\n{response.text[:200]}...")
            model_response = response.text.strip()

        gemini_thoughts = [] # Initialize list to store Gemini's thoughts
        gemini_response_text = "" # Initialize string to store Gemini's main response

        if response.candidates and response.candidates[0].content and response.candidates[0].content.parts: # Check for response parts safely
            for part in response.candidates[0].content.parts: # Iterate through response parts
                if part.thought: # Check if part is a thought
                    gemini_thoughts.append(part.text) # Add thought text to thoughts list
                    log_debug(f"GeminiReasoner.get_reasoning() - Extracted Gemini Thought: {part.text[:100]}...") # Log extracted thought snippet
                else:
                    gemini_response_text += part.text + "\n" # Append non-thought part to response text
                    log_debug(f"GeminiReasoner.get_reasoning() - Extracted Gemini Response Part: {part.text[:100]}...") # Log response part snippet
        else:
            log_warning("GeminiReasoner.get_reasoning() - Warning: No candidates or content parts found in Gemini response.") # Log warning if no parts found


        log_info("--- GeminiReasoner.get_reasoning() END ---")

        # Extract the response text - now handled part-by-part above
        # model_response = response.text.strip() # No longer directly extracting response.text

        return {
            "thoughts": gemini_thoughts, # Return list of Gemini thoughts
            "response": model_response
        }