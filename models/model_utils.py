import os
from typing import List, Any
from rich.console import Console

from agno.models.openai import OpenAIChat
from agno.models.google import Gemini
from agno.models.anthropic import Claude
from agno.models.groq import Groq
from agno.models.mistral import MistralChat
from agno.models.nebius import Nebius
from agno.models.xai import xAI
from agno.models.openrouter import OpenRouter
from agno.models.huggingface import HuggingFace
from agno.models.deepseek import DeepSeek
from dotenv import load_dotenv

from config.loader import load_config
from config.schemas import AppConfig

load_dotenv()
console = Console()

# Global mapping from model IDs to standardized names
_model_id_to_standard_name = {}

def get_enabled_models() -> List[Any]:
    """Get a list of initialized model instances based on validated configuration."""
    try:
        app_config: AppConfig = load_config(verbose=False)  # Silent loading for module import
    except Exception as e:
        console.print(f"❌ Configuration error: {e}", style="bold red")
        return []
    
    enabled_models = []
    
    # Map of provider names to their actual classes
    model_classes = {
        'OpenAI': OpenAIChat,
        'Google': Gemini,
        'Anthropic': Claude,
        'Groq': Groq,
        'Mistral': MistralChat,
        'Nebius': Nebius,
        'xAI': xAI,
        'OpenRouter': OpenRouter,
        'HuggingFace': HuggingFace,
        'DeepSeek': DeepSeek
    }
    
    for model_cfg in app_config.enabled_models:
        provider = model_cfg.provider
        model_id = model_cfg.id
        
        # Check if API key is available
        api_key = os.getenv(model_cfg.api_key_env)
        if not api_key:
            console.print(f"⚠ Skipping {model_id}: Missing API key {model_cfg.api_key_env}", style="yellow")
            continue
        
        # Initialize the model
        try:
            model_class = model_classes[provider]
            model_instance = model_class(id=model_id, api_key=api_key)
            enabled_models.append(model_instance)
            
            # Store the mapping from model ID to standardized name
            _model_id_to_standard_name[model_id] = model_cfg.display_name
            
            console.print(f"Initialized {provider}/{model_id}", style="dim")
        except KeyError:
            console.print(f"❌ Unknown provider: {provider}", style="red")
        except Exception as e:
            console.print(f"❌ Error initializing {provider}/{model_id}: {str(e)}", style="red")
    
    if not enabled_models:
        console.print("You are running the benchmark without selecting models!", style="bold yellow")
    
    return enabled_models

def get_model_display_name(model_id: str) -> str:
    """Get the standardized display name for a model ID."""
    return _model_id_to_standard_name.get(model_id, model_id)

# List of enabled models to evaluate
to_eval = get_enabled_models()