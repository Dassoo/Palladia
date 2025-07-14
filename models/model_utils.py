import yaml
import os
from pathlib import Path
from typing import List, Dict, Any

from agno.models.openai import OpenAIChat
from agno.models.google import Gemini
from agno.models.anthropic import Claude
from agno.models.groq import Groq
from agno.models.mistral import MistralChat
from agno.models.nebius import Nebius
from agno.models.xai import xAI
from agno.models.openrouter import OpenRouter
from dotenv import load_dotenv

load_dotenv()

def load_model_config() -> List[Dict[str, Any]]:
    """Load model configuration from YAML file."""
    config_path = Path(__file__).parent.parent / 'config/model_config.yaml'
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    return config.get('models', [])

def get_enabled_models() -> List[Any]:
    """Get a list of initialized model instances based on the configuration."""
    model_configs = load_model_config()
    enabled_models = []
    
    # Map of class names to their actual classes
    model_classes = {
        'openai': OpenAIChat,
        'google': Gemini,
        'anthropic': Claude,
        'groq': Groq,
        'mistral': MistralChat,
        'nebius': Nebius,
        'xai': xAI,
        'openrouter': OpenRouter
    }
    
    for model_cfg in model_configs:
        if not model_cfg.get('enabled', False):
            continue
            
        model_class = model_cfg['provider']
        model_id = model_cfg['id']
        
        # Prepare model arguments
        kwargs = {}
        if 'api_key_env' in model_cfg:
            kwargs['api_key'] = os.getenv(model_cfg['api_key_env'])
        
        # Initialize the model
        try:
            model_instance = model_classes[model_class](id=model_id, **kwargs)
            enabled_models.append(model_instance)
        except Exception as e:
            print(f"Error initializing {model_class} ({model_id}): {str(e)}")
    
    return enabled_models

# List of enabled models to evaluate
to_eval = get_enabled_models()
