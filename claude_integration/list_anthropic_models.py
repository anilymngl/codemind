import anthropic
import os
from dotenv import load_dotenv

load_dotenv()

def list_anthropic_models():
    """Lists Claude models available through the Anthropic API."""
    api_key = os.environ.get("CLAUDE_API_KEY")
    if not api_key:
        print("Error: CLAUDE_API_KEY not found in environment variables.")
        return

    client = anthropic.Anthropic(api_key=api_key)

    try:
        response = client.models.list()
        print("Available Anthropic Models:")
        for model in response.data: # Use response.data to access the list of models
            print(f"- {model.id}") # Access model ID using model.id

    except Exception as e:
        print(f"Error listing models: {e}")

if __name__ == "__main__":
    list_anthropic_models() 