from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from pathlib import Path
import os


class ModelConfig(BaseModel):
    """Configuration for a single model."""
    provider: str = Field(..., description="Model provider (e.g., openai, google)")
    id: str = Field(..., description="Model identifier")
    enabled: bool = Field(default=False, description="Whether the model is enabled")
    api_key_env: str = Field(..., description="Environment variable name for API key")
    
    @field_validator('api_key_env')
    def validate_api_key_exists(cls, v):
        """Warn if API key environment variable is not set."""
        if not os.getenv(v):
            # Don't fail validation, just warn - user might set it later
            pass
        return v
    
    @field_validator('provider')
    def validate_provider(cls, v):
        """Validate that provider is supported."""
        supported_providers = {
            'OpenAI', 'Google', 'Mistral', 'Groq', 'Nebius', 
            'Anthropic', 'xAI', 'OpenRouter'
        }
        if v not in supported_providers:
            raise ValueError(f"Unsupported provider: {v}. Supported: {supported_providers}")
        return v


class ModelsConfig(BaseModel):
    """Configuration for all models."""
    models: List[ModelConfig] = Field(..., description="List of model configurations")
    
    @field_validator('models')
    def validate_at_least_one_enabled(cls, v):
        """Ensure at least one model is enabled for evaluation."""
        enabled_models = [m for m in v if m.enabled]
        if not enabled_models:
            # Don't fail - user might enable models later via UI
            pass
        return v


class InputPathConfig(BaseModel):
    """Configuration for a single input path."""
    path: str = Field(..., description="Path to the dataset directory")
    images_to_process: int = Field(default=1, ge=1, description="Number of images to process")
    
    @field_validator('path')
    def validate_path_exists(cls, v):
        """Validate that the path exists."""
        if not Path(v).exists():
            raise ValueError(f"Path does not exist: {v}")
        return v
    
    @field_validator('path')
    def validate_has_images(cls, v):
        """Validate that the path contains PNG images."""
        path = Path(v)
        if path.exists():
            png_files = list(path.glob("*.png"))
            if not png_files:
                raise ValueError(f"No PNG images found in: {v}")
        return v


class InputConfig(BaseModel):
    """Configuration for input datasets."""
    input: List[InputPathConfig] = Field(..., description="List of input configurations")
    
    @field_validator('input')
    def validate_not_empty(cls, v):
        """Ensure at least one input is configured."""
        if not v:
            raise ValueError("At least one input configuration is required")
        return v


class AppConfig(BaseModel):
    """Main application configuration combining models and inputs."""
    models_config: ModelsConfig
    input_config: InputConfig
    
    @property
    def enabled_models(self) -> List[ModelConfig]:
        """Get list of enabled models."""
        return [m for m in self.models_config.models if m.enabled]
    
    @property
    def missing_api_keys(self) -> List[str]:
        """Get list of enabled models with missing API keys."""
        missing = []
        for model in self.enabled_models:
            if not os.getenv(model.api_key_env):
                missing.append(f"{model.id} (needs {model.api_key_env})")
        return missing