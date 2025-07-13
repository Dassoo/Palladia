from agno.models.openai import OpenAIChat
from agno.models.google import Gemini
from agno.models.anthropic import Claude
from agno.models.groq import Groq
from agno.models.mistral import MistralChat
from agno.models.nebius import Nebius
from agno.models.openrouter import OpenRouter
from dotenv import load_dotenv
import os

load_dotenv()

# List of models to evaluate
to_eval = [
    # # OpenAI models
    # OpenAIChat(id="gpt-4o"),
    
    # # Google models
    # Gemini(id="gemini-2.5-flash"),
    # Gemini(id="gemini-2.5-pro"),
    
    # # Mistral models
    # MistralChat(id="mistral-small-2506"),
    
    # # Groq models (Llama)
    Groq(id="meta-llama/llama-4-scout-17b-16e-instruct"),
    # Groq(id="meta-llama/llama-4-maverick-17b-128e-instruct"),
    
    # # Nebius models
    # Nebius(id="Qwen/Qwen2.5-VL-72B-Instruct", api_key=os.getenv("NEBIUS_API_KEY")),
    
    # # Anthropic models
    # Claude(id="claude-opus-4-20250514"),
    
    # # xAI models
    # OpenAIChat(id="grok-4-0709", api_key=os.getenv("XAI_API_KEY")),
    
    # # OpenRouter models
    # OpenRouter(id="arcee-ai/spotlight", api_key=os.getenv("OPENROUTER_API_KEY")),
    OpenRouter(id="qwen/qwen2.5-vl-72b-instruct:free", api_key=os.getenv("OPENROUTER_API_KEY")),
    # OpenRouter(id="open-gvlab/internvl-14b", api_key=os.getenv("OPENROUTER_API_KEY"))
]
