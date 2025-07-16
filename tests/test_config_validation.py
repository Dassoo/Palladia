#!/usr/bin/env python3

import tempfile
import yaml
from pathlib import Path
from rich.console import Console

from config.loader import ConfigLoader
from config.schemas import ModelsConfig, InputConfig

console = Console()

def test_valid_config():
    """Test with a valid configuration."""
    console.print("Testing valid configuration...", style="bold blue")
    
    # Create temporary config files
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Valid model config
        model_config = {
            'models': [
                {
                    'provider': 'openai',
                    'id': 'gpt-4o',
                    'enabled': True,
                    'api_key_env': 'OPENAI_API_KEY'
                }
            ]
        }
        
        # Valid input config
        input_config = {
            'input': [
                {
                    'path': 'GT4HistOCR/corpus/EarlyModernLatin/1471-Orthographia-Tortellius/',
                    'images_to_process': 3
                }
            ]
        }
        
        # Create yaml subdirectory and write configs
        yaml_dir = temp_path / 'yaml'
        yaml_dir.mkdir()
        with open(yaml_dir / 'model_config.yaml', 'w') as f:
            yaml.dump(model_config, f)
        with open(yaml_dir / 'input_config.yaml', 'w') as f:
            yaml.dump(input_config, f)
        
        # Test loading
        try:
            loader = ConfigLoader(temp_path)
            app_config = loader.load_app_config()
            console.print("✅ Valid configuration loaded successfully!", style="green")
            console.print(f"   Found {len(app_config.enabled_models)} enabled model(s)")
        except Exception as e:
            console.print(f"❌ Unexpected error: {e}", style="red")


def test_invalid_provider():
    """Test with an invalid provider."""
    console.print("\n🧪 Testing invalid provider...", style="bold blue")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Invalid provider
        model_config = {
            'models': [
                {
                    'provider': 'invalid_provider',  # This should fail
                    'id': 'some-model',
                    'enabled': True,
                    'api_key_env': 'SOME_API_KEY'
                }
            ]
        }
        
        yaml_dir = temp_path / 'yaml'
        yaml_dir.mkdir()
        with open(yaml_dir / 'model_config.yaml', 'w') as f:
            yaml.dump(model_config, f)
        
        try:
            loader = ConfigLoader(temp_path)
            models_config = loader.load_models_config()
            console.print("❌ Should have failed validation!", style="red")
        except Exception as e:
            console.print("✅ Correctly caught invalid provider", style="green")


def test_missing_path():
    """Test with a non-existent path."""
    console.print("\nTesting non-existent path...", style="bold blue")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Non-existent path
        input_config = {
            'input': [
                {
                    'path': '/this/path/does/not/exist',  # This should fail
                    'images_to_process': 3
                }
            ]
        }
        
        yaml_dir = temp_path / 'yaml'
        yaml_dir.mkdir()
        with open(yaml_dir / 'input_config.yaml', 'w') as f:
            yaml.dump(input_config, f)
        
        try:
            loader = ConfigLoader(temp_path)
            input_cfg = loader.load_input_config()
            console.print("❌ Should have failed validation!", style="red")
        except Exception as e:
            console.print("✅ Correctly caught non-existent path", style="green")


def test_negative_images():
    """Test with negative images_to_process."""
    console.print("\nTesting negative images_to_process...", style="bold blue")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Negative images count
        input_config = {
            'input': [
                {
                    'path': 'GT4HistOCR/corpus/EarlyModernLatin/1471-Orthographia-Tortellius/',
                    'images_to_process': -1  # This should fail
                }
            ]
        }
        
        yaml_dir = temp_path / 'yaml'
        yaml_dir.mkdir()
        with open(yaml_dir / 'input_config.yaml', 'w') as f:
            yaml.dump(input_config, f)
        
        try:
            loader = ConfigLoader(temp_path)
            input_cfg = loader.load_input_config()
            console.print("❌ Should have failed validation!", style="red")
        except Exception as e:
            console.print("✅ Correctly caught negative images_to_process", style="green")


if __name__ == "__main__":
    console.print("Testing Pydantic Configuration Validation", style="bold magenta")
    console.print("=" * 50, style="dim")
    
    test_valid_config()
    test_invalid_provider()
    test_missing_path()
    test_negative_images()
    
    console.print("\n" + "=" * 50, style="dim")
    console.print("Configuration validation tests completed!", style="bold green")