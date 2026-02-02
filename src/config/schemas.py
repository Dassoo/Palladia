from pydantic import BaseModel, Field, field_validator
from openrouter import OpenRouter
from pathlib import Path
from typing import List

import yaml
import os

from dotenv import load_dotenv
load_dotenv()

class Model(BaseModel):
    model_id: str = Field(..., description="Name of the model")
    enabled: bool = Field(..., description="Whether the model is enabled")
    link: str = Field(..., description="OpenRouter model page")
    
    @field_validator("model_id")
    def validate_model(cls, v: str):
        """
        Validate that the model exists on OpenRouter.
        
        Args:
            v: Model ID to validate
            
        Returns:
            Validated model ID
            
        Raises:
            ValueError: If API key is missing or model doesn't exist on OpenRouter
        """
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key: 
            raise ValueError("OPENROUTER_API_KEY required")
        
        try:
            with OpenRouter(api_key=api_key) as client:
                models = client.models.list()
                model_ids = [m.id for m in models.data]
                if v not in model_ids:
                    raise ValueError(f"Model '{v}' does not exist on OpenRouter")
            return v
        except Exception as e:
            if "does not exist" in str(e):
                raise ValueError(f"Model '{v}' does not exist on OpenRouter")
            raise ValueError(f"Validation failed: {e}")


class InputConfig(BaseModel):
    source: Path = Field(..., description="Source path of input images")
    images_to_process: int = Field(..., description="Number of images to benchmark")
    avoid_rescan: bool = Field(..., description="Avoid rescanning already processed images")
    models: List[Model] = Field(..., description="All configured models")

    @field_validator("source")
    @classmethod
    def validate_source(cls, v: Path) -> Path:
        """
        Validate that the source path exists.
        
        Args:
            v: Source path to validate
            
        Returns:
            Validated source path
            
        Raises:
            ValueError: If source path does not exist
        """
        if not v.exists():
            raise ValueError(f"Source path does not exist: {v}")
        return v

    @field_validator("images_to_process")
    @classmethod
    def validate_images_to_process(cls, v: int) -> int:
        """
        Validate that images_to_process is a positive integer.
        
        Args:
            v: Number of images to validate
            
        Returns:
            Validated number of images
            
        Raises:
            ValueError: If images_to_process is <= 0
        """
        if v <= 0:
            raise ValueError("images_to_process must be > 0")
        return v

    @property
    def enabled_models(self) -> List[Model]:
        """
        Get list of enabled models.
        
        Returns:
            List of Model instances where enabled=True
        """
        return [m for m in self.models if m.enabled]


# NOTE: This class may look like a duplicate of InputConfig, but it represents the
# execution-ready configuration. All decisions (e.g., enabled models, defaults)
# have been resolved here, so downstream code can safely run without further checks.
class CleanConfig(BaseModel):
    source: Path
    images_to_process: int
    avoid_rescan: bool
    models: List[Model]


def clean_config(config: InputConfig) -> CleanConfig:
    """
    Clean and validate configuration by filtering for enabled models.
    
    Args:
        config: Input configuration object
        
    Returns:
        Clean configuration with only enabled models
        
    Raises:
        ValueError: If no enabled models are found
    """
    enabled_models = config.enabled_models

    if not enabled_models:
        raise ValueError("No enabled models found in configuration")

    return CleanConfig(
        source=config.source,
        images_to_process=config.images_to_process,
        avoid_rescan=config.avoid_rescan,
        models=enabled_models,
    )


def _load_yaml(path: Path) -> dict:
    """
    Load a YAML file from the given path.
    
    Args:
        path: Path to YAML file to load
        
    Returns:
        Dictionary containing YAML content
    """
    with path.open("r") as f:
        return yaml.safe_load(f)


def load_config(
    images_config_path: Path = Path("src/config/images.yaml"), 
    models_config_path: Path = Path("src/config/models.yaml")
) -> CleanConfig:
    """
    Load and validate configuration from YAML files.
    
    Args:
        images_config_path: Path to images configuration YAML file
        models_config_path: Path to models configuration YAML file
        
    Returns:
        Clean and validated configuration object
        
    Raises:
        ValidationError: If configuration fails validation
    """
    images_cfg = _load_yaml(images_config_path)
    models_cfg = _load_yaml(models_config_path)

    full_cfg = {
        **images_cfg,
        **models_cfg,
    }

    validated = InputConfig.model_validate(full_cfg)
    return clean_config(validated)
