import google.generativeai as genai
import os
from dotenv import load_dotenv
load_dotenv() # Load environment variables from .env file
# Configure the API key
api_key= os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=api_key)

# List all available models
models = genai.list_models()

# Print the model names
for model in models:
    print(model.name)